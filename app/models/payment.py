from datetime import datetime
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Text, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class PaymentMode(str, enum.Enum):
    cash   = "cash"      # ← lowercase
    upi    = "upi"
    card   = "card"
    neft   = "neft"
    cheque = "cheque"


class Payment(Base):
    __tablename__ = "payments"

    id:               Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    order_id:         Mapped[int]         = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    amount:           Mapped[float]       = mapped_column(Numeric(12, 2), nullable=False)
    mode:             Mapped[PaymentMode] = mapped_column(Enum(PaymentMode), default=PaymentMode.cash)
    reference_number: Mapped[str | None]  = mapped_column(String(100))
    notes:            Mapped[str | None]  = mapped_column(Text)
    paid_at:          Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship("Order", back_populates="payments")