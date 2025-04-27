from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.routers import screening
from app.routers.auth import router as auth_router
from app.routers.jobs import router as jobs_router
from app.routers.analytics import router as analytics_router
from app.routers.resume import router as resume_router
from app.database import engine, Base, get_db
from app.cache import init_cache
from app.models import User
from app.auth import authenticate_user, create_access_token
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables
logger.info("Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")
    raise

# Initialize cache
init_cache()

app = FastAPI(
    title="Resume Screening API",
    description="Backend API for Resume Web Application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(screening.router)
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(resume_router)

# Token endpoint
@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Resume Web Backend API",
        "version": "1.0.0",
        "status": "running"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    # Initialize any resources here
    pass

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    # Clean up resources here
    pass
