from pydantic import BaseModel, Field
from typing import Optional

# Base Schema
class HospitalBase(BaseModel):
    name: str = Field(min_length=3)
    address: str
    contact_info: Optional[str] = None

# Schema for creating a new Hospital (Request body)
class HospitalCreate(HospitalBase):
    pass

# Schema for updating a Hospital
class HospitalUpdate(HospitalBase):
    is_active: Optional[bool] = None

# Schema for returning a Hospital (Response body)
class Hospital(HospitalBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True # Allows mapping from SQLAlchemy ORM models