from datetime import date, datetime
from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    medicine_id: int
    batch_number: str
    expiry_date: date
    manufacture_date: date | None = None
    purchase_price_per_strip: float = Field(..., gt=0)
    mrp_per_strip: float = Field(..., gt=0)
    sale_price_per_strip: float = Field(..., gt=0)
    quantity_strips: int = Field(..., ge=1)


class BatchUpdate(BaseModel):
    mrp_per_strip: float | None = None
    sale_price_per_strip: float | None = None
    is_active: bool | None = None


class BatchOut(BaseModel):
    id: int
    medicine_id: int
    batch_number: str
    expiry_date: date
    manufacture_date: date | None
    purchase_price_per_strip: float
    mrp_per_strip: float
    sale_price_per_strip: float
    quantity_strips: int
    sold_units: int
    available_units: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
