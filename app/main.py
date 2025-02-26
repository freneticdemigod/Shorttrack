
from fastapi import FastAPI, Depends
from .routers import analytics
from sqlalchemy.orm import Session
from sqlalchemy import text
from .db import SessionLocal
from . import models
from .routers import shorten
from .routers import redirect

app = FastAPI()

app.include_router(shorten.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(redirect.router, prefix="/api")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the URL Shortener API"}


@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    
    result = db.execute(text("SELECT 1")).fetchone()
    return {"db_response": result[0] if result else None}

