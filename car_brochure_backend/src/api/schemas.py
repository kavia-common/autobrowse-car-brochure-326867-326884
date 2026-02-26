from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Display name")
    slug: str = Field(..., description="URL-safe slug")


class CarImageOut(BaseModel):
    id: int = Field(..., description="Image ID")
    url: str = Field(..., description="Public image URL")
    alt: str | None = Field(None, description="Alt text")
    sort_order: int = Field(..., description="Sort order within car gallery")
    is_primary: bool = Field(..., description="Whether image is primary thumbnail")


class CarSummaryOut(BaseModel):
    id: int = Field(..., description="Car ID")
    make: str = Field(..., description="Manufacturer")
    model: str = Field(..., description="Model name")
    year: int = Field(..., description="Model year")
    trim: str | None = Field(None, description="Trim level")
    price_msrp: float | None = Field(None, description="MSRP price")
    currency: str = Field(..., description="Currency code, e.g., USD")
    category: CategoryOut | None = Field(None, description="Category")
    primary_image_url: str | None = Field(None, description="Primary image URL if exists")


class CarDetailOut(BaseModel):
    id: int = Field(..., description="Car ID")
    make: str = Field(..., description="Manufacturer")
    model: str = Field(..., description="Model name")
    year: int = Field(..., description="Model year")
    trim: str | None = Field(None, description="Trim level")
    price_msrp: float | None = Field(None, description="MSRP price")
    currency: str = Field(..., description="Currency code")
    description: str | None = Field(None, description="Description/marketing copy")
    specs: dict[str, Any] | None = Field(None, description="Specifications JSON blob")
    category: CategoryOut | None = Field(None, description="Category")
    images: list[CarImageOut] = Field(default_factory=list, description="Gallery images")


class CarListResponse(BaseModel):
    items: list[CarSummaryOut] = Field(..., description="List of cars")
    total: int = Field(..., description="Total matching cars")
    page: int = Field(..., description="Page index (1-based)")
    page_size: int = Field(..., description="Page size")


class CarSearchFilters(BaseModel):
    q: str | None = Field(None, description="Search query matching make/model/trim")
    category_id: int | None = Field(None, description="Filter by category")
    min_year: int | None = Field(None, description="Minimum year")
    max_year: int | None = Field(None, description="Maximum year")
    min_price: float | None = Field(None, description="Minimum MSRP")
    max_price: float | None = Field(None, description="Maximum MSRP")
    published_only: bool = Field(True, description="If true, show only published cars")


class CompareRequest(BaseModel):
    car_ids: list[int] = Field(..., min_length=2, max_length=4, description="Car IDs to compare (2-4)")


class CompareResponse(BaseModel):
    cars: list[CarDetailOut] = Field(..., description="Cars to compare")


class FavoritesAddRequest(BaseModel):
    user_key: str = Field(..., description="Client-provided stable user identifier (e.g., anonymous UUID)")
    car_id: int = Field(..., description="Car ID to favorite")


class FavoritesRemoveRequest(BaseModel):
    user_key: str = Field(..., description="Client-provided stable user identifier (e.g., anonymous UUID)")
    car_id: int = Field(..., description="Car ID to unfavorite")


class FavoriteOut(BaseModel):
    car: CarSummaryOut = Field(..., description="Favorited car summary")
    created_at: datetime = Field(..., description="When favorited")


class FavoritesListResponse(BaseModel):
    items: list[FavoriteOut] = Field(..., description="Favorites list")


class InquiryCreateRequest(BaseModel):
    car_id: int | None = Field(None, description="Optional car ID")
    inquiry_type: str = Field("contact", description="contact or test_drive")
    name: str = Field(..., min_length=1, max_length=120, description="Customer name")
    email: str = Field(..., min_length=3, max_length=240, description="Customer email")
    phone: str | None = Field(None, max_length=40, description="Optional phone number")
    message: str | None = Field(None, max_length=4000, description="Optional message")


class InquiryOut(BaseModel):
    id: int = Field(..., description="Inquiry ID")
    car_id: int | None = Field(None, description="Car ID")
    inquiry_type: str = Field(..., description="contact or test_drive")
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    phone: str | None = Field(None, description="Phone")
    message: str | None = Field(None, description="Message")
    created_at: datetime = Field(..., description="Created timestamp")


class AdminCarUpsert(BaseModel):
    make: str = Field(..., description="Manufacturer")
    model: str = Field(..., description="Model name")
    year: int = Field(..., ge=1900, le=2100, description="Model year")
    trim: str | None = Field(None, description="Trim")
    price_msrp: float | None = Field(None, ge=0, description="MSRP")
    currency: str = Field("USD", description="Currency code")
    description: str | None = Field(None, description="Description")
    specs: dict[str, Any] | None = Field(None, description="Specs JSON")
    category_id: int | None = Field(None, description="Category")
    is_published: bool = Field(True, description="Published flag")


class AdminCategoryUpsert(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, description="Category name")
    slug: str = Field(..., min_length=1, max_length=120, description="Category slug")


class AdminCarImageUpsert(BaseModel):
    url: str = Field(..., description="Image URL")
    alt: str | None = Field(None, description="Alt text")
    sort_order: int = Field(0, description="Sort order")
    is_primary: bool = Field(False, description="Is primary")
