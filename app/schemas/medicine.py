from datetime import datetime
from pydantic import BaseModel, Field


class MedicineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    generic_name: str | None = None
    manufacturer: str | None = None
    category: str | None = None
    hsn_code: str | None = None
    gst_rate: float = Field(12.0, ge=0, le=100)
    units_per_strip: int = Field(10, ge=1)
    unit_label: str = "Tablet"
    min_stock_units: int = Field(0, ge=0)
    description: str | None = None


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: str | None = None
    generic_name: str | None = None
    manufacturer: str | None = None
    category: str | None = None
    gst_rate: float | None = None
    units_per_strip: int | None = None
    unit_label: str | None = None
    min_stock_units: int | None = None
    is_active: bool | None = None
    description: str | None = None


class MedicineOut(MedicineBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MedicineWithStock(MedicineOut):
    """Medicine with aggregated stock info."""
    total_available_units: int = 0
    nearest_expiry_date: str | None = None
