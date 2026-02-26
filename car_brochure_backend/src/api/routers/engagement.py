from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.schemas import (
    FavoriteOut,
    FavoritesAddRequest,
    FavoritesListResponse,
    FavoritesRemoveRequest,
    InquiryCreateRequest,
    InquiryOut,
)
from src.db.models import Favorite
from src.db.session import get_db_session
from src.services.catalog_service import add_favorite, create_inquiry, get_car_detail, list_favorites, remove_favorite

router = APIRouter(prefix="/api", tags=["Engagement"])


def _fav_to_out(f: Favorite) -> FavoriteOut:
    from src.api.routers.catalog import _car_to_summary

    return FavoriteOut(
        car=_car_to_summary(f.car),
        created_at=f.created_at,
    )


# PUBLIC_INTERFACE
def wire_engagement_router(*, session_maker: async_sessionmaker[AsyncSession]) -> APIRouter:
    """Return a router with DB dependencies properly bound."""
    wired = APIRouter(prefix="/api", tags=["Engagement"])

    @wired.get(
        "/favorites",
        summary="List favorites",
        description="List favorited cars for a given user_key (client-side identifier).",
        response_model=FavoritesListResponse,
        operation_id="list_favorites",
    )
    async def _list_favorites(user_key: str = Query(..., description="User key"), session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        items = await list_favorites(session, user_key=user_key)
        return FavoritesListResponse(items=[_fav_to_out(f) for f in items])

    @wired.post(
        "/favorites/add",
        summary="Add favorite",
        description="Add a car to favorites for a given user_key.",
        response_model=None,
        status_code=status.HTTP_204_NO_CONTENT,
        operation_id="add_favorite",
    )
    async def _add_favorite(payload: FavoritesAddRequest, session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        car = await get_car_detail(session, payload.car_id, include_unpublished=False)
        if not car:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
        await add_favorite(session, user_key=payload.user_key, car_id=payload.car_id)
        return None

    @wired.post(
        "/favorites/remove",
        summary="Remove favorite",
        description="Remove a car from favorites for a given user_key.",
        response_model=None,
        status_code=status.HTTP_204_NO_CONTENT,
        operation_id="remove_favorite",
    )
    async def _remove_favorite(payload: FavoritesRemoveRequest, session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        await remove_favorite(session, user_key=payload.user_key, car_id=payload.car_id)
        return None

    @wired.post(
        "/inquiries",
        summary="Create inquiry",
        description="Submit a contact or test-drive inquiry (optionally tied to a car).",
        response_model=InquiryOut,
        operation_id="create_inquiry",
    )
    async def _create_inquiry(payload: InquiryCreateRequest, session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        if payload.inquiry_type not in ("contact", "test_drive"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid inquiry_type")

        if payload.car_id is not None:
            car = await get_car_detail(session, payload.car_id, include_unpublished=False)
            if not car:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")

        inquiry = await create_inquiry(
            session,
            car_id=payload.car_id,
            inquiry_type=payload.inquiry_type,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            message=payload.message,
        )
        return InquiryOut(
            id=inquiry.id,
            car_id=inquiry.car_id,
            inquiry_type=inquiry.inquiry_type,
            name=inquiry.name,
            email=inquiry.email,
            phone=inquiry.phone,
            message=inquiry.message,
            created_at=inquiry.created_at,
        )

    return wired
