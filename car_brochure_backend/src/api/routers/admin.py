from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.deps import require_admin
from src.api.routers.catalog import _car_to_detail, _car_to_summary
from src.api.schemas import (
    AdminCarImageUpsert,
    AdminCarUpsert,
    AdminCategoryUpsert,
    CarDetailOut,
    CarSummaryOut,
    CategoryOut,
    InquiryOut,
)
from src.core.config import Settings
from src.db.session import get_db_session
from src.services.admin_service import (
    admin_add_car_image,
    admin_delete_car,
    admin_delete_car_image,
    admin_delete_category,
    admin_list_cars,
    admin_list_inquiries,
    admin_upsert_car,
    admin_upsert_category,
)


# PUBLIC_INTERFACE
def wire_admin_router(*, session_maker: async_sessionmaker[AsyncSession], settings: Settings) -> APIRouter:
    """Return admin router with admin auth + DB dependencies bound."""
    wired = APIRouter(prefix="/api/admin", tags=["Admin"])

    def _auth(x_admin_key: str | None = None):
        return require_admin(settings, x_admin_key)

    @wired.post(
        "/categories",
        summary="Create category",
        description="Admin: create a category.",
        response_model=CategoryOut,
        operation_id="admin_create_category",
    )
    async def _create_category(payload: AdminCategoryUpsert, _: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        cat = await admin_upsert_category(session, category_id=None, name=payload.name, slug=payload.slug)
        return CategoryOut(id=cat.id, name=cat.name, slug=cat.slug)

    @wired.put(
        "/categories/{category_id}",
        summary="Update category",
        description="Admin: update a category.",
        response_model=CategoryOut,
        operation_id="admin_update_category",
    )
    async def _update_category(category_id: int, payload: AdminCategoryUpsert, _: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        try:
            cat = await admin_upsert_category(session, category_id=category_id, name=payload.name, slug=payload.slug)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        return CategoryOut(id=cat.id, name=cat.name, slug=cat.slug)

    @wired.delete(
        "/categories/{category_id}",
        summary="Delete category",
        description="Admin: delete a category.",
        response_model=None,
        status_code=status.HTTP_204_NO_CONTENT,
        operation_id="admin_delete_category",
    )
    async def _delete_category(category_id: int, _: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        await admin_delete_category(session, category_id=category_id)
        return None

    @wired.get(
        "/cars",
        summary="List cars (admin)",
        description="Admin: list cars including unpublished by default.",
        response_model=list[CarSummaryOut],
        operation_id="admin_list_cars",
    )
    async def _list_cars(_: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        cars = await admin_list_cars(session, include_unpublished=True)
        return [_car_to_summary(c) for c in cars]

    @wired.post(
        "/cars",
        summary="Create car",
        description="Admin: create a car listing.",
        response_model=CarDetailOut,
        operation_id="admin_create_car",
    )
    async def _create_car(payload: AdminCarUpsert, _: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        car = await admin_upsert_car(session, car_id=None, payload=payload.model_dump())
        return _car_to_detail(car)

    @wired.put(
        "/cars/{car_id}",
        summary="Update car",
        description="Admin: update a car listing.",
        response_model=CarDetailOut,
        operation_id="admin_update_car",
    )
    async def _update_car(car_id: int, payload: AdminCarUpsert, _: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        try:
            car = await admin_upsert_car(session, car_id=car_id, payload=payload.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        return _car_to_detail(car)

    @wired.delete(
        "/cars/{car_id}",
        summary="Delete car",
        description="Admin: delete a car listing.",
        response_model=None,
        status_code=status.HTTP_204_NO_CONTENT,
        operation_id="admin_delete_car",
    )
    async def _delete_car(car_id: int, _: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        await admin_delete_car(session, car_id=car_id)
        return None

    @wired.post(
        "/cars/{car_id}/images",
        summary="Add car image",
        description="Admin: add an image to a car.",
        response_model=None,
        status_code=status.HTTP_201_CREATED,
        operation_id="admin_add_car_image",
    )
    async def _add_image(car_id: int, payload: AdminCarImageUpsert, _: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        try:
            await admin_add_car_image(
                session,
                car_id=car_id,
                url=payload.url,
                alt=payload.alt,
                sort_order=payload.sort_order,
                is_primary=payload.is_primary,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        return None

    @wired.delete(
        "/images/{image_id}",
        summary="Delete car image",
        description="Admin: delete a car image.",
        response_model=None,
        status_code=status.HTTP_204_NO_CONTENT,
        operation_id="admin_delete_car_image",
    )
    async def _delete_image(image_id: int, _: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        await admin_delete_car_image(session, image_id=image_id)
        return None

    @wired.get(
        "/inquiries",
        summary="List inquiries",
        description="Admin: list customer inquiries.",
        response_model=list[InquiryOut],
        operation_id="admin_list_inquiries",
    )
    async def _list_inquiries(_: None = Depends(_auth), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        inquiries = await admin_list_inquiries(session)
        return [
            InquiryOut(
                id=i.id,
                car_id=i.car_id,
                inquiry_type=i.inquiry_type,
                name=i.name,
                email=i.email,
                phone=i.phone,
                message=i.message,
                created_at=i.created_at,
            )
            for i in inquiries
        ]

    return wired
