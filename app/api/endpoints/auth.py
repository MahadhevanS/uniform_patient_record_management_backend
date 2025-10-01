from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.crud import user as crud_user
from app.schemas import user as schemas_user
from app.core import dependencies
from app.core import security
from app.core.config import settings
from app.db import models

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas_user.User, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: schemas_user.UserCreate, 
    patient_profile_in: schemas_user.PatientProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new Patient user. Only Patient registration is public.
    Doctor and Admin accounts must be created by an existing Admin.
    """
    if user_in.role != "Patient":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Public registration is only allowed for the 'Patient' role."
        )

    # Check if user already exists
    db_user = crud_user.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Create the user and their profile
    new_user = crud_user.create_user(
        db=db, 
        user=user_in, 
        profile_data=patient_profile_in.model_dump(exclude_unset=True)
    )
    return new_user

@router.post("/login", response_model=schemas_user.Token)
def login_for_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Authenticate a user and return a JWT access token."""
    user = crud_user.get_user_by_email(db, email=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Create the token using the user's ID and Role
    access_token = security.create_access_token(
        subject=user.id,
        role=user.role,
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas_user.User)
def read_users_me(current_user: models.User = Depends(dependencies.get_current_user_and_role)):
    """Retrieve the current authenticated user's details."""
    return current_user