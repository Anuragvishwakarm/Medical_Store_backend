"""Utility helpers shared across services."""
from datetime import datetime


def generate_order_number() -> str:
    """Generate a unique order number like ORD-20240715-00001."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"ORD-{ts}"


def calculate_line_total(
    quantity: int,
    price_per_unit: float,
    discount_percent: float,
    gst_rate: float,
) -> tuple[float, float]:
    """
    Returns (line_total_with_gst, gst_amount).
    GST is calculated on post-discount price (as per Indian GST rules for retail pharma).
    """
    gross = quantity * price_per_unit
    discount_amount = gross * (discount_percent / 100)
    taxable = gross - discount_amount
    gst_amount = taxable * (gst_rate / 100)
    line_total = round(taxable + gst_amount, 2)
    return line_total, round(gst_amount, 2)
