# Breathe ESG — Carbon Emissions Data Ingestion & Review Platform

Breathe ESG is an advanced carbon data ingestion, normalization, and audit-review dashboard designed for modern enterprise greenhouse gas (GHG) reporting. It ingests CSV logs from three distinct corporate sources, normalizes metrics into metric values, automatically flags compliance anomalies, and exposes an analyst review console to approve, reject, and lock records before compliance audits.

---

## 🚀 Tech Stack
- **Backend**: Python 3.9, Django 4.2, Django REST Framework, Pandas (CSV Parsing), SQLite / PostgreSQL
- **Frontend**: React 18, Vite, Tailwind CSS, Axios, Lucide Icons

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.9+** and **Node.js 18+** installed on your system.

### 2. Backend Setup
Navigate to the root workspace directory `/Users/riteshsingh/Documents/breatheesg`:

1. **Activate the Virtual Environment**:
   ```bash
   source venv/bin/activate
   ```
2. **Apply Migrations**:
   ```bash
   python backend/manage.py migrate
   ```
3. **Seed Database**:
   This creates a default Superuser / Analyst account and a default Client ("Acme Corporation").
   ```bash
   python backend/manage.py seed_db
   ```
4. **Start the Django Server**:
   ```bash
   python backend/manage.py runserver
   ```
   The backend API will start on **`http://localhost:8000/`**.

### 3. Frontend Setup
Open a new terminal window, navigate to the `frontend/` directory, and start the development server:

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```
2. **Start Vite Server**:
   ```bash
   npm run dev
   ```
   The interactive dashboard will start on **`http://localhost:5173/`**.

---

## 🔑 Login Credentials

The database seeding script creates a default superuser account for the Django Admin panel:
- **Admin Panel URL**: `http://localhost:8000/admin/`
- **Username**: `admin`
- **Password**: `admin`
- **Email**: `admin@breatheesg.com`

---

## 📈 Testing Ingestion & Review Flow

### Step 1: Upload Data Sources
Navigate to the **Ingest Data** page on the frontend (`http://localhost:5173/upload`):
1. **SAP Fuel (Scope 1)**: Drag and drop or browse `sample_data/sap_sample.csv` and click **Ingest Data**.
2. **Utility Power (Scope 2)**: Upload `sample_data/utility_sample.csv`.
3. **Travel Log (Scope 3)**: Upload `sample_data/travel_sample.csv`.

*The upload cards will show full loading states and display success/error notifications indicating rows processed.*

### Step 2: Analyze & Filter Anomalies
Navigate to the **Review Dashboard** page (`http://localhost:5173/dashboard`):
- Observe the **KPI Cards** updated dynamically: total record counts, approved emissions (CO2e), and flagging tallies.
- Utilize the **Query Filters** (Source, Scope, Status, and Text search) to drill down into anomalous entries.
- Review **Suspicious Badges** (hover to see descriptions) like:
  - `OUTLIER`: Fuel quantities 3x above average or flight distances exceeding 20,000 km.
  - `DUPLICATE`: Identical transaction IDs or overlapping utility billing cycles.
  - `UNIT_MISMATCH`: Unrecognized unit values (e.g. `LBS`).
  - `DATE_GAP`: Gaps between consecutive electricity bill dates for the same meter.
  - `ZERO_VALUE`: Gaps or zero-consumption meter readings.

### Step 3: Approve & Reject Audit Records
- **Approve**: Click **Approve** on a record. This locks the record, disables actions, and creates an `APPROVED` entry in the `AuditLog` timeline.
- **Reject**: Click **Reject** on a record. A modal will prompt you to enter a mandatory justification note (e.g. "needs invoice upload validation"). The record status changes to `REJECTED` and logs the note.
- **Bulk Approve**: Select multiple records using the row checkboxes and click **Bulk Approve Selected** to process them in a single batch transaction.
- **Detailed History**: Click the **Eye icon** on any row to open the **Record Detail View** to inspect:
  - The step-by-step unit conversion equations.
  - The immutable raw JSON CSV row.
  - The comprehensive **Audit Lifecycle Timeline**.
