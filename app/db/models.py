import uuid
import json 
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, Unicode 
# Import the Base class from our database setup
from app.db.database import Base

class JsonbString(TypeDecorator):
    impl = Unicode # Use a string type for implementation
    
    def process_bind_param(self, value, dialect):
        # Convert Python object (list/dict) to JSON string for database insertion
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        # Convert JSON string from database back to Python object
        if value is not None:
            return json.loads(value)
        return value
    
# --- Table Definitions (ORM Models) ---

class Hospital(Base):
    """Corresponds to the Hospitals table."""
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    address = Column(Text, nullable=False)
    contact_info = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    doctors = relationship("Doctor", back_populates="hospital")
    admins = relationship("HospitalAdmin", back_populates="hospital")
    records = relationship("MedicalRecord", back_populates="hospital")


class User(Base):
    """Corresponds to the Users table (Authentication and Roles)."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False) # 'Patient', 'Doctor', 'Hospital Admin'
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships (One-to-One profile links)
    patient_profile = relationship("PatientProfile", uselist=False, back_populates="user")
    doctor_profile = relationship("Doctor", uselist=False, back_populates="user")
    admin_profile = relationship("HospitalAdmin", uselist=False, back_populates="user")


class PatientProfile(Base):
    """Corresponds to the Patient_Profiles table."""
    __tablename__ = "patient_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(50))
    blood_type = Column(String(5))
    contact_number = Column(String(50))
    address = Column(Text)

    # Relationships
    user = relationship("User", back_populates="patient_profile")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    lab_tests = relationship("LabTest", back_populates="patient")
    treatments = relationship("TreatmentProcedure", back_populates="patient")
    health_reports = relationship("HealthReport", back_populates="patient")


class Doctor(Base):
    """Corresponds to the Doctors table."""
    __tablename__ = "doctors"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="RESTRICT"), nullable=False, index=True)
    specialty = Column(String(100), nullable=False)
    license_number = Column(String(100), unique=True, nullable=False)
    contact_number = Column(String(50))

    # Relationships
    user = relationship("User", back_populates="doctor_profile")
    hospital = relationship("Hospital", back_populates="doctors")
    created_records = relationship("MedicalRecord", back_populates="doctor")
    performed_treatments = relationship("TreatmentProcedure", back_populates="doctor")


class HospitalAdmin(Base):
    """Corresponds to the Hospital_Admins table."""
    __tablename__ = "hospital_admins"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="RESTRICT"), nullable=False)
    job_title = Column(String(100))

    # Relationships
    user = relationship("User", back_populates="admin_profile")
    hospital = relationship("Hospital", back_populates="admins")


class MedicalRecord(Base):
    """Corresponds to the Medical_Records table (Core visit data)."""
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="RESTRICT"), nullable=False)
    date_of_visit = Column(DateTime(timezone=True), default=func.now())
    chief_complaint = Column(Text)
    diagnosis = Column(Text, nullable=False)
    treatment_summary = Column(Text)
    medications = Column(JsonbString)
    notes = Column(Text)

    # Relationships
    patient = relationship("PatientProfile", back_populates="medical_records")
    doctor = relationship("Doctor", back_populates="created_records")
    hospital = relationship("Hospital", back_populates="records")
    lab_tests = relationship("LabTest", back_populates="medical_record")
    originating_treatments = relationship("TreatmentProcedure", back_populates="originating_record")


class LabTest(Base):
    """Corresponds to the Lab_Tests table (Detailed test results)."""
    __tablename__ = "lab_tests"

    id = Column(Integer, primary_key=True, index=True)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id", ondelete="CASCADE"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    test_name = Column(String(150), nullable=False)
    test_date = Column(Date, default=func.now())
    result_value = Column(String(255))
    units = Column(String(50))
    reference_range = Column(String(100))
    is_abnormal = Column(Boolean)
    test_data = Column(JSONB)
    performed_by_lab = Column(String(255))
    result_file_url = Column(Text)

    # Relationships
    patient = relationship("PatientProfile", back_populates="lab_tests")
    medical_record = relationship("MedicalRecord", back_populates="lab_tests")


class TreatmentProcedure(Base):
    """Corresponds to the Treatments_Procedures table (Detailed interventions)."""
    __tablename__ = "treatments_procedures"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.user_id", ondelete="SET NULL"))
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="RESTRICT"), nullable=False)
    procedure_name = Column(String(255), nullable=False)
    procedure_date = Column(DateTime(timezone=True), nullable=False)
    procedure_code = Column(String(50))
    outcome = Column(Text)
    complications = Column(Text)
    notes = Column(Text)
    originating_record_id = Column(Integer, ForeignKey("medical_records.id", ondelete="SET NULL"))

    # Relationships
    patient = relationship("PatientProfile", back_populates="treatments")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], back_populates="performed_treatments")
    originating_record = relationship("MedicalRecord", back_populates="originating_treatments")


class HealthReport(Base):
    """Corresponds to the Health_Reports table (Consolidated Analytical Reports)."""
    __tablename__ = "health_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)
    report_date = Column(Date, nullable=False)
    report_type = Column(String(100))
    vitals = Column(JSONB)
    summary = Column(Text)
    analytics_data = Column(JSONB)
    
    # A unique constraint is useful for analytical reports
    # __table_args__ = (UniqueConstraint('patient_id', 'report_date', 'report_type', name='uq_patient_report_date_type'),)

    # Relationships
    patient = relationship("PatientProfile", back_populates="health_reports")