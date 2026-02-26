from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.schemas import (
    CarDetailOut,
    CarListResponse,
    CarSearchFilters,
    CategoryOut,
    CompareRequest,
    CompareResponse,
)
from src.db.models import Car
from src.db.session import get_db_session
from src.services.catalog_service import compare_cars, get_car_detail, list_categories, list_cars

router = APIRouter(prefix="/api", tags=["Catalog"])


def _car_to_category_out(car: Car) -> CategoryOut | None:
    if not car.category:
        return None
    return CategoryOut(id=car.category.id, name=car.category.name, slug=car.category.slug)


def _primary_url(car: Car) -> str | None:
    if not car.images:
        return None
    primary = sorted(car.images, key=lambda i: (0 if i.is_primary else 1, i.sort_order, i.id))[0]
    return primary.url


def _car_to_summary(car: Car):
    from src.api.schemas import CarSummaryOut

    return CarSummaryOut(
        id=car.id,
        make=car.make,
        model=car.model,
        year=car.year,
        trim=car.trim,
        price_msrp=float(car.price_msrp) if car.price_msrp is not None else None,
        currency=car.currency,
        category=_car_to_category_out(car),
        primary_image_url=_primary_url(car),
    )


def _car_to_detail(car: Car) -> CarDetailOut:
    from src.api.schemas import CarImageOut

    images = sorted(car.images or [], key=lambda i: (i.sort_order, i.id))
    return CarDetailOut(
        id=car.id,
        make=car.make,
        model=car.model,
        year=car.year,
        trim=car.trim,
        price_msrp=float(car.price_msrp) if car.price_msrp is not None else None,
        currency=car.currency,
        description=car.description,
        specs=car.specs,
        category=_car_to_category_out(car),
        images=[
            CarImageOut(
                id=img.id,
                url=img.url,
                alt=img.alt,
                sort_order=img.sort_order,
                is_primary=img.is_primary,
            )
            for img in images
        ],
    )


@router.get(
    "/categories",
    summary="List categories",
    description="Fetch all categories available for filtering/browsing.",
    response_model=list[CategoryOut],
    operation_id="list_categories",
)
async def api_list_categories(
    session_maker: async_sessionmaker[AsyncSession] = Depends(lambda: None),
):
    # session_maker is injected at app wiring time via dependency override
    raise RuntimeError("Dependency override missing for session maker")


@router.get(
    "/cars",
    summary="List cars",
    description="Browse cars with pagination, search, and filters.",
    response_model=CarListResponse,
    operation_id="list_cars",
)
async def api_list_cars(
    q: str | None = Query(None, description="Search query"),
    category_id: int | None = Query(None, description="Category ID"),
    min_year: int | None = Query(None, description="Min year"),
    max_year: int | None = Query(None, description="Max year"),
    min_price: float | None = Query(None, description="Min MSRP"),
    max_price: float | None = Query(None, description="Max MSRP"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(12, ge=1, le=48, description="Page size"),
    session: AsyncSession = Depends(lambda: None),
):
    raise RuntimeError("Dependency override missing for DB session")


@router.get(
    "/cars/{car_id}",
    summary="Get car details",
    description="Fetch full details for a car (images/specs/pricing).",
    response_model=CarDetailOut,
    operation_id="get_car_detail",
)
async def api_get_car_detail(
    car_id: int,
    session: AsyncSession = Depends(lambda: None),
):
    raise RuntimeError("Dependency override missing for DB session")


@router.post(
    "/compare",
    summary="Compare cars",
    description="Compare 2-4 cars by returning their detailed fields in the requested order.",
    response_model=CompareResponse,
    operation_id="compare_cars",
)
async def api_compare(
    payload: CompareRequest,
    session: AsyncSession = Depends(lambda: None),
):
    raise RuntimeError("Dependency override missing for DB session")


# --- Wiring helpers used by main.py to avoid circular imports ---

# PUBLIC_INTERFACE
def wire_catalog_router(
    *,
    session_maker: async_sessionmaker[AsyncSession],
) -> APIRouter:
    """Return a router with DB dependencies properly bound.

    Contract:
      - Inputs: session_maker created from app settings.
      - Output: APIRouter ready to include in FastAPI.
    """
    wired = APIRouter(prefix="/api", tags=["Catalog"])

    @wired.get(
        "/categories",
        summary="List categories",
        description="Fetch all categories available for filtering/browsing.",
        response_model=list[CategoryOut],
        operation_id="list_categories",
    )
    async def _list_categories(session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        cats = await list_categories(session)
        return [CategoryOut(id=c.id, name=c.name, slug=c.slug) for c in cats]

    @wired.get(
        "/cars",
        summary="List cars",
        description="Browse cars with pagination, search, and filters.",
        response_model=CarListResponse,
        operation_id="list_cars",
    )
    async def _list_cars(
        q: str | None = Query(None, description="Search query"),
        category_id: int | None = Query(None, description="Category ID"),
        min_year: int | None = Query(None, description="Min year"),
        max_year: int | None = Query(None, description="Max year"),
        min_price: float | None = Query(None, description="Min MSRP"),
        max_price: float | None = Query(None, description="Max MSRP"),
        page: int = Query(1, ge=1, description="Page number (1-based)"),
        page_size: int = Query(12, ge=1, le=48, description="Page size"),
        session: AsyncSession = Depends(lambda: get_db_session(session_maker)),
    ):
        filters = CarSearchFilters(
            q=q,
            category_id=category_id,
            min_year=min_year,
            max_year=max_year,
            min_price=min_price,
            max_price=max_price,
            published_only=True,
        )
        cars, total = await list_cars(session, filters=filters, page=page, page_size=page_size)
        return CarListResponse(
            items=[_car_to_summary(c) for c in cars],
            total=total,
            page=page,
            page_size=page_size,
        )

    @wired.get(
        "/cars/{car_id}",
        summary="Get car details",
        description="Fetch full details for a car (images/specs/pricing).",
        response_model=CarDetailOut,
        operation_id="get_car_detail",
    )
    async def _get_car_detail(car_id: int, session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        car = await get_car_detail(session, car_id, include_unpublished=False)
        if not car:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
        return _car_to_detail(car)

    @wired.post(
        "/compare",
        summary="Compare cars",
        description="Compare 2-4 cars by returning their detailed fields in the requested order.",
        response_model=CompareResponse,
        operation_id="compare_cars",
    )
    async def _compare(payload: CompareRequest, session: AsyncSession = Depends(lambda: get_db_session(session_maker))):
        cars = await compare_cars(session, payload.car_ids)
        return CompareResponse(cars=[_car_to_detail(c) for c in cars])

    return wired
