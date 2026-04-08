"""
Professional A4 Invoice Service with Print Support
"""
from app.models.order import Order
from app.models.medicine import Medicine
from app.models.batch import Batch
from app.models.customer import Customer
from sqlalchemy.ext.asyncio import AsyncSession


INVOICE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invoice {order_number}</title>
<style>
  /* ── Reset ── */
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  /* ── Screen styles ── */
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #e5e7eb;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
    color: #1f2937;
  }}

  /* ── Print toolbar ── */
  .toolbar {{
    width: 210mm;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-bottom: 12px;
  }}
  .btn {{
    padding: 8px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
  }}
  .btn-print {{
    background: #0694a2;
    color: white;
  }}
  .btn-print:hover {{ background: #047481; }}
  .btn-close {{
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
  }}
  .btn-close:hover {{ background: #e5e7eb; }}

  /* ── A4 Paper ── */
  .page {{
    width: 210mm;
    min-height: 297mm;
    background: white;
    padding: 12mm 14mm;
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
    position: relative;
    display: flex;
    flex-direction: column;
  }}

  /* ── Header ── */
  .invoice-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 3px solid #0694a2;
    padding-bottom: 12px;
    margin-bottom: 14px;
  }}
  .store-info h1 {{
    font-size: 22px;
    color: #0694a2;
    font-weight: 700;
    letter-spacing: -0.5px;
  }}
  .store-info p {{
    font-size: 11px;
    color: #6b7280;
    margin-top: 2px;
  }}
  .invoice-meta {{
    text-align: right;
  }}
  .invoice-meta .inv-title {{
    font-size: 18px;
    font-weight: 700;
    color: #111827;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  .invoice-meta .inv-number {{
    font-size: 11px;
    color: #6b7280;
    margin-top: 4px;
    font-family: monospace;
  }}
  .invoice-meta .inv-date {{
    font-size: 11px;
    color: #374151;
    margin-top: 3px;
  }}

  /* ── Info Grid ── */
  .info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
    margin-bottom: 16px;
  }}
  .info-box {{
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 10px 12px;
  }}
  .info-box .label {{
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #9ca3af;
    margin-bottom: 5px;
  }}
  .info-box .value {{
    font-size: 12px;
    font-weight: 600;
    color: #111827;
    line-height: 1.5;
  }}
  .info-box .value span {{
    font-weight: 400;
    color: #4b5563;
  }}

  /* ── Status Badge ── */
  .badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .badge-paid    {{ background: #d1fae5; color: #065f46; }}
  .badge-partial {{ background: #fef3c7; color: #92400e; }}
  .badge-pending {{ background: #fee2e2; color: #991b1b; }}

  /* ── Items Table ── */
  .items-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
    font-size: 11.5px;
  }}
  .items-table thead tr {{
    background: #0694a2;
    color: white;
  }}
  .items-table thead th {{
    padding: 9px 10px;
    text-align: left;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
  }}
  .items-table thead th.right {{ text-align: right; }}
  .items-table tbody tr {{ border-bottom: 1px solid #f3f4f6; }}
  .items-table tbody tr:nth-child(even) {{ background: #f9fafb; }}
  .items-table tbody td {{
    padding: 8px 10px;
    color: #374151;
    vertical-align: middle;
  }}
  .items-table tbody td.right {{ text-align: right; font-weight: 600; }}
  .items-table tbody td.center {{ text-align: center; }}
  .items-table .med-name {{ font-weight: 600; color: #111827; }}
  .items-table .batch-no {{ font-family: monospace; font-size: 10px; color: #6b7280; }}
  .items-table tfoot td {{
    padding: 6px 10px;
    font-size: 11px;
    color: #6b7280;
    font-style: italic;
  }}

  /* ── Summary ── */
  .summary-section {{
    display: flex;
    justify-content: flex-end;
    margin-top: auto;
    margin-bottom: 16px;
  }}
  .summary-box {{
    width: 230px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
  }}
  .summary-row {{
    display: flex;
    justify-content: space-between;
    padding: 7px 14px;
    font-size: 12px;
    border-bottom: 1px solid #f3f4f6;
  }}
  .summary-row:last-child {{ border-bottom: none; }}
  .summary-row .s-label {{ color: #6b7280; }}
  .summary-row .s-value {{ font-weight: 600; color: #111827; }}
  .summary-row.discount .s-value {{ color: #dc2626; }}
  .summary-row.gst .s-value {{ color: #d97706; }}
  .summary-row.total {{
    background: #0694a2;
    padding: 10px 14px;
  }}
  .summary-row.total .s-label,
  .summary-row.total .s-value {{
    color: white;
    font-size: 14px;
    font-weight: 700;
  }}
  .summary-row.paid .s-value {{ color: #059669; }}
  .summary-row.balance .s-value {{ color: {balance_color}; }}

  /* ── Footer ── */
  .invoice-footer {{
    border-top: 1px solid #e5e7eb;
    padding-top: 10px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .footer-note {{
    font-size: 9.5px;
    color: #9ca3af;
    max-width: 320px;
    line-height: 1.5;
  }}
  .signature-box {{
    text-align: center;
  }}
  .signature-line {{
    width: 120px;
    border-top: 1px solid #374151;
    margin: 20px auto 4px;
  }}
  .signature-label {{
    font-size: 10px;
    color: #6b7280;
  }}

  /* ── Print styles ── */
  @media print {{
    body {{
      background: white;
      padding: 0;
    }}
    .toolbar {{ display: none !important; }}
    .page {{
      width: 100%;
      min-height: auto;
      box-shadow: none;
      padding: 10mm 12mm;
    }}
    @page {{
      size: A4;
      margin: 0;
    }}
  }}
</style>
</head>
<body>

<!-- Print Toolbar -->
<div class="toolbar">
  <button class="btn btn-close" onclick="window.close()">✕ Close</button>
  <button class="btn btn-print" onclick="window.print()">🖨️ Print Invoice</button>
</div>

<!-- A4 Page -->
<div class="page">

  <!-- Header -->
  <div class="invoice-header">
    <div class="store-info">
      <h1>🏥 Medical Store</h1>
      <p>Retail Pharmacy · Drug License: DL/MH/2020/1234</p>
      <p>GST No: 27AAACS1234A1Z5</p>
      <p>📞 +91 98765 43210 &nbsp;|&nbsp; 📧 store@medstore.com</p>
    </div>
    <div class="invoice-meta">
      <div class="inv-title">GST Invoice</div>
      <div class="inv-number">#{order_number}</div>
      <div class="inv-date">📅 {date}</div>
      <div style="margin-top:6px">
        <span class="badge badge-{pay_badge}">{payment_status}</span>
      </div>
    </div>
  </div>

  <!-- Info Grid -->
  <div class="info-grid">
    <div class="info-box">
      <div class="label">Bill To</div>
      <div class="value">{customer_name}<br><span>{customer_phone}</span></div>
    </div>
    <div class="info-box">
      <div class="label">Doctor / Prescription</div>
      <div class="value">
        Dr. {doctor_name}<br>
        <span>Rx# {prescription_number}</span>
      </div>
    </div>
    <div class="info-box">
      <div class="label">Payment Summary</div>
      <div class="value">
        Total: ₹{total_amount}<br>
        <span>Paid: ₹{paid_amount} &nbsp;|&nbsp; Due: ₹{balance_amount}</span>
      </div>
    </div>
  </div>

  <!-- Items Table -->
  <table class="items-table">
    <thead>
      <tr>
        <th style="width:28px">#</th>
        <th>Medicine</th>
        <th>Batch No</th>
        <th>Expiry</th>
        <th class="center">Qty</th>
        <th class="right">Rate/Unit</th>
        <th class="center">Disc%</th>
        <th class="center">GST%</th>
        <th class="right">Amount</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
    <tfoot>
      <tr>
        <td colspan="9">
          * All prices are inclusive of GST as per Indian GST regulations for retail pharmacy.
        </td>
      </tr>
    </tfoot>
  </table>

  <!-- Summary -->
  <div class="summary-section">
    <div class="summary-box">
      <div class="summary-row">
        <span class="s-label">Subtotal</span>
        <span class="s-value">₹{subtotal}</span>
      </div>
      <div class="summary-row discount">
        <span class="s-label">Discount</span>
        <span class="s-value">− ₹{discount_amount}</span>
      </div>
      <div class="summary-row gst">
        <span class="s-label">GST</span>
        <span class="s-value">+ ₹{gst_amount}</span>
      </div>
      <div class="summary-row total">
        <span class="s-label">TOTAL</span>
        <span class="s-value">₹{total_amount}</span>
      </div>
      <div class="summary-row paid">
        <span class="s-label">Paid</span>
        <span class="s-value">₹{paid_amount}</span>
      </div>
      <div class="summary-row balance">
        <span class="s-label">Balance Due</span>
        <span class="s-value">₹{balance_amount}</span>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="invoice-footer">
    <div class="footer-note">
      <strong>Terms & Conditions:</strong><br>
      • Medicines once sold are not returnable without valid prescription.<br>
      • Check expiry date before consuming medicine.<br>
      • This is a computer-generated invoice, no signature required.
    </div>
    <div class="signature-box">
      <div class="signature-line"></div>
      <div class="signature-label">Authorized Signature</div>
    </div>
  </div>

</div>

<script>
  // Auto open print dialog (optional — comment out if not needed)
  // window.onload = () => window.print();
</script>
</body>
</html>
"""

ROW_TEMPLATE = """
<tr>
  <td style="color:#9ca3af;font-size:11px">{sr}</td>
  <td>
    <div class="med-name">{medicine_name}</div>
  </td>
  <td><span class="batch-no">{batch_number}</span></td>
  <td style="font-size:11px;color:#374151">{expiry_date}</td>
  <td class="center">{qty}</td>
  <td class="right">₹{rate}</td>
  <td class="center">{disc}%</td>
  <td class="center">{gst}%</td>
  <td class="right">₹{amount}</td>
</tr>
"""


async def generate_invoice_html(order: Order, db: AsyncSession) -> str:

    # ── Customer ───────────────────────────────────────────────
    customer_name  = "Walk-in Customer"
    customer_phone = "—"
    if order.customer_id:
        customer = await db.get(Customer, order.customer_id)
        if customer:
            customer_name  = customer.name
            customer_phone = customer.phone or "—"
    elif order.walk_in_name:
        customer_name  = order.walk_in_name
        customer_phone = order.walk_in_phone or "—"

    # ── Items ──────────────────────────────────────────────────
    rows_html = ""
    for i, item in enumerate(order.items, 1):
        medicine = await db.get(Medicine, item.medicine_id)
        batch    = await db.get(Batch,    item.batch_id)

        rows_html += ROW_TEMPLATE.format(
            sr=i,
            medicine_name=medicine.name if medicine else f"Medicine #{item.medicine_id}",
            batch_number=batch.batch_number if batch else "—",
            expiry_date=str(batch.expiry_date) if batch else "—",
            qty=item.quantity_units,
            rate=f"{float(item.sale_price_per_unit):.2f}",
            disc=f"{float(item.discount_percent):.1f}",
            gst=f"{float(item.gst_rate):.1f}",
            amount=f"{float(item.line_total):.2f}",
        )

    # ── Payment status ─────────────────────────────────────────
    pay_val    = order.payment_status.value if hasattr(order.payment_status, 'value') else str(order.payment_status)
    pay_badge  = pay_val  # paid / partial / pending
    pay_label  = pay_val.upper()
    bal_color  = "#059669" if float(order.balance_amount) <= 0 else "#dc2626"

    # ── Date ──────────────────────────────────────────────────
    date_str = (order.confirmed_at or order.created_at).strftime("%d %b %Y, %I:%M %p")

    return INVOICE_HTML.format(
        order_number=order.order_number,
        date=date_str,
        customer_name=customer_name,
        customer_phone=customer_phone,
        doctor_name=order.doctor_name or "—",
        prescription_number=order.prescription_number or "—",
        rows=rows_html,
        subtotal=f"{float(order.subtotal):,.2f}",
        discount_amount=f"{float(order.discount_amount):,.2f}",
        gst_amount=f"{float(order.gst_amount):,.2f}",
        total_amount=f"{float(order.total_amount):,.2f}",
        paid_amount=f"{float(order.paid_amount):,.2f}",
        balance_amount=f"{float(order.balance_amount):,.2f}",
        pay_badge=pay_badge,
        payment_status=pay_label,
        balance_color=bal_color,
    )