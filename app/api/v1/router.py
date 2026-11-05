from fastapi import APIRouter

from app.api.v1.endpoints import auth, items, users, payments, delivery

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    items.router,
    prefix="/items",
    tags=["Items"]
)

api_router.include_router(
    users.router,
    prefix="/user",
    tags=["User"]
)

api_router.include_router(
    payments.router,
    prefix="/payments",
    tags=["Payments"]
)

api_router.include_router(
    delivery.router,
    prefix="/delivery",
    tags=["Delivery"]
)
