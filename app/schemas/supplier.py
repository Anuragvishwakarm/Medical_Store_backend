from datetime import datetime
from pydantic import BaseModel, EmailStr


class SupplierBase(BaseModel):
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    gst_number: str | None = None
    drug_license_number: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(SupplierBase):
    name: str | None = None
    is_active: bool | None = None


class SupplierOut(SupplierBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
