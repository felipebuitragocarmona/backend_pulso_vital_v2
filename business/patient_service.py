from datetime import datetime
import math
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

from data.patient_repository import PatientRepository
from data.repository_factory import get_repositories
from models.dto.patient_dto import Patient, PatientCreate, PatientUpdate
from models.entity.patient_entity import PatientEntity


class PatientService:
    """Casos de uso de pacientes.

    Esta capa contiene reglas de negocio y puede ser llamada desde REST o MCP.
    La generación del id queda en la base de datos relacional.
    """

    def __init__(self, repo: Optional[PatientRepository] = None) -> None:
        self.repo = repo if repo is not None else get_repositories().patients

    def _to_dict(self, entity: PatientEntity) -> Dict[str, Any]:
        return {
            "id": entity.id,
            "fullName": entity.fullName,
            "birthDate": entity.birthDate,
            "createdAt": entity.createdAt,
            "updatedAt": entity.updatedAt,
        }

    def create_patient(self, patient: PatientCreate) -> Patient:
        now = datetime.now().isoformat()
        entity = PatientEntity(
            fullName=patient.fullName,
            birthDate=patient.birthDate,
            createdAt=now,
            updatedAt=None,
        )
        created = self.repo.save(self._to_dict(entity))
        return Patient(**created)

    def list_patients(self) -> List[Patient]:
        return [Patient(**patient) for patient in self.repo.find_all()]

    def list_patients_paged(self, page: int, page_size: int) -> Dict[str, Any]:
        items, total = self.repo.find_paged(page, page_size)
        return {
            "data": [Patient(**p) for p in items],
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": math.ceil(total / page_size) if page_size > 0 else 0,
        }

    def get_patient(self, patient_id: int) -> Optional[Patient]:
        patient = self.repo.find_by_id(int(patient_id))
        if not patient:
            return None
        return Patient(**patient)

    def update_patient(self, patient_id: int, update: PatientUpdate) -> Dict[str, Any] | Patient:
        data = update.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            return {"error": "No se enviaron campos para actualizar"}

        data["updatedAt"] = datetime.now().isoformat()
        updated = self.repo.update(int(patient_id), data)
        if not updated:
            return {"error": "Paciente no encontrado"}
        return Patient(**updated)

    def delete_patient(self, patient_id: int) -> Dict[str, Any]:
        patient_id = int(patient_id)
        ok = self.repo.delete_by_id(patient_id)
        if not ok:
            return {"error": "Paciente no encontrado"}

        patient_dir = Path("uploads") / "ecgs" / f"patient_{patient_id}"
        if patient_dir.exists() and patient_dir.is_dir():
            shutil.rmtree(patient_dir)

        return {"deleted": True, "patientId": patient_id}
