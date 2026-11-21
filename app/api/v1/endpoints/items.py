import math
import uuid
from sqlalchemy import or_
from app.core.limiter import limiter

from app.models.item import ItemCategory, ItemStatus
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.item import Item
from app.models.image import ItemImage
from app.models.payments import Payment, OrderStatus

from app.service.cloudnare_service import upload_photo, delete_photo

from app.schemas.item import ItemCreate, ItemResponse, ItemDetailedResponse, ItemPaginatedResponse, ItemUpdate
from app.schemas.item import ItemImageResponse

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024

router = APIRouter()

@router.post("/create-item", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_item(request: Request,body: ItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.iban:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please add your IBAN first"
        )
    new_item = Item(
        title=body.title,
        description=body.description,
        price=body.price,
        category=body.category.value,
        weight=body.weight.value,
        user_id=current_user.id
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item

@router.get("/", response_model=ItemPaginatedResponse, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
def get_items(
        request: Request,
        page: int = Query(1, ge=1, description="Number of page(starts with 1)"),
        size: int = Query(10, ge=1, le = 20, description="Amount of items in page(max 20)"),
        category: ItemCategory | None = Query(None, description="Filter by category"),
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        db: Session = Depends(get_db)
):
    query_items = db.query(Item).filter(Item.is_sold == False, Item.status == ItemStatus.ACCEPTED.value)

    if category:
        query_items = query_items.filter(Item.category == category.value)

    if min_price is not None:
        query_items = query_items.filter(Item.price >= min_price)

    if max_price is not None:
        query_items = query_items.filter(Item.price <= max_price)

    if search:
        query_items = query_items.filter(
            or_(
                Item.title.ilike(f"%{search}%"),
                Item.description.ilike(f"%{search}%")
            )
        )

    query_items = query_items.order_by(Item.createdAt.desc(), Item.id)

    total = query_items.count()

    offset = (page - 1) * size

    items = query_items.offset(offset).limit(size).all()

    total_pages = math.ceil(total/size) if total > 0 else 1

    return ItemPaginatedResponse(
        items = items,
        total = total,
        page=page,
        size=size,
        pages=total_pages
    )
@router.get("/get_my_items", response_model=ItemPaginatedResponse, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
def get_my_items(
        request: Request,
        page: int = Query(1, ge=1, description="Number of page(starts with 1)"),
        size: int = Query(10, ge=1, le=20, description="Amount of items on page (max 20)"),
        is_sold: bool | None = Query(None, description="Filter: only active (False) or sold (True)"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    query_items = db.query(Item).filter(Item.user_id == current_user.id)

    if is_sold is not None:
        query_items = query_items.filter(Item.is_sold == is_sold)

    query_items = query_items.order_by(Item.createdAt.desc())


    total = query_items.count()

    offset = (page - 1) * size

    items = query_items.offset(offset).limit(size).all()

    total_pages = math.ceil(total/size) if total > 0 else 1

    return ItemPaginatedResponse(
        items = items,
        total = total,
        page=page,
        size=size,
        pages=total_pages
    )


@router.get("/get-item-by-id/{item_id}", response_model=ItemDetailedResponse, status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
def get_item_by_id(request: Request, item_id: uuid.UUID, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: uuid.UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    current_item = db.query(Item).filter(Item.id == item_id).first()

    if not current_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    if current_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permission"
        )

    has_active_payment = db.query(Payment).filter(
        Payment.item_id == item_id,
        Payment.status != OrderStatus.CANCELLED.value
    ).first()

    if has_active_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item has payments and cannot be deleted"
        )

    public_ids = [img.public_id for img in current_item.images]

    db.delete(current_item)
    db.commit()

    for public_id in public_ids:
        try:
            delete_photo(public_id)
        except Exception:
            pass

@router.patch("/update-item/{item_id}", response_model=ItemResponse)
def update_item(request: Request,
                item_id: uuid.UUID,
                body: ItemUpdate,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own item"
        )

    if item.is_sold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sold item cannot be edited"
        )

    updated_item = body.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in updated_item.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item

@router.post("/{item_id}/images", response_model=list[ItemImageResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def upload_item_image(
        request: Request,
        item_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        files: list[UploadFile] = File(...),
):
    item = db.query(Item).filter(Item.id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found item"
        )
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add photo to your own item"
        )

    current_count = db.query(ItemImage).filter(ItemImage.item_id == item_id).count()
    if current_count + len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum 5 photos allowed. Currently have {current_count}, trying to add {len(files)}"
        )

    for file in files:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file.filename}. Allowed: JPEG, PNG, WEBP"
            )
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} is too large. Max size is 5MB"
            )

        header = file.file.read(16)
        file.file.seek(0)
        is_jpeg = header.startswith(b'\xff\xd8\xff')
        is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
        is_webp = header.startswith(b'RIFF') and b'WEBP' in header
        if not (is_jpeg or is_png or is_webp):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} is not a valid image!"
            )

    uploaded_records = []

    for file in files:
        upload_data = upload_photo(file)

        new_image = ItemImage(
            item_id=item.id,
            image_url=upload_data["image_url"],
            public_id=upload_data["public_id"]
        )
        db.add(new_image)
        uploaded_records.append(new_image)

    db.commit()

    for img in uploaded_records:
        db.refresh(img)

    return uploaded_records

@router.delete("/{item_id}/images/{image_id}", status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
def delete_item_image(
        request: Request,
        item_id: uuid.UUID,
        image_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    image = db.query(ItemImage).filter(ItemImage.id == image_id,
                                       ItemImage.item_id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found item"
        )

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found image"
        )

    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete photo on your own item"
        )
    public_id = image.public_id
    db.delete(image)
    db.commit()

    try:
        delete_photo(public_id)
    except Exception:
        pass

    return {"message": "Image deleted successfully"}





