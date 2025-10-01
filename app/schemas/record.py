import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, date

# --- Medication JSON Structure ---
class Medication(BaseModel):
    name: str
    dosage: str
    frequency: Optional[str] = None

# --- Medical Record Schemas (Visit) ---
class MedicalRecordBase(BaseModel):
    chief_complaint: Optional[str] = None
    diagnosis: str
    treatment_summary: Optional[str] = None
    medications: Optional[List[Medication]] = None
    notes: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    # Required for creation
    patient_id: uuid.UUID
    # doctor_id and hospital_id will be derived from the logged-in user

class MedicalRecord(MedicalRecordBase):
    id: int
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    hospital_id: int
    date_of_visit: datetime

    class Config:
        from_attributes = True

# --- Lab Test Schemas ---
class LabTestBase(BaseModel):
    test_name: str
    result_value: Optional[str] = None
    units: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: Optional[bool] = None
    test_data: Optional[dict[str, Any]] = None # JSONB field
    performed_by_lab: Optional[str] = None
    result_file_url: Optional[str] = None

class LabTestCreate(LabTestBase):
    # Link to the record that ordered it
    medical_record_id: Optional[int] = None
    patient_id: uuid.UUID
    
class LabTest(LabTestBase):
    id: int
    medical_record_id: Optional[int] = None
    patient_id: uuid.UUID
    test_date: date

    class Config:
        from_attributes = True

# --- Treatment/Procedure Schemas ---
class TreatmentProcedureBase(BaseModel):
    procedure_name: str
    procedure_date: datetime
    procedure_code: Optional[str] = None
    outcome: Optional[str] = None
    complications: Optional[str] = None
    notes: Optional[str] = None

class TreatmentProcedureCreate(TreatmentProcedureBase):
    patient_id: uuid.UUID
    originating_record_id: Optional[int] = None
    # doctor_id and hospital_id will be derived from the logged-in user

class TreatmentProcedure(TreatmentProcedureBase):
    id: int
    patient_id: uuid.UUID
    doctor_id: Optional[uuid.UUID] = None
    hospital_id: int
    originating_record_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Health Report Schemas ---
class HealthReportBase(BaseModel):
    report_date: date
    report_type: Optional[str] = None
    vitals: Optional[dict[str, Any]] = None # JSONB field
    summary: Optional[str] = None
    analytics_data: Optional[dict[str, Any]] = None # JSONB field

class HealthReportCreate(HealthReportBase):
    patient_id: uuid.UUID

class HealthReport(HealthReportBase):
    id: int
    patient_id: uuid.UUID

    class Config:
        from_attributes = True