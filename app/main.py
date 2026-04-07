from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers import (
    medicines,
    suppliers,
    purchases,
    customers,
    orders,
    payments,
    alerts,
    reports,
    invoices,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (use Alembic migrations in production)."""
    await create_tables()
    yield


app = FastAPI(
    title="Medical Store Management System",
    description=(
        "Full-featured POS + Inventory + Billing API for a medical store.\n\n"
        "**Key features:**\n"
        "- FEFO (First Expiry, First Out) batch allocation\n"
        "- Strip ↔ Unit conversion\n"
        "- Multi-batch selling\n"
        "- Draft → Confirm order flow\n"
        "- Partial / Full payment tracking\n"
        "- Expiry & Low-stock alerts\n"
        "- HTML invoice generation\n"
        "- Sales dashboard & reports\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medicines.router)
app.include_router(suppliers.router)
app.include_router(purchases.router)
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(invoices.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "app": "Medical Store Management System",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
