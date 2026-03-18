from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from config import UPLOAD_DIR
from routers import auth, users, restaurants, reviews, favorites, ai_assistant, history,yelp

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Yelp Prototype API",
    description="Restaurant Discovery & Review Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(yelp.router)
app.include_router(restaurants.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(history.router)
app.include_router(ai_assistant.router)

@app.on_event("startup")
def startup_ai_check():
    from services import ai_service
    if not ai_service.llm and ai_service.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            ai_service.llm = ChatGroq(
                model="llama-3.3-70b-versatile", temperature=0.7, api_key=ai_service.GROQ_API_KEY
            )
        except Exception:
            pass


@app.get("/")
def root():
    return {"message": "Yelp Prototype API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/db")
def health_check_db():
    try:
        from sqlalchemy import text
        from database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "message": str(e)}
