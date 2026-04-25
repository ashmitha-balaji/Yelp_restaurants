# Lab Partner Setup Guide (backend 2 + frontend 2)

## Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0+ (running)

---

## Step 1: Create MySQL Database

If MySQL is running, create the database:

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS yelp_db_partner;"
```

The `.env` uses `mysql+pymysql://root@localhost:3306/yelp_db_partner` (no password). If your MySQL root has a password, edit `backend 2/.env`:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/yelp_db_partner
```

---

## Step 2: Backend (backend 2)

```bash
cd "backend 2"
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at http://localhost:8000. API docs: http://localhost:8000/docs

The `.env` file is already configured with your partner's API keys.

---

## Step 3: Frontend (frontend 2)

Open a **new terminal** (keep backend running):

```bash
cd "frontend 2"
npm install
npm start
```

Frontend opens at http://localhost:3000

---

## Quick Reference

| Component | Directory | Command | URL |
|-----------|-----------|---------|-----|
| Backend | `backend 2` | `uvicorn main:app --reload --port 8000` | http://localhost:8000 |
| Frontend | `frontend 2` | `npm start` | http://localhost:3000 |

---

## Troubleshooting

- **MySQL not running:** Start MySQL (`brew services start mysql` on macOS)
- **Database connection error:** Check `DATABASE_URL` in `backend 2/.env`
- **Port 8000 in use:** Use `--port 8001` and update frontend `REACT_APP_API_URL` if needed
