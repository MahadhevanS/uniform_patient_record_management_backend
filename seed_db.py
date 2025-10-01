import os
import sys
import uuid
import random
import json
from datetime import datetime, timedelta, date
from faker import Faker
from sqlalchemy.orm import Session

# --- Configuration and Database Setup ---
# Add the project directory to the path to allow imports from 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.db.database import SessionLocal, engine, Base
from app.db import models
from app.core.security import get_password_hash

# ----------------------------------------------------------------------
# GLOBAL SETUP
# ----------------------------------------------------------------------
# Initialize Faker
fake = Faker()

# List of valid specialties and blood types
SPECIALTIES = ["Cardiology", "Neurology", "Pediatrics", "Oncology", "Orthopedics", "General Practice"]
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
ROLES = ["Doctor", "Hospital Admin", "Patient"]
NUM_HOSPITALS = 3
NUM_ADMINS = 3
NUM_DOCTORS = 15
NUM_PATIENTS = 50
RECORDS_PER_PATIENT = 5

# Hardcoded test credentials (for easy manual API testing)
TEST_PASS = "testpass" 
TEST_PASSWORD_HASH = get_password_hash(TEST_PASS) # Hash the test password once

# ----------------------------------------------------------------------
# CORE GENERATOR FUNCTIONS
# ----------------------------------------------------------------------

def create_user_and_profile(db: Session, hospital_id: int, role: str) -> models.User:
    """Creates a User and associated profile (Doctor, Admin, or Patient)."""
    
    user_id = uuid.uuid4()
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@{fake.domain_name()}"
    
    # 1. Create User
    db_user = models.User(
        id=user_id,
        email=email,
        password_hash=TEST_PASSWORD_HASH,
        role=role
    )
    db.add(db_user)
    db.flush()
    
    # 2. Create Profile
    if role == "Doctor":
        db_profile = models.Doctor(
            user_id=user_id,
            hospital_id=hospital_id,
            specialty=random.choice(SPECIALTIES),
            license_number=f"LIC-{fake.unique.random_number(digits=6)}",
            contact_number=fake.phone_number()
        )
    elif role == "Hospital Admin":
        db_profile = models.HospitalAdmin(
            user_id=user_id,
            hospital_id=hospital_id,
            job_title=random.choice(["Manager", "Director", "IT Head"])
        )
    elif role == "Patient":
        db_profile = models.PatientProfile(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
            gender=random.choice(["Male", "Female", "Other"]),
            blood_type=random.choice(BLOOD_TYPES),
            contact_number=fake.phone_number(),
            address=fake.address()
        )
    
    db.add(db_profile)
    db.flush()
    
    return db_user

def create_medical_record(db: Session, patient: models.PatientProfile, doctor: models.Doctor):
    """Creates a full set of medical history for one visit."""
    
    # Date in the last two years
    start_date = datetime.now() - timedelta(days=730)
    end_date = datetime.now()

    visit_date = fake.date_time_between(
        start_date=start_date, 
        end_date=end_date, 
        tzinfo=None
    )
    # 1. Medical Record
    db_record = models.MedicalRecord(
        patient_id=patient.user_id,
        doctor_id=doctor.user_id,
        hospital_id=doctor.hospital_id,
        date_of_visit=visit_date,
        chief_complaint=fake.sentence(nb_words=6),
        diagnosis=fake.sentence(nb_words=4),
        treatment_summary=fake.paragraph(nb_sentences=2),
        medications=json.dumps([
            {"name": fake.word().capitalize(), "dosage": f"{random.randint(10, 500)}mg", "frequency": random.choice(["Daily", "Twice Daily"])},
            {"name": fake.word().capitalize(), "dosage": f"{random.randint(1, 5)}ml", "frequency": "As Needed"}
        ]),
        notes=fake.text(max_nb_chars=200)
    )
    db.add(db_record)
    db.flush() # Need ID for linkage

    # 2. Lab Test (Link to record)
    db_test = models.LabTest(
        medical_record_id=db_record.id,
        patient_id=patient.user_id,
        test_name=random.choice(["CBC", "CMP", "Lipid Panel", "Glucose"]),
        test_date=visit_date.date(),
        result_value=f"{random.randint(50, 200)}",
        units=random.choice(["mg/dL", "k/uL", "%"]),
        reference_range="Normal",
        is_abnormal=fake.boolean(chance_of_getting_true=20),
        performed_by_lab=fake.company()
    )
    db.add(db_test)
    
    # 3. Treatment/Procedure (Random chance)
    if fake.boolean(chance_of_getting_true=30):
        db_procedure = models.TreatmentProcedure(
            patient_id=patient.user_id,
            doctor_id=doctor.user_id,
            hospital_id=doctor.hospital_id,
            procedure_name=random.choice(["Minor Sutures", "Flu Vaccine", "Casting"]),
            procedure_date=visit_date + timedelta(hours=random.randint(1, 24)),
            outcome=fake.sentence(nb_words=4),
            originating_record_id=db_record.id
        )
        db.add(db_procedure)

def create_health_report(db: Session, patient: models.PatientProfile):
    """Creates one comprehensive health report for a patient."""
    
    db_report = models.HealthReport(
        patient_id=patient.user_id,
        report_date=fake.date_this_year(),
        report_type=random.choice(["Annual Physical", "Specialty Review"]),
        vitals=json.dumps({
            "BP": f"{random.randint(110, 160)}/{random.randint(70, 100)}",
            "HR": random.randint(60, 100),
            "Temp": round(random.uniform(97.5, 99.5), 1)
        }),
        summary=fake.paragraph(nb_sentences=3),
        analytics_data=json.dumps({"bmi": round(random.uniform(18.5, 35.0), 1), "risk_level": random.choice(["Low", "Medium", "High"])}),
    )
    db.add(db_report)
    
# ----------------------------------------------------------------------
# MAIN EXECUTION
# ----------------------------------------------------------------------

def seed_database():
    """Main function to orchestrate the data generation and insertion."""
    print("Starting database seeding...")
    
    # 1. Clear existing data to ensure fresh start (Optional but recommended)
    # Be extremely careful with this step in a production environment!
    # Base.metadata.drop_all(bind=engine)
    # Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Check if users already exist to prevent duplicate runs
        if db.query(models.User).count() > 5:
            print("Database already contains sufficient user data. Skipping seed.")
            return

        hospitals = []
        doctors = []
        patients = []
        
        # A. Create Hospitals
        print(f"Creating {NUM_HOSPITALS} Hospitals...")
        for i in range(NUM_HOSPITALS):
            h = models.Hospital(
                name=f"{fake.city()} {random.choice(['General', 'Regional', 'St. Jude'])} Hospital",
                address=fake.address(),
                contact_info=fake.phone_number()
            )
            db.add(h)
            db.flush()
            hospitals.append(h)
        
        # B. Create Admins and Doctors
        print(f"Creating {NUM_ADMINS} Admins and {NUM_DOCTORS} Doctors...")
        for i in range(NUM_ADMINS):
            hospital_id = hospitals[i % NUM_HOSPITALS].id
            create_user_and_profile(db, hospital_id, "Hospital Admin")
            
        for _ in range(NUM_DOCTORS):
            hospital_id = random.choice(hospitals).id
            user = create_user_and_profile(db, hospital_id, "Doctor")
            doctors.append(db.query(models.Doctor).filter(models.Doctor.user_id == user.id).first())
            
        # C. Create Patients
        print(f"Creating {NUM_PATIENTS} Patients...")
        for _ in range(NUM_PATIENTS):
            user = create_user_and_profile(db, 1, "Patient") # Patients don't need a specific hospital link initially
            patients.append(db.query(models.PatientProfile).filter(models.PatientProfile.user_id == user.id).first())

        # D. Create Medical History, Tests, and Reports
        print("Creating Medical Records, Tests, and Reports...")
        for patient in patients:
            # Create several records per patient
            for _ in range(random.randint(1, RECORDS_PER_PATIENT)):
                doctor = random.choice(doctors)
                create_medical_record(db, patient, doctor)
            
            # Create one health report for the patient
            create_health_report(db, patient)
            
        db.commit()
        
        print("\n=============================================")
        print("✅ Seeding complete!")
        print(f"Total Users Created: {NUM_ADMINS + NUM_DOCTORS + NUM_PATIENTS}")
        print(f"Test Password for all: '{TEST_PASS}'")
        print("=============================================")
        
    except Exception as e:
        db.rollback()
        print(f"An error occurred during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()