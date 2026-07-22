from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from business.ecg_service import EcgService
from data.repository_factory import get_repositories
from models.dto.ecg_dto import Ecg, EcgUploadResponse

router = APIRouter(tags=["ecgs"])

repositories = get_repositories()
ecg_service = EcgService(
    ecg_repo=repositories.ecgs,
    patient_repo=repositories.patients,
)


@router.post("/patients/{patient_id}/ecgs/upload", response_model=EcgUploadResponse)
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


@router.get("/patients/{patient_id}/ecgs", response_model=Dict[str, Any])
def list_patient_ecgs(
    patient_id: int,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
):
    result = ecg_service.list_patient_ecgs_paged(patient_id, page, pageSize)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/ecgs/{ecg_id}", response_model=Ecg)
def get_ecg(ecg_id: int):
    ecg = ecg_service.get_ecg(ecg_id)
    if not ecg:
        raise HTTPException(status_code=404, detail="ECG no encontrado")
    return ecg


@router.delete("/ecgs/{ecg_id}")
def delete_ecg(ecg_id: int):
    result = ecg_service.delete_ecg(ecg_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
