from fastapi import FastAPI
from app.routers import resume  
from app.routers import job
from app.routers import matching

app = FastAPI()

# Include the router
app.include_router(resume.router)
app.include_router(job.router)
app.include_router(matching.router)