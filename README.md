How to Run

**Prerequisites:** Python 3.10+, Node.js 18+, MySQL 8.0

**Backend (backend 2):**
```bash
cd "backend 2"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with DATABASE_URL, SECRET_KEY, GROQ_API_KEY, TAVILY_API_KEY, YELP_API_KEY
uvicorn main:app --reload --port 8000
```

**Frontend (frontend 2):**
```bash
cd "frontend 2"
npm install
npm start
```

**Database:**
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS yelp_db_partner;"
```
