from datetime import datetime
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    generic_name: Mapped[str | None] = mapped_column(String(255))
    manufacturer: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))          # e.g. Tablet, Syrup, Injection
    hsn_code: Mapped[str | None] = mapped_column(String(20))           # for GST
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=12.0)
    
    # Unit conversion — how many units per strip
    units_per_strip: Mapped[int] = mapped_column(Integer, default=10)
    unit_label: Mapped[str] = mapped_column(String(50), default="Tablet")  # Tablet / ml / etc.

    # Minimum stock level for low-stock alert
    min_stock_units: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    batches: Mapped[list["Batch"]] = relationship("Batch", back_populates="medicine", lazy="selectin")
