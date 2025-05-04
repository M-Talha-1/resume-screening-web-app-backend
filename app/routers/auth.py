from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import re
import logging
import bcrypt
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.database import get_db
from app.models import User
from app.schemas import TokenData, Token, UserCreate, UserResponse, UserTokenData

# Load environment variables
load_dotenv()

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Rate limiting configuration
MAX_LOGIN_ATTEMPTS = 5
LOGIN_TIMEOUT_MINUTES = 15
failed_attempts = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error hashing password"
        )

def validate_password(password: str) -> bool:
    """Validate password complexity"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Authentication failed: User not found - {email}")
            return None
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password - {email}")
            return None
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token"""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current user from the token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token validation failed: No email in payload")
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        logger.error(f"Token validation error: {str(e)}")
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        logger.warning(f"Token validation failed: User not found - {token_data.email}")
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register_user(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        # Validate password complexity
        if not validate_password(user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long and contain uppercase, lowercase, and number"
            )

        # Check if user already exists
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            name=user.name,
            hashed_password=hashed_password,
            role=user.role,
            is_active=True
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User registered successfully: {user.email}")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    try:
        logger.info(f"Login attempt for user: {form_data.username}")
        
        # Check rate limiting first
        current_time = time.time()
        if form_data.username in failed_attempts:
            last_attempt_time, attempts = failed_attempts[form_data.username]
            if attempts >= MAX_LOGIN_ATTEMPTS:
                if current_time - last_attempt_time < LOGIN_TIMEOUT_MINUTES * 60:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many failed login attempts. Please try again later."
                    )
                else:
                    # Reset attempts if timeout has passed
                    failed_attempts[form_data.username] = (current_time, 0)
        
        # Authenticate user
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            # Update failed attempts
            if form_data.username in failed_attempts:
                last_time, attempts = failed_attempts[form_data.username]
                failed_attempts[form_data.username] = (current_time, attempts + 1)
            else:
                failed_attempts[form_data.username] = (current_time, 1)
            
            logger.warning(f"Login failed for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        # Reset failed attempts on successful login
        if form_data.username in failed_attempts:
            del failed_attempts[form_data.username]

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        # Create user token data
        user_token_data = UserTokenData(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_token_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/deactivate")
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate the current user's account"""
    try:
        current_user.is_active = False
        db.commit()
        logger.info(f"Account deactivated: {current_user.email}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Account deactivated successfully"}
        )
    except Exception as e:
        logger.error(f"Error deactivating account: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating account"
        ) 