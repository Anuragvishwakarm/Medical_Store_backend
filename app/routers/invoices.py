from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderStatus
from app.services.invoice import generate_invoice_html

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/{order_id}", response_class=HTMLResponse, summary="Get printable HTML invoice")
async def get_invoice(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(409, "Invoice is only available for confirmed orders")

    html = await generate_invoice_html(order, db)
    return HTMLResponse(content=html)
