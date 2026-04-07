from datetime import datetime
from pydantic import BaseModel


class CustomerBase(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    doctor_name: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    name: str | None = None
    is_active: bool | None = None


class CustomerOut(CustomerBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
