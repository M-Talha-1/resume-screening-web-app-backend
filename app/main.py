from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.routers import screening
from app.routers.auth import router as auth_router
from app.routers.jobs import router as jobs_router
from app.routers.analytics import router as analytics_router
from app.routers.resume import router as resume_router
from app.routers.matching import router as matching_router
from app.database import engine, Base, get_db, test_connection
from app.cache import init_cache
import logging
from typing import Dict
import time
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Initialize rate limiter
@app.on_event("startup")
async def startup():
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_client)

# Include routers
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(resume_router)
app.include_router(matching_router)
app.include_router(screening.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Resume Web Backend API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict:
    """
    Health check endpoint that verifies database connectivity
    """
    try:
        start_time = time.time()
        db_status = test_connection()
        end_time = time.time()
        
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "response_time": f"{(end_time - start_time):.3f}s"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable"
        )

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    # Test database connection
    if not test_connection():
        logger.error("Failed to connect to database on startup")
        raise Exception("Database connection failed")
    logger.info("Database connection successful")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    # Close database connections
    engine.dispose()
    logger.info("Database connections closed")
