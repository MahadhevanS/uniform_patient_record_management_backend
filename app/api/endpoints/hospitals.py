from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.crud import hospital as crud_hospital
from app.schemas import hospitals as schemas_hospital
from app.core.dependencies import AdminUser

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])

# --- Endpoint: Create New Hospital (Admin Only) ---
@router.post("/", response_model=schemas_hospital.Hospital, status_code=status.HTTP_201_CREATED)
def create_hospital(
    hospital_in: schemas_hospital.HospitalCreate,
    current_admin: AdminUser, # Requires 'Hospital Admin' role
    db: Session = Depends(get_db)
):
    """
    Creates a new hospital entity. Restricted to Hospital Admins.
    """
    # Note: For production, you might restrict this further to a *Super Admin* role.
    
    db_hospital = crud_hospital.create_hospital(db=db, hospital=hospital_in)
    return db_hospital

# --- Endpoint: Get All Hospitals (Admin/Doctor access for listing) ---
@router.get("/", response_model=List[schemas_hospital.Hospital])
def read_hospitals(
    current_user: AdminUser, # Requires 'Hospital Admin' for this broad query
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all hospitals.
    """
    hospitals = crud_hospital.get_hospitals(db, skip=skip, limit=limit)
    return hospitals

# --- Endpoint: Get Hospital by ID ---
@router.get("/{hospital_id}", response_model=schemas_hospital.Hospital)
def read_hospital(
    hospital_id: int, 
    current_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Retrieves a single hospital by ID.
    """
    db_hospital = crud_hospital.get_hospital(db, hospital_id=hospital_id)
    if db_hospital is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")
    return db_hospital

# --- Endpoint: Update Hospital Details (Admin Only, usually self-admin) ---
@router.put("/{hospital_id}", response_model=schemas_hospital.Hospital)
def update_hospital(
    hospital_id: int,
    hospital_in: schemas_hospital.HospitalUpdate,
    current_admin: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Updates details for a specific hospital. Restricted to Hospital Admins.
    """
    db_hospital = crud_hospital.get_hospital(db, hospital_id=hospital_id)
    if db_hospital is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")
        
    # Optional Security: Ensure the admin only modifies their own hospital
    admin_details = db.query(models.HospitalAdmin).filter(models.HospitalAdmin.user_id == current_admin.id).first()
    if admin_details.hospital_id != hospital_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another hospital's data.")

    db_hospital = crud_hospital.update_hospital(db, db_hospital, hospital_in)
    return db_hospital