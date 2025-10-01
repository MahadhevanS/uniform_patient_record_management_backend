import uuid
from sqlalchemy.orm import Session
from app.db import models
from app.schemas import record as schemas
from typing import List, Optional

# --- Medical Record CRUD ---

def create_medical_record(db: Session, record: schemas.MedicalRecordCreate, doctor_id: uuid.UUID, hospital_id: int) -> models.MedicalRecord:
    """Creates a new Medical Record entry."""
    record_data = record.model_dump(exclude_unset=True, exclude={'medications'})
    
    db_record = models.MedicalRecord(
        **record_data,
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        # Manually handle JSONB field conversion
        medications=[m.model_dump() for m in record.medications] if record.medications else None
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_record_by_id(db: Session, record_id: int) -> Optional[models.MedicalRecord]:
    """Retrieves a medical record by ID."""
    return db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()

def get_patient_records(db: Session, patient_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[models.MedicalRecord]:
    """Retrieves all medical records for a specific patient."""
    return db.query(models.MedicalRecord)\
             .filter(models.MedicalRecord.patient_id == patient_id)\
             .order_by(models.MedicalRecord.date_of_visit.desc())\
             .offset(skip).limit(limit).all()
            
def count_all_medical_records(db: Session) -> int:
    """Counts the total number of medical records across the platform."""
    return db.query(models.MedicalRecord).count()
# --- (Further CRUD functions for LabTest, TreatmentProcedure, HealthReport would follow here) ---