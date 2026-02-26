from __future__ import annotations

import logging

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.schemas import CarSearchFilters
from src.db.models import Car, Category, Favorite, Inquiry

logger = logging.getLogger(__name__)


def _apply_filters(stmt, filters: CarSearchFilters):
    conditions = []
    if filters.published_only:
        conditions.append(Car.is_published.is_(True))
    if filters.category_id is not None:
        conditions.append(Car.category_id == filters.category_id)
    if filters.min_year is not None:
        conditions.append(Car.year >= filters.min_year)
    if filters.max_year is not None:
        conditions.append(Car.year <= filters.max_year)
    if filters.min_price is not None:
        conditions.append(Car.price_msrp >= filters.min_price)
    if filters.max_price is not None:
        conditions.append(Car.price_msrp <= filters.max_price)
    if filters.q:
        q = f"%{filters.q.strip()}%"
        conditions.append(or_(Car.make.ilike(q), Car.model.ilike(q), Car.trim.ilike(q)))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    return stmt


# PUBLIC_INTERFACE
async def list_categories(session: AsyncSession) -> list[Category]:
    """List categories ordered by name."""
    result = await session.execute(select(Category).order_by(Category.name.asc()))
    return list(result.scalars().all())


# PUBLIC_INTERFACE
async def list_cars(
    session: AsyncSession,
    *,
    filters: CarSearchFilters,
    page: int,
    page_size: int,
) -> tuple[list[Car], int]:
    """List cars with filtering and pagination.

    Returns:
      (cars, total)
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 48:
        page_size = 12

    base = select(Car).options(selectinload(Car.images), selectinload(Car.category)).order_by(
        Car.year.desc(), Car.make.asc(), Car.model.asc()
    )
    base = _apply_filters(base, filters)

    count_stmt = select(func.count()).select_from(_apply_filters(select(Car.id), filters).subquery())
    total = int((await session.execute(count_stmt)).scalar_one())

    stmt = base.offset((page - 1) * page_size).limit(page_size)
    cars = list((await session.execute(stmt)).scalars().unique().all())
    return cars, total


# PUBLIC_INTERFACE
async def get_car_detail(session: AsyncSession, car_id: int, *, include_unpublished: bool = False) -> Car | None:
    """Fetch a car detail by ID. Returns None if not found or not published (unless include_unpublished)."""
    stmt = (
        select(Car)
        .where(Car.id == car_id)
        .options(selectinload(Car.images), selectinload(Car.category))
    )
    if not include_unpublished:
        stmt = stmt.where(Car.is_published.is_(True))
    result = await session.execute(stmt)
    return result.scalars().unique().first()


# PUBLIC_INTERFACE
async def compare_cars(session: AsyncSession, car_ids: list[int]) -> list[Car]:
    """Fetch a list of cars for comparison, preserving input ordering (missing unpublished omitted)."""
    if not car_ids:
        return []
    stmt = (
        select(Car)
        .where(Car.id.in_(car_ids), Car.is_published.is_(True))
        .options(selectinload(Car.images), selectinload(Car.category))
    )
    cars = list((await session.execute(stmt)).scalars().unique().all())
    car_by_id = {c.id: c for c in cars}
    return [car_by_id[cid] for cid in car_ids if cid in car_by_id]


# PUBLIC_INTERFACE
async def add_favorite(session: AsyncSession, *, user_key: str, car_id: int) -> None:
    """Add favorite if not present."""
    existing = await session.execute(select(Favorite).where(Favorite.user_key == user_key, Favorite.car_id == car_id))
    if existing.scalars().first():
        return
    session.add(Favorite(user_key=user_key, car_id=car_id))
    await session.commit()


# PUBLIC_INTERFACE
async def remove_favorite(session: AsyncSession, *, user_key: str, car_id: int) -> None:
    """Remove favorite if exists."""
    existing = await session.execute(select(Favorite).where(Favorite.user_key == user_key, Favorite.car_id == car_id))
    fav = existing.scalars().first()
    if not fav:
        return
    await session.delete(fav)
    await session.commit()


# PUBLIC_INTERFACE
async def list_favorites(session: AsyncSession, *, user_key: str) -> list[Favorite]:
    """List favorites for user_key including car summary relations."""
    stmt = (
        select(Favorite)
        .where(Favorite.user_key == user_key)
        .order_by(Favorite.created_at.desc())
        .options(selectinload(Favorite.car).selectinload(Car.images), selectinload(Favorite.car).selectinload(Car.category))
    )
    return list((await session.execute(stmt)).scalars().unique().all())


# PUBLIC_INTERFACE
async def create_inquiry(
    session: AsyncSession,
    *,
    car_id: int | None,
    inquiry_type: str,
    name: str,
    email: str,
    phone: str | None,
    message: str | None,
) -> Inquiry:
    """Create an inquiry."""
    inquiry = Inquiry(
        car_id=car_id,
        inquiry_type=inquiry_type,
        name=name,
        email=email,
        phone=phone,
        message=message,
    )
    session.add(inquiry)
    await session.commit()
    await session.refresh(inquiry)
    return inquiry
