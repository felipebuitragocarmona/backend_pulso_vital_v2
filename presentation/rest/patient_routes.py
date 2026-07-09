from typing import List

from fastapi import APIRouter, HTTPException

from business.patient_service import PatientService
from data.repository_factory import get_repositories
from models.dto.patient_dto import Patient, PatientCreate, PatientUpdate

router = APIRouter(tags=["patients"])

repositories = get_repositories()
patient_service = PatientService(repo=repositories.patients)


@router.post("/patients", response_model=Patient)
def create_patient(data: PatientCreate):
    return patient_service.create_patient(data)


@router.get("/patients", response_model=List[Patient])
def list_patients():
    return patient_service.list_patients()


@router.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: int):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return patient


@router.put("/patients/{patient_id}", response_model=Patient)
def update_patient(patient_id: int, data: PatientUpdate):
    result = patient_service.update_patient(patient_id, data)
    if isinstance(result, dict) and result.get("error"):
        status_code = 404 if result["error"] == "Paciente no encontrado" else 400
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: int):
    result = patient_service.delete_patient(patient_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
