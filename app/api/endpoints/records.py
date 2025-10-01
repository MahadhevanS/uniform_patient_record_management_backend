# app/api/endpoints/records.py (FINAL CORRECT VERSION)

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.crud import record as crud_record
from app.schemas import record as schemas_record
from app.core.dependencies import DoctorUser, PatientUser, AnyAuthenticatedUser

router = APIRouter(prefix="/records", tags=["Patient Records"])

# --- Endpoint 1: Create New Medical Record (POST is not affected by GET ordering) ---
@router.post("/", response_model=schemas_record.MedicalRecord, status_code=status.HTTP_201_CREATED)
def create_record(
    record_in: schemas_record.MedicalRecordCreate,
    current_doctor: DoctorUser,
    db: Session = Depends(get_db)
):
    """Creates a new medical record for a patient. Requires Doctor role."""
    if not db.query(models.PatientProfile).filter(models.PatientProfile.user_id == record_in.patient_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        
    doctor_details = db.query(models.Doctor).filter(models.Doctor.user_id == current_doctor.id).first()
    
    db_record = crud_record.create_medical_record(
        db=db,
        record=record_in,
        doctor_id=current_doctor.id,
        hospital_id=doctor_details.hospital_id
    )
    return db_record

# ----------------------------------------------------------------------------------
# 🚨 CRITICAL FIX: The two GET routes MUST be in this order 🚨
# ----------------------------------------------------------------------------------

# --- Endpoint 2 (FIRST GET): Get Single Medical Record Detail (INTEGER ID) ---
@router.get("/{record_id:int}", response_model=schemas_record.MedicalRecord)
def read_record_detail(
    record_id: int, 
    current_user: AnyAuthenticatedUser,
    db: Session = Depends(get_db)
):
    """Retrieves a single medical record by its integer ID."""
    db_record = crud_record.get_record_by_id(db, record_id=record_id)

    if not db_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical Record not found.")
        
    # Security Check
    if current_user.role == "Patient" and current_user.id != db_record.patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    
    return db_record

# --- Endpoint 3 (SECOND GET): Get Patient Records List (UUID ID) ---
@router.get("/{patient_id:uuid}", response_model=List[schemas_record.MedicalRecord])
def read_patient_records(
    patient_id: uuid.UUID, # Handles UUIDs like '51ac1ab0-...'
    current_user: AnyAuthenticatedUser,
    db: Session = Depends(get_db)
):
    """Retrieves all medical records for a specific patient (UUID)."""
    
    # 1. Role-based access control check
    if current_user.role == "Patient" and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Patients can only view their own records."
        )
    
    # 2. Check if the target patient profile exists
    if not db.query(models.PatientProfile).filter(models.PatientProfile.user_id == patient_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")
        
    # 3. Retrieve records
    db_records = crud_record.get_patient_records(db, patient_id=patient_id)
    return db_records

