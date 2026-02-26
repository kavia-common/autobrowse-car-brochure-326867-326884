from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    cars: Mapped[list["Car"]] = relationship(back_populates="category")


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    make: Mapped[str] = mapped_column(String(80), index=True)
    model: Mapped[str] = mapped_column(String(120), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    trim: Mapped[str | None] = mapped_column(String(120), nullable=True)

    price_msrp: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD")

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Example: {"engine":"2.0L","hp":250,"mpg_city":22,"mpg_hwy":30,...}
    specs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    category: Mapped[Category | None] = relationship(back_populates="cars")
    images: Mapped[list["CarImage"]] = relationship(back_populates="car", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="car", cascade="all, delete-orphan")
    inquiries: Mapped[list["Inquiry"]] = relationship(back_populates="car", cascade="all, delete-orphan")


class CarImage(Base):
    __tablename__ = "car_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), index=True)
    url: Mapped[str] = mapped_column(Text)
    alt: Mapped[str | None] = mapped_column(String(240), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    car: Mapped[Car] = relationship(back_populates="images")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_key", "car_id", name="uq_favorite_user_car"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_key: Mapped[str] = mapped_column(String(128), index=True)  # simple anonymous/user identifier
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    car: Mapped[Car] = relationship(back_populates="favorites")


class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    car_id: Mapped[int | None] = mapped_column(ForeignKey("cars.id"), nullable=True, index=True)

    inquiry_type: Mapped[str] = mapped_column(String(32), default="contact")  # contact | test_drive
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(240))
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    car: Mapped[Car | None] = relationship(back_populates="inquiries")
