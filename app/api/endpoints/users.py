import uuid
from typing import Optional, Union, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.crud import user as crud_user
from app.crud import record as crud_record
from app.schemas import user as schemas_user
from app.core.dependencies import AdminUser, AnyAuthenticatedUser, DoctorUser
from pydantic import BaseModel

class AdminAnalyticsResponse(BaseModel):
    total_patients: int
    total_records: int
    hospital_staff_count: int
    hospital_id: int

router = APIRouter(prefix="/users", tags=["User & Profiles"])

# --- Helper to get user profile by role ---
def get_user_profile(db: Session, user: models.User) -> Optional[Union[schemas_user.PatientProfile, schemas_user.Doctor, schemas_user.HospitalAdmin]]:
    """Fetches the specific profile associated with a user."""
    if user.role == "Patient":
        db_profile = db.query(models.PatientProfile).filter(models.PatientProfile.user_id == user.id).first()
        return schemas_user.PatientProfile.model_validate(db_profile)
    if user.role == "Doctor":
        db_profile = db.query(models.Doctor).filter(models.Doctor.user_id == user.id).first()
        return schemas_user.Doctor.model_validate(db_profile)
    if user.role == "Hospital Admin":
        db_profile = db.query(models.HospitalAdmin).filter(models.HospitalAdmin.user_id == user.id).first()
        return schemas_user.HospitalAdmin.model_validate(db_profile)
    return None

# --- Endpoint: Create Doctor/Admin (Admin Only) ---
@router.post("/", response_model=schemas_user.User, status_code=status.HTTP_201_CREATED)
def create_staff_user(
    user_in: schemas_user.UserCreate, 
    profile_in: Union[schemas_user.DoctorCreate, schemas_user.HospitalAdminCreate],
    current_admin: AdminUser, # Only Admins can create staff accounts
    db: Session = Depends(get_db)
):
    """
    Creates a new Doctor or Hospital Admin account. Restricted to existing Hospital Admins.
    """
    if user_in.role == "Patient":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use the /auth/register endpoint for patient sign-up.")

    db_user = crud_user.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
    # Security Check: Ensure admin creates accounts for their own hospital
    admin_details = db.query(models.HospitalAdmin).filter(models.HospitalAdmin.user_id == current_admin.id).first()
    if profile_in.hospital_id != admin_details.hospital_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create staff for another hospital.")

    new_user = crud_user.create_user(
        db=db, 
        user=user_in, 
        profile_data=profile_in.model_dump(exclude_unset=True)
    )
    return new_user

# --- Endpoint: Read Own Profile ---
@router.get("/me/profile", response_model=Union[schemas_user.PatientProfile, schemas_user.Doctor, schemas_user.HospitalAdmin])
def read_current_user_profile(
    current_user: AnyAuthenticatedUser, 
    db: Session = Depends(get_db)
):
    """Retrieves the profile details (PatientProfile, Doctor, or HospitalAdmin) for the current user."""
    profile = get_user_profile(db, current_user)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return profile

# --- Endpoint: Update Patient Profile (Self-Update) ---
@router.put("/me/profile/patient", response_model=schemas_user.PatientProfile)
def update_patient_profile(
    profile_in: schemas_user.PatientProfileCreate, # Can use Create schema for updates
    current_user: AnyAuthenticatedUser,
    db: Session = Depends(get_db)
):
    """Allows a Patient to update their own profile details."""
    if current_user.role != "Patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Patients can update this profile type.")
        
    db_profile = db.query(models.PatientProfile).filter(models.PatientProfile.user_id == current_user.id).first()
    if not db_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found.")

    update_data = profile_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)
        
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return db_profile

@router.get("/patients/search", response_model=List[schemas_user.PatientSearchResult])
def search_patients_endpoint(
    query: str,
    current_user: DoctorUser, # Only Doctors (and optionally Admins) should search
    db: Session = Depends(get_db)
):
    """
    Searches for patients by name or email (Doctor/Admin only).
    """
    if not query or len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters.")

    db_patients = crud_user.search_patients(db, query)
    
    results = []
    for p in db_patients:
        # Construct the full name from the profile data
        full_name = f"{p.first_name} {p.last_name}"
        
        # Manually create the desired output structure
        results.append(schemas_user.PatientSearchResult(
            user_id=p.user_id,
            full_name=full_name,
            date_of_birth=p.date_of_birth,
            contact_number=p.contact_number
        ))
        
    if not results:
        raise HTTPException(status_code=404, detail="No patients matched the search query.")
        
    return results

@router.get("/admin/analytics", response_model=AdminAnalyticsResponse)
def get_admin_analytics(
    current_admin: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Retrieves key operational analytics for the platform and the Admin's hospital.
    """
    # 1. Get Admin's Hospital ID
    admin_profile = db.query(models.HospitalAdmin).filter(models.HospitalAdmin.user_id == current_admin.id).first()
    if not admin_profile:
        raise HTTPException(status_code=404, detail="Admin profile not linked to a hospital.")
        
    hospital_id = admin_profile.hospital_id

    # 2. Gather metrics using CRUD functions
    total_patients = crud_user.count_all_patients(db)
    total_records = crud_record.count_all_medical_records(db) # We need to ensure this CRUD func exists
    hospital_staff = crud_user.count_hospital_doctors(db, hospital_id)

    return AdminAnalyticsResponse(
        total_patients=total_patients,
        total_records=total_records,
        hospital_staff_count=hospital_staff,
        hospital_id=hospital_id
    )
