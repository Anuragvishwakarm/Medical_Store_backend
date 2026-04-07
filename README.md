# 🏥 Medical Store Management System

A production-ready REST API built with **FastAPI + PostgreSQL** for managing a medical store.
Covers inventory, purchases, sales (POS), billing, payments, expiry alerts, and reporting.

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.111 |
| Database | PostgreSQL (asyncpg driver) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Python | 3.11+ |

---

## 🗂️ Project Structure

```
medical_store/
├── app/
│   ├── main.py               # FastAPI app + router registration
│   ├── config.py             # Settings from .env
│   ├── database.py           # Async engine + session + Base
│   ├── models/
│   │   ├── medicine.py       # Medicine (with GST, unit conversion)
│   │   ├── batch.py          # Batch (FEFO stock per lot)
│   │   ├── supplier.py       # Supplier
│   │   ├── purchase.py       # Purchase + PurchaseItem
│   │   ├── customer.py       # Customer (registered + walk-in)
│   │   ├── order.py          # Order + OrderItem (Draft→Confirmed)
│   │   └── payment.py        # Payment (Cash/UPI/Card/NEFT/Cheque)
│   ├── schemas/              # Pydantic request/response models
│   ├── routers/
│   │   ├── medicines.py      # CRUD + stock info
│   │   ├── suppliers.py      # CRUD
│   │   ├── purchases.py      # Receive stock → auto-creates batches
│   │   ├── customers.py      # CRUD
│   │   ├── orders.py         # Create draft, confirm, cancel
│   │   ├── payments.py       # Add payments, track balance
│   │   ├── alerts.py         # Expiry / low-stock / expired stock
│   │   ├── reports.py        # Dashboard + sales summary + top medicines
│   │   └── invoices.py       # Printable HTML invoice
│   └── services/
│       ├── fefo.py           # FEFO batch selection logic
│       ├── invoice.py        # HTML invoice generator
│       └── utils.py          # Order number + GST calculation
├── alembic/
│   ├── env.py                # Async Alembic config
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py   # First migration (all tables)
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## 🚀 Setup & Run

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 14+

### 2. Clone & Install
```bash
git clone <repo-url>
cd medical_store
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/medical_store
SECRET_KEY=your-super-secret-key
```

### 4. Create Database
```sql
CREATE DATABASE medical_store;
```

### 5. Run Migrations
```bash
alembic upgrade head
```

### 6. Start Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 📋 API Endpoints

### 💊 Medicines — `/medicines`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/medicines/` | Add a new medicine |
| GET | `/medicines/` | List all (search, category, low_stock filter) |
| GET | `/medicines/{id}` | Get one with live stock info |
| PATCH | `/medicines/{id}` | Update |
| DELETE | `/medicines/{id}` | Soft-delete |

### 🏭 Suppliers — `/suppliers`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/suppliers/` | Add supplier |
| GET | `/suppliers/` | List (with search) |
| GET | `/suppliers/{id}` | Get one |
| PATCH | `/suppliers/{id}` | Update |

### 🛒 Purchases — `/purchases`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/purchases/` | Receive stock — creates batches automatically |
| GET | `/purchases/` | List purchases |
| GET | `/purchases/{id}` | Get one with items |

### 👥 Customers — `/customers`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/customers/` | Add customer |
| GET | `/customers/` | List (name/phone search) |
| GET | `/customers/{id}` | Get one |
| PATCH | `/customers/{id}` | Update |

### 🧾 Orders — `/orders`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/orders/` | Create DRAFT order (FEFO allocation happens here) |
| POST | `/orders/{id}/confirm` | Confirm — deducts stock, records initial payment |
| POST | `/orders/{id}/cancel` | Cancel a DRAFT order |
| GET | `/orders/` | List (filter by status, payment_status, customer) |
| GET | `/orders/{id}` | Get one with items |

### 💳 Payments — `/payments`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/payments/` | Add payment to a confirmed order |
| GET | `/payments/order/{order_id}` | All payments for an order |

### 🔔 Alerts — `/alerts`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/alerts/expiry?days=30` | Batches expiring within N days |
| GET | `/alerts/low-stock` | Medicines below minimum stock level |
| GET | `/alerts/expired` | Expired batches with remaining stock |

### 📊 Reports — `/reports`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/reports/dashboard` | Today/month sales, pending balance, alerts count |
| GET | `/reports/sales-summary` | Day-wise sales breakdown |
| GET | `/reports/top-medicines` | Top medicines by revenue |

### 🖨️ Invoices — `/invoices`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/invoices/{order_id}` | Printable HTML invoice |

---

## 🔄 Core Business Flow

```
1. Add Medicines        → POST /medicines/
2. Add Suppliers        → POST /suppliers/
3. Receive Stock        → POST /purchases/   (auto-creates Batches)
4. Create Order (Draft) → POST /orders/      (FEFO selects batches)
5. Confirm Order        → POST /orders/{id}/confirm  (deducts stock)
6. Add Payments         → POST /payments/    (partial/full)
7. Print Invoice        → GET  /invoices/{id}
```

---

## ⚙️ Key Business Logic

### FEFO — First Expiry, First Out
When a sale is created, `services/fefo.py` picks batches in **ascending expiry date order**.
If quantity spans multiple batches, it auto-splits across them.
Expired batches and batches with zero stock are automatically skipped.

### Strip ↔ Unit Conversion
- Each medicine has `units_per_strip` (e.g. 10 tablets per strip).
- Purchases are entered in **strips**; stock is stored in **units**.
- Sales are billed in **units** with price = `sale_price_per_strip / units_per_strip`.

### GST Calculation (Indian pharma rules)
```
taxable = quantity × unit_price × (1 - discount%)
gst     = taxable × gst_rate%
total   = taxable + gst
```

### Order States
```
DRAFT ──confirm──▶ CONFIRMED
DRAFT ──cancel──▶  CANCELLED
CONFIRMED          (cannot cancel — raise a return)
```

### Payment States
```
PENDING ──partial payment──▶ PARTIAL ──full payment──▶ PAID
PENDING ──full payment──▶    PAID
```

---

## 🔧 Common Commands

```bash
# New migration after model changes
alembic revision --autogenerate -m "describe change"
alembic upgrade head

# Rollback one step
alembic downgrade -1

# Run with auto-reload
uvicorn app.main:app --reload

# Run in production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🛡️ Production Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `allow_origins` to your frontend domain in CORS middleware
- [ ] Use `--workers 4` (or more) with uvicorn
- [ ] Enable SSL / put Nginx in front
- [ ] Set up database connection pooling (PgBouncer)
- [ ] Add authentication (JWT middleware)
- [ ] Set up log aggregation

---

## 📝 Improvements Over Original Document

| Area | Original | Implemented |
|---|---|---|
| Tables | 4 tables listed | 8 fully normalized tables |
| Batch tracking | Not specified | Per-unit FEFO stock tracking |
| Customer | Missing | Full customer + walk-in support |
| Supplier | Missing | Supplier with GST & drug license |
| Payments | 3 states mentioned | Full `payments` table with mode + reference |
| GST/HSN | Not mentioned | GST per medicine + HSN code |
| Order states | Draft/Confirm | Draft → Confirmed → Cancelled |
| Pricing snapshot | Not mentioned | Price locked at time of sale on `order_items` |
| Alerts | 7/30 days expiry + low stock | + expired-with-stock alert |
| Reports | Phase 5 only | Dashboard + day-wise + top medicines |
| Invoice | Listed as feature | Full HTML invoice with GST breakdown |
| Migrations | Not mentioned | Full Alembic setup with initial migration |
