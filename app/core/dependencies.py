import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.user import TokenData
from app.db.database import get_db
from app.db import models

# OAuth2 scheme for the 'Authorization: Bearer <token>' header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# --- Utility Function to Get Current User and Role ---
def get_current_user_and_role(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    """Decodes JWT, finds the user in the database, and returns the User object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        user_role: str = payload.get("role")
        
        if user_id_str is None or user_role is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=uuid.UUID(user_id_str), role=user_role)
    except JWTError:
        raise credentials_exception

    # Fetch user from DB using the ID
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    
    if user is None:
        raise credentials_exception
    
    return user

# --- RBAC Dependencies ---

def require_role(allowed_roles: list[str]):
    """
    A factory function to create a dependency for checking user roles.
    Example: Depends(require_role(["Doctor", "Hospital Admin"]))
    """
    def role_checker(current_user: Annotated[models.User, Depends(get_current_user_and_role)]):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not authorized for this action."
            )
        return current_user
    return role_checker

# Predefined common role dependencies
# NOTE: Patient is currently named 'User' in the requirement, so we include both.
# We will use 'Patient' for clarity in the rest of the code.

DoctorUser = Annotated[models.User, Depends(require_role(["Doctor"]))]
AdminUser = Annotated[models.User, Depends(require_role(["Hospital Admin"]))]
PatientUser = Annotated[models.User, Depends(require_role(["Patient"]))]
AnyAuthenticatedUser = Annotated[models.User, Depends(get_current_user_and_role)]