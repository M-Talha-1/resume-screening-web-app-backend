from setuptools import setup, find_packages

setup(
    name="resume_web_backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "python-dotenv",
        "pydantic",
        "httpx",
        "pytest",
        "pytest-asyncio",
        "aiosqlite"
    ],
) 