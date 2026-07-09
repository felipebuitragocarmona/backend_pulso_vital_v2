from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from business.ecg_service import EcgService
from business.patient_service import PatientService
from data.repository_factory import get_repositories
from models.dto.ecg_dto import Ecg, EcgUploadResponse
from models.dto.patient_dto import Patient, PatientCreate, PatientUpdate

router = APIRouter()

# Los repositorios concretos comparten la misma conexión relacional.
repositories = get_repositories()
patient_service = PatientService(repo=repositories.patients)
ecg_service = EcgService(
    ecg_repo=repositories.ecgs,
    patient_repo=repositories.patients,
)


@router.post("/patients", response_model=Patient, tags=["patients"])
def create_patient(data: PatientCreate):
    return patient_service.create_patient(data)


@router.get("/patients", response_model=List[Patient], tags=["patients"])
def list_patients():
    return patient_service.list_patients()


@router.get("/patients/{patient_id}", response_model=Patient, tags=["patients"])
def get_patient(patient_id: int):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return patient


@router.put("/patients/{patient_id}", response_model=Patient, tags=["patients"])
def update_patient(patient_id: int, data: PatientUpdate):
    result = patient_service.update_patient(patient_id, data)
    if isinstance(result, dict) and result.get("error"):
        status_code = 404 if result["error"] == "Paciente no encontrado" else 400
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.delete("/patients/{patient_id}", tags=["patients"])
def delete_patient(patient_id: int):
    result = patient_service.delete_patient(patient_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/patients/{patient_id}/ecgs/upload", response_model=EcgUploadResponse, tags=["ecgs"])
async def upload_patient_ecg(
    patient_id: int,
    file: UploadFile = File(...),
    registeredAt: str | None = Form(default=None),
):
    pdf_bytes = await file.read()
    result = ecg_service.upload_ecg_pdf_bytes(
        patient_id=patient_id,
        pdf_bytes=pdf_bytes,
        filename=file.filename or "ecg.pdf",
        registeredAt=registeredAt,
    )
    if isinstance(result, dict) and result.get("error"):
        status_code = 404 if result["error"] == "Paciente no encontrado" else 400
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.get("/patients/{patient_id}/ecgs", response_model=List[Ecg], tags=["ecgs"])
def list_patient_ecgs(patient_id: int):
    result = ecg_service.list_patient_ecgs(patient_id)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/ecgs/{ecg_id}", response_model=Ecg, tags=["ecgs"])
def get_ecg(ecg_id: int):
    ecg = ecg_service.get_ecg(ecg_id)
    if not ecg:
        raise HTTPException(status_code=404, detail="ECG no encontrado")
    return ecg


@router.delete("/ecgs/{ecg_id}", tags=["ecgs"])
def delete_ecg(ecg_id: int):
    result = ecg_service.delete_ecg(ecg_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
