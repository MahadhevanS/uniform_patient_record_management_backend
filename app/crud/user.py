import uuid
from sqlalchemy.orm import Session
from app.db import models
from app.schemas import user as schemas
from app.core.security import get_password_hash
from typing import Optional 
from sqlalchemy import or_, func
from typing import List


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Finds a user by email."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    """Finds a user by UUID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate, profile_data: dict) -> models.User:
    """Creates a User and their corresponding profile (Patient, Doctor, or Admin)."""
    
    # 1. Hash password
    hashed_password = get_password_hash(user.password)
    
    # 2. Create User record
    db_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.flush() # Flushes to get the user_id before commit

    # 3. Create Profile record based on role
    profile_data['user_id'] = db_user.id
    
    if user.role == "Patient":
        db_profile = models.PatientProfile(**profile_data)
    elif user.role == "Doctor":
        db_profile = models.Doctor(**profile_data)
    elif user.role == "Hospital Admin":
        db_profile = models.HospitalAdmin(**profile_data)
    else:
        # This shouldn't happen if validation is correct, but for safety
        raise ValueError("Invalid user role.")
        
    db.add(db_profile)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def search_patients(db: Session, query: str) -> List[models.PatientProfile]:
    """
    Searches for Patient Profiles based on a query matching first name, last name, or email.
    """
    # Use ILIKE for case-insensitive partial matching (PostgreSQL specific)
    search_term = f"%{query}%"

    # 1. Search in Patient_Profiles table (first_name or last_name)
    profiles = db.query(models.PatientProfile) \
                 .filter(or_(
                     models.PatientProfile.first_name.ilike(search_term),
                     models.PatientProfile.last_name.ilike(search_term)
                 )).all()

    # 2. Search in Users table by email (if not found in profiles, or combine results)
    # For a simple solution, we'll combine the list of IDs to avoid duplicates if possible
    profile_user_ids = {p.user_id for p in profiles}

    users_by_email = db.query(models.User) \
                       .filter(models.User.role == "Patient") \
                       .filter(models.User.email.ilike(search_term)) \
                       .all()

    # Get profiles for users found by email but not yet included
    new_user_ids = [u.id for u in users_by_email if u.id not in profile_user_ids]
    
    if new_user_ids:
        new_profiles = db.query(models.PatientProfile) \
                         .filter(models.PatientProfile.user_id.in_(new_user_ids)) \
                         .all()
        profiles.extend(new_profiles)
        
    return profiles

def count_all_patients(db: Session) -> int:
    """Counts the total number of users with the 'Patient' role."""
    return db.query(models.User).filter(models.User.role == "Patient").count()


def count_all_medical_records(db: Session) -> int:
    """Counts the total number of medical records across the platform."""
    return db.query(models.MedicalRecord).count()


def count_hospital_doctors(db: Session, hospital_id: int) -> int:
    """Counts the total number of doctors affiliated with a specific hospital."""
    return db.query(models.Doctor).filter(models.Doctor.hospital_id == hospital_id).count()