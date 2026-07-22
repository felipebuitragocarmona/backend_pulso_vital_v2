from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import math
from uuid import uuid4

from business.extraction.ecg_extraction_service import EcgExtractionService
from data.ecg_repository import EcgRepository
from data.patient_repository import PatientRepository
from data.repository_factory import get_repositories
from models.dto.ecg_dto import Ecg
from models.entity.ecg_entity import EcgEntity


class EcgService:
    """Casos de uso de archivos ECG asociados a pacientes."""

    def __init__(
        self,
        ecg_repo: Optional[EcgRepository] = None,
        patient_repo: Optional[PatientRepository] = None,
        ecg_extraction_service: Optional[EcgExtractionService] = None,
    ) -> None:
        repositories = get_repositories() if ecg_repo is None or patient_repo is None else None
        self.ecg_repo = ecg_repo if ecg_repo is not None else repositories.ecgs
        self.patient_repo = patient_repo if patient_repo is not None else repositories.patients
        self.ecg_extraction_service = (
            ecg_extraction_service
            if ecg_extraction_service is not None
            else EcgExtractionService()
        )

    def _to_dict(self, entity: EcgEntity) -> Dict[str, Any]:
        return {
            "id": entity.id,
            "patientId": entity.patientId,
            "registeredAt": entity.registeredAt,
            "pdfUrl": entity.pdfUrl,
            "originalFilename": entity.originalFilename,
            "uploadedAt": entity.uploadedAt,
        }

    def _to_json_compatible(self, value: Any) -> Any:
        """Convierte tipos externos como NumPy/Pandas a tipos nativos serializables."""
        if isinstance(value, dict):
            return {str(key): self._to_json_compatible(item) for key, item in value.items()}

        if isinstance(value, list):
            return [self._to_json_compatible(item) for item in value]

        if isinstance(value, tuple):
            return [self._to_json_compatible(item) for item in value]

        if hasattr(value, "item") and callable(getattr(value, "item")):
            try:
                return self._to_json_compatible(value.item())
            except Exception:
                pass

        if hasattr(value, "tolist") and callable(getattr(value, "tolist")):
            try:
                return self._to_json_compatible(value.tolist())
            except Exception:
                pass

        return value

    def upload_ecg_pdf_bytes(
        self,
        patient_id: int,
        pdf_bytes: bytes,
        filename: str,
        registeredAt: Optional[str] = None,
    ) -> Union[Dict[str, Any], Ecg]:
        patient_id = int(patient_id)

        patient = self.patient_repo.find_by_id(patient_id)
        if not patient:
            return {"error": "Paciente no encontrado"}

        if not pdf_bytes:
            return {"error": "El archivo PDF está vacío"}

        extension = Path(filename or "").suffix.lower()
        if extension != ".pdf":
            return {"error": "El ECG debe cargarse en formato PDF"}

        if not pdf_bytes.startswith(b"%PDF"):
            return {"error": "El archivo no parece ser un PDF válido"}

        now = datetime.now().isoformat()

        patient_dir = Path("uploads") / "ecgs" / f"patient_{patient_id}"
        patient_dir.mkdir(parents=True, exist_ok=True)

        # La base de datos relacional genera el id. Por eso el nombre físico del
        # archivo usa un identificador único independiente del id de tabla.
        unique_name = f"ecg_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex}.pdf"
        file_path = patient_dir / unique_name
        file_path.write_bytes(pdf_bytes)

        entity = EcgEntity(
            patientId=patient_id,
            registeredAt=registeredAt or now,
            pdfUrl=file_path.as_posix(),
            originalFilename=filename,
            uploadedAt=now,
        )

        created = self.ecg_repo.save(self._to_dict(entity))
        ecg_dto = Ecg(**created)

        output_dir = patient_dir / f"ecg_{ecg_dto.id}_output"

        try:
            extraction_result = self.ecg_extraction_service.extract_from_pdf(
                pdf_path=file_path.as_posix(),
                source=None,
                output_dir=output_dir.as_posix(),
            )

            extraction_result = self._to_json_compatible(extraction_result)

            return {
                "ecg": ecg_dto,
                "extraction": extraction_result,
            }

        except Exception as error:
            return {
                "ecg": ecg_dto,
                "extraction": {
                    "processed": False,
                    "error": str(error),
                },
            }

    def list_patient_ecgs(self, patient_id: int) -> Union[Dict[str, Any], List[Ecg]]:
        patient_id = int(patient_id)

        if not self.patient_repo.exists_by_id(patient_id):
            return {"error": "Paciente no encontrado"}

        return [Ecg(**ecg) for ecg in self.ecg_repo.find_by_patient_id(patient_id)]

    def list_patient_ecgs_paged(
        self, patient_id: int, page: int, page_size: int
    ) -> Union[Dict[str, Any], Dict[str, Any]]:
        patient_id = int(patient_id)

        if not self.patient_repo.exists_by_id(patient_id):
            return {"error": "Paciente no encontrado"}

        items, total = self.ecg_repo.find_by_patient_id_paged(patient_id, page, page_size)
        return {
            "data": [Ecg(**ecg) for ecg in items],
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": math.ceil(total / page_size) if page_size > 0 else 0,
        }

    def get_ecg(self, ecg_id: int) -> Optional[Ecg]:
        ecg = self.ecg_repo.find_by_id(int(ecg_id))
        if not ecg:
            return None
        return Ecg(**ecg)

    def delete_ecg(self, ecg_id: int) -> Dict[str, Any]:
        ecg_id = int(ecg_id)
        ecg = self.ecg_repo.find_by_id(ecg_id)
        if not ecg:
            return {"error": "ECG no encontrado"}

        ok = self.ecg_repo.delete_by_id(ecg_id)
        if not ok:
            return {"error": "ECG no encontrado"}

        pdf_path = ecg.get("pdfUrl")
        if pdf_path:
            path = Path(pdf_path)
            if path.exists() and path.is_file():
                path.unlink()

        return {
            "deleted": True,
            "ecgId": ecg_id,
        }
