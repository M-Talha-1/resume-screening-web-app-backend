from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to Resume Screening API!"}

@app.get("/test_db")
def test_db(db: Session = Depends(get_db)):
    return {"message": "Database connection successful!"}
