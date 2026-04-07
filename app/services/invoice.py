"""
Invoice generation service.
Returns an HTML string for a confirmed order.
Can be extended to produce PDF with weasyprint.
"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.medicine import Medicine


INVOICE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; font-size: 13px; padding: 20px; }}
    h2 {{ text-align: center; margin: 0; }}
    .header {{ text-align: center; margin-bottom: 20px; }}
    .meta {{ display: flex; justify-content: space-between; margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    .totals {{ margin-top: 10px; text-align: right; }}
    .totals td {{ border: none; padding: 2px 10px; }}
    .paid {{ color: green; font-weight: bold; }}
    .pending {{ color: red; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="header">
    <h2>Medical Store</h2>
    <p>GST Invoice</p>
  </div>

  <div class="meta">
    <div>
      <b>Invoice #:</b> {order_number}<br>
      <b>Date:</b> {date}<br>
      {customer_info}
    </div>
    <div>
      <b>Prescription #:</b> {prescription_number}<br>
      <b>Doctor:</b> {doctor_name}<br>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Medicine</th>
        <th>Batch</th>
        <th>Expiry</th>
        <th>Qty (Units)</th>
        <th>Rate</th>
        <th>Disc%</th>
        <th>GST%</th>
        <th>Amount</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>

  <table class="totals">
    <tr><td>Subtotal:</td><td>₹{subtotal}</td></tr>
    <tr><td>Discount:</td><td>- ₹{discount_amount}</td></tr>
    <tr><td>GST:</td><td>+ ₹{gst_amount}</td></tr>
    <tr><td><b>Total:</b></td><td><b>₹{total_amount}</b></td></tr>
    <tr><td>Paid:</td><td class="paid">₹{paid_amount}</td></tr>
    <tr><td>Balance:</td><td class="{balance_class}">₹{balance_amount}</td></tr>
  </table>

  <p style="margin-top:20px; font-size:11px; color:#666;">
    This is a computer-generated invoice. Medicines once sold are not returnable without a valid reason.
  </p>
</body>
</html>
"""

ROW_TEMPLATE = """
<tr>
  <td>{sr}</td>
  <td>{medicine_name}</td>
  <td>{batch_number}</td>
  <td>{expiry_date}</td>
  <td>{qty}</td>
  <td>₹{rate}</td>
  <td>{disc}%</td>
  <td>{gst}%</td>
  <td>₹{amount}</td>
</tr>
"""


async def generate_invoice_html(order: Order, db: AsyncSession) -> str:
    """Build invoice HTML for a confirmed order."""

    customer_info = ""
    if order.customer_id and order.customer:
        c = order.customer
        customer_info = f"<b>Customer:</b> {c.name}<br><b>Phone:</b> {c.phone or '-'}"
    elif order.walk_in_name:
        customer_info = f"<b>Customer:</b> {order.walk_in_name}<br><b>Phone:</b> {order.walk_in_phone or '-'}"
    else:
        customer_info = "<b>Customer:</b> Walk-in"

    rows_html = ""
    for i, item in enumerate(order.items, 1):
        medicine = await db.get(Medicine, item.medicine_id)
        from app.models.batch import Batch
        batch = await db.get(Batch, item.batch_id)

        rows_html += ROW_TEMPLATE.format(
            sr=i,
            medicine_name=medicine.name if medicine else f"ID:{item.medicine_id}",
            batch_number=batch.batch_number if batch else "-",
            expiry_date=str(batch.expiry_date) if batch else "-",
            qty=item.quantity_units,
            rate=f"{item.sale_price_per_unit:.2f}",
            disc=f"{item.discount_percent:.1f}",
            gst=f"{item.gst_rate:.1f}",
            amount=f"{item.line_total:.2f}",
        )

    balance_class = "paid" if float(order.balance_amount) <= 0 else "pending"
    date_str = (order.confirmed_at or order.created_at).strftime("%d-%m-%Y %H:%M")

    return INVOICE_TEMPLATE.format(
        order_number=order.order_number,
        date=date_str,
        customer_info=customer_info,
        prescription_number=order.prescription_number or "-",
        doctor_name=order.doctor_name or "-",
        rows=rows_html,
        subtotal=f"{order.subtotal:.2f}",
        discount_amount=f"{order.discount_amount:.2f}",
        gst_amount=f"{order.gst_amount:.2f}",
        total_amount=f"{order.total_amount:.2f}",
        paid_amount=f"{order.paid_amount:.2f}",
        balance_amount=f"{order.balance_amount:.2f}",
        balance_class=balance_class,
    )
