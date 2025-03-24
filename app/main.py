from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import resume  
from app.routers import job
from app.routers import matching

# Initialize FastAPI app first
app = FastAPI()

# Add CORS middleware after initializing the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers
app.include_router(resume.router)
app.include_router(job.router)
app.include_router(matching.router)
