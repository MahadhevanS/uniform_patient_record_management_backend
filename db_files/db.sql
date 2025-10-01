-- ----------------------------------------------------------------------
-- Database Creation Script: Uniform Patient Record Maintenance Platform (PostgreSQL)
--
-- This script creates 9 essential tables for the system, ensuring data
-- integrity and linking across different roles and records.
-- ----------------------------------------------------------------------

-- Ensure the 'uuid-ossp' or equivalent extension is available for gen_random_uuid()
-- If not available, you may need to run: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. HOSPITALS Table
------------------------------------------------------------------------
CREATE TABLE Hospitals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    contact_info VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. USERS Table (Authentication and Roles)
------------------------------------------------------------------------
CREATE TABLE Users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('Patient', 'Doctor', 'Hospital Admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookup by email
CREATE INDEX idx_user_email ON Users (email);

-- Trigger function to update 'updated_at' column automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to the Users table
CREATE TRIGGER update_user_updated_at
BEFORE UPDATE ON Users
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- 3. PATIENT_PROFILES Table (Patient Demographics)
------------------------------------------------------------------------
CREATE TABLE Patient_Profiles (
    user_id UUID PRIMARY KEY REFERENCES Users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(50),
    blood_type VARCHAR(5),
    contact_number VARCHAR(50),
    address TEXT
);

-- 4. DOCTORS Table (Professional Details)
------------------------------------------------------------------------
CREATE TABLE Doctors (
    user_id UUID PRIMARY KEY REFERENCES Users(id) ON DELETE CASCADE,
    hospital_id INTEGER REFERENCES Hospitals(id) ON DELETE RESTRICT,
    specialty VARCHAR(100) NOT NULL,
    license_number VARCHAR(100) NOT NULL UNIQUE,
    contact_number VARCHAR(50)
);

CREATE INDEX idx_doctor_hospital ON Doctors (hospital_id);

-- 5. HOSPITAL_ADMINS Table (Admin Affiliation)
------------------------------------------------------------------------
CREATE TABLE Hospital_Admins (
    user_id UUID PRIMARY KEY REFERENCES Users(id) ON DELETE CASCADE,
    hospital_id INTEGER REFERENCES Hospitals(id) ON DELETE RESTRICT,
    job_title VARCHAR(100)
);

-- 6. MEDICAL_RECORDS Table (Core Visit Data)
------------------------------------------------------------------------
CREATE TABLE Medical_Records (
    id BIGSERIAL PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES Patient_Profiles(user_id) ON DELETE RESTRICT,
    doctor_id UUID NOT NULL REFERENCES Doctors(user_id) ON DELETE RESTRICT,
    hospital_id INTEGER NOT NULL REFERENCES Hospitals(id) ON DELETE RESTRICT,
    date_of_visit TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    chief_complaint TEXT,
    diagnosis TEXT NOT NULL,
    treatment_summary TEXT, -- High-level plan/notes
    medications JSONB, -- JSON array of prescribed drugs
    notes TEXT
);

CREATE INDEX idx_record_patient ON Medical_Records (patient_id);
CREATE INDEX idx_record_doctor ON Medical_Records (doctor_id);

-- 7. LAB_TESTS Table (Detailed Test Results)
------------------------------------------------------------------------
CREATE TABLE Lab_Tests (
    id BIGSERIAL PRIMARY KEY,
    -- Links to the visit record that ordered the test
    medical_record_id BIGINT REFERENCES Medical_Records(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES Patient_Profiles(user_id) ON DELETE RESTRICT,
    test_name VARCHAR(150) NOT NULL,
    test_date DATE DEFAULT CURRENT_DATE,
    result_value VARCHAR(255),
    units VARCHAR(50),
    reference_range VARCHAR(100),
    is_abnormal BOOLEAN,
    test_data JSONB, -- For complex structured data or full raw results
    performed_by_lab VARCHAR(255),
    result_file_url TEXT
);

CREATE INDEX idx_labtest_patient ON Lab_Tests (patient_id);
CREATE INDEX idx_labtest_record ON Lab_Tests (medical_record_id);

-- 8. TREATMENTS_PROCEDURES Table (Detailed Interventions)
------------------------------------------------------------------------
CREATE TABLE Treatments_Procedures (
    id BIGSERIAL PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES Patient_Profiles(user_id) ON DELETE RESTRICT,
    doctor_id UUID REFERENCES Doctors(user_id) ON DELETE SET NULL,
    hospital_id INTEGER REFERENCES Hospitals(id) ON DELETE RESTRICT,
    procedure_name VARCHAR(255) NOT NULL,
    procedure_date TIMESTAMP WITH TIME ZONE NOT NULL,
    procedure_code VARCHAR(50),
    outcome TEXT,
    complications TEXT,
    notes TEXT,
    -- Links to the visit record that initiated the procedure
    originating_record_id BIGINT REFERENCES Medical_Records(id) ON DELETE SET NULL
);

CREATE INDEX idx_procedure_patient ON Treatments_Procedures (patient_id);

-- 9. HEALTH_REPORTS Table (Consolidated Analytical Reports)
------------------------------------------------------------------------
CREATE TABLE Health_Reports (
    id BIGSERIAL PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES Patient_Profiles(user_id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    report_type VARCHAR(100),
    vitals JSONB,
    summary TEXT,
    analytics_data JSONB,
    UNIQUE (patient_id, report_date, report_type)
);

CREATE INDEX idx_report_patient ON Health_Reports (patient_id);