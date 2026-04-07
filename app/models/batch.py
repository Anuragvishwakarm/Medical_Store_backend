from datetime import date, datetime
from sqlalchemy import String, Integer, Numeric, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Batch(Base):
    """
    One batch = one purchase lot of a medicine.
    Stock is tracked at batch level to support FEFO.
    """
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), nullable=False, index=True)

    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    manufacture_date: Mapped[date | None] = mapped_column(Date)

    # Pricing per strip
    purchase_price_per_strip: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    mrp_per_strip: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sale_price_per_strip: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Stock in units (strips × units_per_strip)
    quantity_strips: Mapped[int] = mapped_column(Integer, default=0)    # total received (strips)
    sold_units: Mapped[int] = mapped_column(Integer, default=0)         # total sold (units)
    available_units: Mapped[int] = mapped_column(Integer, default=0)    # remaining (units)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="batches")
    purchase_item: Mapped["PurchaseItem"] = relationship("PurchaseItem", back_populates="batch", uselist=False)
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="batch")
