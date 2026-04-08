from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.batch import Batch
from app.models.medicine import Medicine
from app.models.purchase import Purchase, PurchaseItem, PurchaseStatus
from app.models.supplier import Supplier
from app.schemas.purchase import PurchaseCreate, PurchaseOut

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.post("/", response_model=PurchaseOut, status_code=201)
async def create_purchase(payload: PurchaseCreate, db: AsyncSession = Depends(get_db)):
    # Validate supplier
    supplier = await db.get(Supplier, payload.supplier_id)
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    # Check duplicate invoice
    existing = await db.execute(
        select(Purchase).where(Purchase.invoice_number == payload.invoice_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Invoice '{payload.invoice_number}' already exists")

    subtotal  = 0.0
    gst_total = 0.0
    db_items  = []

    for item in payload.items:
        medicine = await db.get(Medicine, item.medicine_id)
        if not medicine:
            raise HTTPException(404, f"Medicine ID {item.medicine_id} not found")

        line_subtotal = float(item.purchase_price_per_strip) * item.quantity_strips
        line_gst      = line_subtotal * (float(item.gst_rate) / 100)
        line_total    = line_subtotal + line_gst
        subtotal      += line_subtotal
        gst_total     += line_gst

        # Create batch — available_units = strips × units_per_strip
        available_units = item.quantity_strips * medicine.units_per_strip
        batch = Batch(
            medicine_id=item.medicine_id,
            batch_number=item.batch_number,
            expiry_date=item.expiry_date,
            manufacture_date=item.manufacture_date,
            purchase_price_per_strip=item.purchase_price_per_strip,
            mrp_per_strip=item.mrp_per_strip,
            sale_price_per_strip=item.sale_price_per_strip,
            quantity_strips=item.quantity_strips,
            sold_units=0,
            available_units=available_units,
        )
        db.add(batch)
        await db.flush()  # get batch.id

        pi = PurchaseItem(
            medicine_id=item.medicine_id,
            batch_id=batch.id,
            quantity_strips=item.quantity_strips,
            purchase_price_per_strip=item.purchase_price_per_strip,
            mrp_per_strip=item.mrp_per_strip,
            sale_price_per_strip=item.sale_price_per_strip,
            gst_rate=item.gst_rate,
            line_total=round(line_total, 2),
        )
        db_items.append(pi)

    total = subtotal + gst_total - float(payload.discount_amount)

    purchase = Purchase(
        invoice_number=payload.invoice_number,
        supplier_id=payload.supplier_id,
        purchase_date=payload.purchase_date,
        
        status=PurchaseStatus.received,
        subtotal=round(subtotal, 2),
        discount_amount=payload.discount_amount,
        gst_amount=round(gst_total, 2),
        total_amount=round(total, 2),
        notes=payload.notes,
    )
    db.add(purchase)
    await db.flush()

    for pi in db_items:
        pi.purchase_id = purchase.id
        db.add(pi)

    await db.flush()
    await db.refresh(purchase)
    return purchase


@router.get("/", response_model=list[PurchaseOut])
async def list_purchases(
    supplier_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(Purchase)
    if supplier_id:
        query = query.where(Purchase.supplier_id == supplier_id)
    result = await db.execute(
        query.order_by(Purchase.purchase_date.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{purchase_id}", response_model=PurchaseOut)
async def get_purchase(purchase_id: int, db: AsyncSession = Depends(get_db)):
    purchase = await db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(404, "Purchase not found")
    return purchase