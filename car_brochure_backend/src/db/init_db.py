from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from src.db.models import Base, Car, CarImage, Category

logger = logging.getLogger(__name__)


# PUBLIC_INTERFACE
async def initialize_database(engine: AsyncEngine) -> None:
    """Initialize database schema and seed minimal demo content.

    Flow name: InitializeDatabaseFlow
    Entrypoint: initialize_database(engine)

    Contract:
      - Inputs: AsyncEngine connected to target PostgreSQL DB.
      - Side effects: Creates tables if missing; inserts seed categories/cars if DB is empty.
      - Errors: Propagates SQLAlchemy/DB errors with context in logs.
    """
    logger.info("InitializeDatabaseFlow: start")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed content only if there are no cars yet.
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        existing = (await session.execute(select(Car.id).limit(1))).first()
        if existing:
            logger.info("InitializeDatabaseFlow: seed skipped (cars already exist)")
            return

        suv = Category(name="SUV", slug="suv")
        sedan = Category(name="Sedan", slug="sedan")
        ev = Category(name="EV", slug="ev")
        session.add_all([suv, sedan, ev])
        await session.flush()

        car1 = Car(
            make="Autobrowse",
            model="Falcon X",
            year=2025,
            trim="Premium",
            price_msrp=45999,
            currency="USD",
            description="A modern SUV with a comfortable interior and advanced safety features.",
            specs={"engine": "2.0L Turbo", "hp": 255, "drivetrain": "AWD", "mpg_city": 22, "mpg_hwy": 29},
            category_id=suv.id,
            is_published=True,
        )
        car1.images = [
            CarImage(url="https://picsum.photos/seed/falconx1/1200/800", alt="Falcon X front", sort_order=0, is_primary=True),
            CarImage(url="https://picsum.photos/seed/falconx2/1200/800", alt="Falcon X interior", sort_order=1, is_primary=False),
        ]

        car2 = Car(
            make="Autobrowse",
            model="Comet S",
            year=2024,
            trim="Sport",
            price_msrp=32999,
            currency="USD",
            description="A sleek sedan tuned for responsive handling and efficient performance.",
            specs={"engine": "1.8L Hybrid", "hp": 200, "drivetrain": "FWD", "mpg_city": 44, "mpg_hwy": 48},
            category_id=sedan.id,
            is_published=True,
        )
        car2.images = [
            CarImage(url="https://picsum.photos/seed/comets1/1200/800", alt="Comet S profile", sort_order=0, is_primary=True),
        ]

        car3 = Car(
            make="Autobrowse",
            model="Aurora EV",
            year=2025,
            trim="Long Range",
            price_msrp=51999,
            currency="USD",
            description="An all-electric crossover with fast charging and long range capability.",
            specs={"battery_kwh": 82, "range_miles": 310, "drivetrain": "AWD", "charge_10_80_min": 28},
            category_id=ev.id,
            is_published=True,
        )
        car3.images = [
            CarImage(url="https://picsum.photos/seed/auroraev1/1200/800", alt="Aurora EV front", sort_order=0, is_primary=True),
        ]

        session.add_all([car1, car2, car3])
        await session.commit()

    logger.info("InitializeDatabaseFlow: done")
