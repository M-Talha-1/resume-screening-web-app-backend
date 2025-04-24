from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.jobs import router as jobs_router
from app.routers.analytics import router as analytics_router
from app.routers.resume import router as resume_router
from app.database import engine, Base
from app.cache import init_cache
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
    title="Resume Web Backend",
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
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(resume_router)

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
