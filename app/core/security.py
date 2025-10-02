from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Setup password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Password Hashing Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    
    # 1. Truncate the plain_password and encode it to bytes
    # We must pass the original string value of the plain password to pwd_context.verify, 
    # but we will rely on the underlying library to handle the truncation/encoding if possible.
    # If the hash stored in the DB is based on a truncated string, we must verify against the truncated string.
    
    # Re-apply the truncation logic that was used during hashing (which returns a string)
    truncated_password_str = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    
    # NOTE: The bcrypt handler usually prefers a string input for `verify`.
    return pwd_context.verify(truncated_password_str, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    
    # 1. Truncate the input password to 72 bytes and decode back to string
    # This is the string form saved to the DB, ensuring consistency.
    truncated_password_str = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    
    # 2. Pass the safely truncated string to be hashed
    # passlib/bcrypt will internally handle the final encoding for hashing.
    return pwd_context.hash(truncated_password_str)

# --- JWT Token Functions ---

def create_access_token(
    subject: str | Any, 
    role: str, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a signed JWT token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration time from config
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
