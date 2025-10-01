from sqlalchemy.orm import Session
from app.db import models
from app.schemas import hospitals as schemas
from typing import List, Optional

def create_hospital(db: Session, hospital: schemas.HospitalCreate) -> models.Hospital:
    """Creates a new Hospital entry."""
    db_hospital = models.Hospital(**hospital.model_dump())
    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)
    return db_hospital

def get_hospital(db: Session, hospital_id: int) -> Optional[models.Hospital]:
    """Retrieves a hospital by ID."""
    return db.query(models.Hospital).filter(models.Hospital.id == hospital_id).first()

def get_hospitals(db: Session, skip: int = 0, limit: int = 100) -> List[models.Hospital]:
    """Retrieves a list of hospitals."""
    return db.query(models.Hospital).offset(skip).limit(limit).all()

def update_hospital(db: Session, db_hospital: models.Hospital, hospital_in: schemas.HospitalUpdate) -> models.Hospital:
    """Updates an existing Hospital record."""
    update_data = hospital_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_hospital, key, value)
        
    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)
    return db_hospital