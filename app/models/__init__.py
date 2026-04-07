"""
models/__init__.py  — import all models so Alembic sees them.
"""
from app.models.medicine import Medicine
from app.models.batch import Batch
from app.models.supplier import Supplier
from app.models.purchase import Purchase, PurchaseItem
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.payment import Payment

__all__ = [
    "Medicine",
    "Batch",
    "Supplier",
    "Purchase",
    "PurchaseItem",
    "Customer",
    "Order",
    "OrderItem",
    "Payment",
]
