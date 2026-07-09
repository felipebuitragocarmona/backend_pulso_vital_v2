from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    fullName: str = Field(..., min_length=2, examples=["Felipe Buitrago"])
    birthDate: str = Field(..., examples=["1990-05-20"])


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    fullName: Optional[str] = Field(default=None, min_length=2)
    birthDate: Optional[str] = None


class Patient(PatientBase):
    id: int
    createdAt: str
    updatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
