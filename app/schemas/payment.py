from datetime import datetime
from pydantic import BaseModel, Field
from app.models.payment import PaymentMode


class PaymentCreate(BaseModel):
    order_id: int
    amount: float = Field(..., gt=0)
    mode: PaymentMode = PaymentMode.cash          # ← lowercase
    reference_number: str | None = None
    notes: str | None = None


class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: float
    mode: PaymentMode
    reference_number: str | None
    notes: str | None
    paid_at: datetime

    model_config = {"from_attributes": True}