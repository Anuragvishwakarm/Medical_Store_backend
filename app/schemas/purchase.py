from datetime import date, datetime
from pydantic import BaseModel, Field
from app.models.purchase import PurchaseStatus


class PurchaseItemCreate(BaseModel):
    medicine_id: int
    batch_number: str
    expiry_date: date
    manufacture_date: date | None = None
    quantity_strips: int = Field(..., ge=1)
    purchase_price_per_strip: float = Field(..., gt=0)
    mrp_per_strip: float = Field(..., gt=0)
    sale_price_per_strip: float = Field(..., gt=0)
    gst_rate: float = Field(12.0, ge=0, le=100)


class PurchaseCreate(BaseModel):
    invoice_number: str
    supplier_id: int
    purchase_date: date
    discount_amount: float = Field(0, ge=0)
    notes: str | None = None
    items: list[PurchaseItemCreate] = Field(..., min_length=1)


class PurchaseItemOut(BaseModel):
    id: int
    medicine_id: int
    batch_id: int | None
    quantity_strips: int
    purchase_price_per_strip: float
    mrp_per_strip: float
    sale_price_per_strip: float
    gst_rate: float
    line_total: float

    model_config = {"from_attributes": True}


class PurchaseOut(BaseModel):
    id: int
    invoice_number: str
    supplier_id: int
    purchase_date: date
    status: PurchaseStatus
    subtotal: float
    discount_amount: float
    gst_amount: float
    total_amount: float
    notes: str | None
    items: list[PurchaseItemOut]
    created_at: datetime

    model_config = {"from_attributes": True}
