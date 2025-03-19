from fastapi import FastAPI
from app.routers import resume  

app = FastAPI()

# Include the router
app.include_router(resume.router)
