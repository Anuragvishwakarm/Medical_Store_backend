"""Initial migration — create all tables

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── medicines ─────────────────────────────────────────────
    op.create_table(
        "medicines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("generic_name", sa.String(255)),
        sa.Column("manufacturer", sa.String(255)),
        sa.Column("category", sa.String(100)),
        sa.Column("hsn_code", sa.String(20)),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False, server_default="12.0"),
        sa.Column("units_per_strip", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("unit_label", sa.String(50), nullable=False, server_default="Tablet"),
        sa.Column("min_stock_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_medicines_name", "medicines", ["name"])

    # ── suppliers ─────────────────────────────────────────────
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact_person", sa.String(255)),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("address", sa.Text()),
        sa.Column("gst_number", sa.String(20)),
        sa.Column("drug_license_number", sa.String(50)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── batches ───────────────────────────────────────────────
    op.create_table(
        "batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("medicine_id", sa.Integer(), sa.ForeignKey("medicines.id"), nullable=False),
        sa.Column("batch_number", sa.String(100), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("manufacture_date", sa.Date()),
        sa.Column("purchase_price_per_strip", sa.Numeric(10, 2), nullable=False),
        sa.Column("mrp_per_strip", sa.Numeric(10, 2), nullable=False),
        sa.Column("sale_price_per_strip", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity_strips", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sold_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_batches_medicine_id", "batches", ["medicine_id"])
    op.create_index("ix_batches_expiry_date", "batches", ["expiry_date"])

    # ── customers ─────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("address", sa.String(500)),
        sa.Column("doctor_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_customers_phone", "customers", ["phone"])

    # ── purchases ─────────────────────────────────────────────
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_number", sa.String(100), nullable=False, unique=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "received", "cancelled", name="purchasestatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("subtotal", sa.Numeric(12, 2), server_default="0"),
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("gst_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── purchase_items ────────────────────────────────────────
    op.create_table(
        "purchase_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_id", sa.Integer(), sa.ForeignKey("purchases.id"), nullable=False),
        sa.Column("medicine_id", sa.Integer(), sa.ForeignKey("medicines.id"), nullable=False),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("batches.id")),
        sa.Column("quantity_strips", sa.Integer(), nullable=False),
        sa.Column("purchase_price_per_strip", sa.Numeric(10, 2), nullable=False),
        sa.Column("mrp_per_strip", sa.Numeric(10, 2), nullable=False),
        sa.Column("sale_price_per_strip", sa.Numeric(10, 2), nullable=False),
        sa.Column("gst_rate", sa.Numeric(5, 2), server_default="12.0"),
        sa.Column("line_total", sa.Numeric(12, 2), server_default="0"),
    )

    # ── orders ────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_number", sa.String(50), nullable=False, unique=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id")),
        sa.Column("walk_in_name", sa.String(255)),
        sa.Column("walk_in_phone", sa.String(20)),
        sa.Column("prescription_number", sa.String(100)),
        sa.Column("doctor_name", sa.String(255)),
        sa.Column(
            "status",
            sa.Enum("draft", "confirmed", "cancelled", name="orderstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "payment_status",
            sa.Enum("pending", "partial", "paid", name="paymentstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("subtotal", sa.Numeric(12, 2), server_default="0"),
        sa.Column("discount_percent", sa.Numeric(5, 2), server_default="0"),
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("gst_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("paid_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("balance_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_orders_order_number", "orders", ["order_number"])

    # ── order_items ───────────────────────────────────────────
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("medicine_id", sa.Integer(), sa.ForeignKey("medicines.id"), nullable=False),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("batches.id"), nullable=False),
        sa.Column("quantity_units", sa.Integer(), nullable=False),
        sa.Column("sale_price_per_unit", sa.Numeric(10, 4), nullable=False),
        sa.Column("mrp_per_unit", sa.Numeric(10, 4), nullable=False),
        sa.Column("discount_percent", sa.Numeric(5, 2), server_default="0"),
        sa.Column("gst_rate", sa.Numeric(5, 2), server_default="0"),
        sa.Column("line_total", sa.Numeric(12, 2), server_default="0"),
    )

    # ── payments ──────────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "mode",
            sa.Enum("cash", "upi", "card", "neft", "cheque", name="paymentmode"),
            nullable=False,
            server_default="cash",
        ),
        sa.Column("reference_number", sa.String(100)),
        sa.Column("notes", sa.Text()),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("purchase_items")
    op.drop_table("purchases")
    op.drop_table("customers")
    op.drop_table("batches")
    op.drop_table("suppliers")
    op.drop_table("medicines")
    op.execute("DROP TYPE IF EXISTS paymentmode")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS purchasestatus")
