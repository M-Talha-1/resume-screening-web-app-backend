from fastapi import FastAPI
from app.routers import resume  
from app.routers import job
from app.routers import matching
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI()

# Include the router
app.include_router(resume.router)
app.include_router(job.router)
app.include_router(matching.router)