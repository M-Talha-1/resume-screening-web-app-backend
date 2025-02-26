from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:root123@localhost:5432/resume_screening_db")

try:
    with engine.connect() as connection:
        print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
