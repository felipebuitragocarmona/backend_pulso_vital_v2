from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class EcgCreate(BaseModel):
    patientId: int
    registeredAt: str = Field(..., examples=["2026-06-28T00:01:00"])
    pdfUrl: str
    originalFilename: Optional[str] = None


class Ecg(BaseModel):
    id: int
    patientId: int
    registeredAt: str
    pdfUrl: str
    originalFilename: Optional[str] = None
    uploadedAt: str

    model_config = ConfigDict(from_attributes=True)


class EcgUploadResponse(BaseModel):
    ecg: Ecg
    extraction: Dict[str, Any]
