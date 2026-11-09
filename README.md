# 📊 Finance Dashboard

Upload a **CSV or Excel (.xlsx)** file of monthly figures, store it in **MySQL**, and explore it as a **table**, **bar chart** and summary cards.

**Stack:** Python · Flask · MySQL · openpyxl · gunicorn · HTML/CSS/JS · Chart.js · nginx · Docker Compose · Postman/Newman · GitHub Actions

---

## Quick start (Docker)

```bash
cp .env.example .env        # then change the passwords
docker compose up --build
```

Open <http://localhost:8080>. The database schema is created automatically on first start, with a demo user (`User ID 1`).

## Running without Docker

```bash
# 1. Database (creates finance_db and finance_test_db)
mysql -u root -p < backend/db_setup.sql

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
export DB_PASSWORD=your-password                      # see backend/.env.example
python app.py                                         # http://127.0.0.1:5000

# 3. Frontend (second terminal)
cd frontend
python -m http.server 8000                            # http://127.0.0.1:8000
```

The frontend talks to `http://127.0.0.1:5000` by default; change `frontend/config.js` if your backend lives elsewhere.

---

## File format

Two columns with a header row: **Month** and **Amount**.

| Month    | Amount   |
|----------|----------|
| January  | 1000.50  |
| Feb      | 1,200.00 |

- Months can be full names or 3-letter abbreviations, in any case.
- Amounts may include thousands separators. `0` is a valid amount.
- Commas, semicolons or tabs are accepted as CSV delimiters.
- A month that already exists for that user/year is skipped, never overwritten.
- Rows that can't be imported are reported back with their row number and reason.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/health` | `200` when the API and database are up, `503` otherwise |
| `POST` | `/api/finances/upload/<user_id>/<year>` | Multipart upload, field name `file`. Returns `201` with `inserted`, `skipped`, `duplicates`, `rows_received`, `problems[]` |
| `GET`  | `/api/finances/<user_id>/<year>` | Records in calendar order: `[{name, month, amount}]` |

All errors are JSON: `{"error": "..."}` with a `400`, `404`, `413` or `500` status. An upload is one transaction, so a failure imports nothing. Limits: 10 MB, 5,000 rows.

```bash
curl -F "file=@postman_tests/test_data.csv" http://localhost:8080/api/finances/upload/1/2025
curl http://localhost:8080/api/finances/1/2025
```

## Tests

```bash
cd backend
python -m unittest discover -s . -p "test_*.py" -v      # needs MySQL for the integration test
```

- `test_parsing.py`: parsing and validation (no database needed)
- `test_app.py`: API behaviour and error responses
- `test_integration.py`: upload → fetch against a real database
- `postman_tests/`: API contract suite, run in CI with Newman

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request:
unit + integration tests, Newman contract tests, and a Docker Compose smoke test. A failing check fails the build.

## Project layout

```
backend/         Flask API, tests, Dockerfile, db_setup.sql
frontend/        Static dashboard (index.html, config.js), nginx config, Dockerfile
postman_tests/   Newman contract collection and fixtures
docker-compose.yml
ROADMAP.md       What's planned next
```
