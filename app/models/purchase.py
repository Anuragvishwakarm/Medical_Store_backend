from datetime import date, datetime
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Text, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class PurchaseStatus(str, enum.Enum):
    DRAFT = "draft"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(PurchaseStatus), default=PurchaseStatus.DRAFT
    )

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gst_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchases")
    items: Mapped[list["PurchaseItem"]] = relationship(
        "PurchaseItem", back_populates="purchase", cascade="all, delete-orphan", lazy="selectin"
    )


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_id: Mapped[int] = mapped_column(Integer, ForeignKey("purchases.id"), nullable=False)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), nullable=False)
    batch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("batches.id"))

    quantity_strips: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_price_per_strip: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    mrp_per_strip: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sale_price_per_strip: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=12.0)
    line_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="items")
    batch: Mapped["Batch"] = relationship("Batch", back_populates="purchase_item")
