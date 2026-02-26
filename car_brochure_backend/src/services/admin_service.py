from __future__ import annotations

import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Car, CarImage, Category, Inquiry

logger = logging.getLogger(__name__)


# PUBLIC_INTERFACE
async def admin_upsert_category(session: AsyncSession, *, category_id: int | None, name: str, slug: str) -> Category:
    """Create or update a category."""
    if category_id is None:
        cat = Category(name=name, slug=slug)
        session.add(cat)
        await session.commit()
        await session.refresh(cat)
        return cat

    cat = (await session.execute(select(Category).where(Category.id == category_id))).scalars().first()
    if not cat:
        raise ValueError("Category not found")
    cat.name = name
    cat.slug = slug
    await session.commit()
    await session.refresh(cat)
    return cat


# PUBLIC_INTERFACE
async def admin_delete_category(session: AsyncSession, *, category_id: int) -> None:
    """Delete a category."""
    await session.execute(delete(Category).where(Category.id == category_id))
    await session.commit()


# PUBLIC_INTERFACE
async def admin_upsert_car(session: AsyncSession, *, car_id: int | None, payload: dict) -> Car:
    """Create or update a car listing."""
    if car_id is None:
        car = Car(**payload)
        session.add(car)
        await session.commit()
        await session.refresh(car)
        return car

    car = (await session.execute(select(Car).where(Car.id == car_id))).scalars().first()
    if not car:
        raise ValueError("Car not found")

    for k, v in payload.items():
        setattr(car, k, v)

    await session.commit()
    await session.refresh(car)
    return car


# PUBLIC_INTERFACE
async def admin_delete_car(session: AsyncSession, *, car_id: int) -> None:
    """Delete a car (cascades to images/favorites/inquiries)."""
    await session.execute(delete(Car).where(Car.id == car_id))
    await session.commit()


# PUBLIC_INTERFACE
async def admin_list_cars(session: AsyncSession, *, include_unpublished: bool = True) -> list[Car]:
    """List all cars for admin usage."""
    stmt = select(Car).options(selectinload(Car.images), selectinload(Car.category)).order_by(
        Car.updated_at.desc(), Car.id.desc()
    )
    if not include_unpublished:
        stmt = stmt.where(Car.is_published.is_(True))
    return list((await session.execute(stmt)).scalars().unique().all())


# PUBLIC_INTERFACE
async def admin_add_car_image(
    session: AsyncSession,
    *,
    car_id: int,
    url: str,
    alt: str | None,
    sort_order: int,
    is_primary: bool,
) -> CarImage:
    """Add an image to a car; if `is_primary` is true, unset other primary images.

    Errors:
      - ValueError: if car does not exist.
    """
    car = (await session.execute(select(Car).where(Car.id == car_id))).scalars().first()
    if not car:
        raise ValueError("Car not found")

    if is_primary:
        images = list((await session.execute(select(CarImage).where(CarImage.car_id == car_id))).scalars().all())
        for img in images:
            img.is_primary = False

    img = CarImage(car_id=car_id, url=url, alt=alt, sort_order=sort_order, is_primary=is_primary)
    session.add(img)
    await session.commit()
    await session.refresh(img)
    return img


# PUBLIC_INTERFACE
async def admin_delete_car_image(session: AsyncSession, *, image_id: int) -> None:
    """Delete a car image."""
    await session.execute(delete(CarImage).where(CarImage.id == image_id))
    await session.commit()


# PUBLIC_INTERFACE
async def admin_list_inquiries(session: AsyncSession) -> list[Inquiry]:
    """List inquiries newest first."""
    stmt = select(Inquiry).order_by(Inquiry.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())
