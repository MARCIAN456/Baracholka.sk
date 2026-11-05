import math
import uuid
from sqlalchemy import or_

from app.models.item import ItemCategory
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.item import Item

from app.schemas.item import ItemCreate, ItemResponse, ItemDetailedResponse, ItemPaginatedResponse, ItemUpdate

router = APIRouter()

@router.post("/create-item", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(body: ItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

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
def get_items(
        page: int = Query(1, ge=1, description="Number of page(starts with 1)"),
        size: int = Query(10, ge=1, le = 20, description="Amount of items in page(max 20)"),
        category: ItemCategory | None = Query(None, description="Фільтр за категорією"),
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        db: Session = Depends(get_db)
):
    query_items = db.query(Item).filter(Item.is_sold == False)

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
def get_my_items(
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
def get_item_by_id(item_id: uuid.UUID, db: Session = Depends(get_db)):
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

    db.delete(current_item)
    db.commit()

@router.patch("/update-item/{item_id}", response_model=ItemResponse)
def update_item(item_id: uuid.UUID,
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

    updated_item = body.model_dump(exclude_unset=True)

    for field, value in updated_item.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item





