from datetime import datetime
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Text, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    draft     = "draft"        # ← lowercase
    confirmed = "confirmed"
    cancelled = "cancelled"


class PaymentStatus(str, enum.Enum):
    pending = "pending"        # ← lowercase
    partial = "partial"
    paid    = "paid"


class Order(Base):
    __tablename__ = "orders"

    id:           Mapped[int]       = mapped_column(Integer, primary_key=True, index=True)
    order_number: Mapped[str]       = mapped_column(String(50), nullable=False, unique=True, index=True)
    customer_id:  Mapped[int | None]= mapped_column(Integer, ForeignKey("customers.id"))

    walk_in_name:        Mapped[str | None] = mapped_column(String(255))
    walk_in_phone:       Mapped[str | None] = mapped_column(String(20))
    prescription_number: Mapped[str | None] = mapped_column(String(100))
    doctor_name:         Mapped[str | None] = mapped_column(String(255))

    status:         Mapped[OrderStatus]  = mapped_column(Enum(OrderStatus),  default=OrderStatus.draft)
    payment_status: Mapped[PaymentStatus]= mapped_column(Enum(PaymentStatus),default=PaymentStatus.pending)

    subtotal:        Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount_percent:Mapped[float] = mapped_column(Numeric(5, 2),  default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    gst_amount:      Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_amount:    Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    paid_amount:     Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    balance_amount:  Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes:           Mapped[str | None] = mapped_column(Text)

    created_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    confirmed_at: Mapped[datetime | None]= mapped_column(DateTime(timezone=True))

    customer: Mapped["Customer"]      = relationship("Customer", back_populates="orders")
    items:    Mapped[list["OrderItem"]]= relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="order", lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id:    Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"),    nullable=False)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), nullable=False)
    batch_id:    Mapped[int] = mapped_column(Integer, ForeignKey("batches.id"),   nullable=False)

    quantity_units:      Mapped[int]   = mapped_column(Integer, nullable=False)
    sale_price_per_unit: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    mrp_per_unit:        Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    discount_percent:    Mapped[float] = mapped_column(Numeric(5, 2),  default=0)
    gst_rate:            Mapped[float] = mapped_column(Numeric(5, 2),  default=0)
    line_total:          Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    batch: Mapped["Batch"] = relationship("Batch", back_populates="order_items")