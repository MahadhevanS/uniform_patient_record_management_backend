import uuid
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

# --- Base User & Profile Schemas ---

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=8,max_length=128)
    role: str # Must be validated to 'Patient', 'Doctor', or 'Hospital Admin'
    
class User(UserBase):
    id: uuid.UUID
    role: str
    is_active: bool = True

    class Config:
        from_attributes = True

# --- Profile Schemas ---

class PatientProfileBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None

class PatientProfileCreate(PatientProfileBase):
    # Used when registering a patient
    pass

class PatientProfile(PatientProfileBase):
    user_id: uuid.UUID

    class Config:
        from_attributes = True

class PatientSearchResult(BaseModel):
    user_id: uuid.UUID
    full_name: str
    date_of_birth: Optional[date] = None
    contact_number: Optional[str] = None
    # Optionally, add last visit date if we calculate it later
    
    class Config:
        from_attributes = True

class DoctorBase(BaseModel):
    specialty: str
    license_number: str
    contact_number: Optional[str] = None

class DoctorCreate(DoctorBase):
    hospital_id: int

class Doctor(DoctorBase):
    user_id: uuid.UUID
    hospital_id: int

    class Config:
        from_attributes = True

class HospitalAdminBase(BaseModel):
    job_title: Optional[str] = None

class HospitalAdminCreate(HospitalAdminBase):
    hospital_id: int
    
class HospitalAdmin(HospitalAdminBase):
    user_id: uuid.UUID
    hospital_id: int

    class Config:
        from_attributes = True
        
# --- Authentication Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = None
    role: Optional[str] = None