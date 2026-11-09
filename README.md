# 📊 Finance Dashboard

A full-stack application that lets users upload a **CSV or Excel (.xlsx)** file
with monthly financial data, stores it in **MySQL**, and displays it as a
**table** and **bar chart**.

---

## ⚙️ Features
- Upload `.xlsx` or `.csv` files (month + amount columns)
- Parses & stores records in MySQL, skipping duplicate month/year rows
- Retrieve data via a small REST API
- Interactive dashboard: sortable table, Chart.js bar chart, totals summary

---

## 🗄️ Database Setup

1. Copy `backend/.env.example` to `backend/.env` and set your own DB password.
2. Create the database and tables:
   ```bash
   mysql -u root -p < backend/db_setup.sql
   ```
   This creates **both** `finance_db` (used by the running app) and
   `finance_test_db` (used by the automated tests).

---

## ▶️ Running the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

export DB_PASSWORD=your-password  # or load backend/.env
python app.py
```

The API listens on `http://127.0.0.1:5000` by default (override with `PORT`).

---

## ▶️ Running the frontend

The frontend is a single static file — no build step required:

```bash
cd frontend
python -m http.server 8000
```

Then open `http://127.0.0.1:8000` in your browser. If your backend runs on a
different host/port, update the `API_BASE` constant near the top of the
`<script>` block in `frontend/index.html`.

---

## ✅ Running tests

```bash
cd backend
python -m unittest test_app.py -v
python -m unittest test_integration.py -v
```

`test_integration.py` needs a real MySQL connection (it creates/drops tables
in `finance_test_db` automatically). `test_app.py` mocks around the DB layer
where possible.
