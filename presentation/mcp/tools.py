import base64
from typing import Any

from fastmcp import FastMCP
from fastmcp.apps.file_upload import FileUpload

from business.ecg_service import EcgService
from business.patient_service import PatientService
from data.repository_factory import get_repositories
from models.dto.patient_dto import PatientCreate, PatientUpdate


class UserScopedUpload(FileUpload):
    """Proveedor de carga de archivos para FastMCP en modo HTTP stateless."""

    def _get_scope_key(self, ctx: Any):
        request = None
        if hasattr(ctx, "get_http_request"):
            try:
                request = ctx.get_http_request()
            except Exception:
                request = None

        if request is None and hasattr(ctx, "request"):
            request = ctx.request

        headers = request.headers if request is not None and hasattr(request, "headers") else {}
        for header_name in ("x-user-id", "x-patient-user-id", "x-session-key"):
            value = headers.get(header_name) if hasattr(headers, "get") else None
            if value:
                return f"user:{value}"

        if request is not None and getattr(request, "client", None) is not None:
            host = getattr(request.client, "host", None)
            if host:
                return f"ip:{host}"

        return "medical-ecg-default-upload-scope"

    def get_file_bytes(self, name: str, ctx: Any) -> bytes:
        scope = self._get_scope_key(ctx)
        session_files = self._store.get(scope, {})
        entry = session_files.get(name)
        if entry is None:
            available = list(session_files.keys())
            raise ValueError(f"Archivo {name!r} no encontrado. Disponibles: {available}")
        return base64.b64decode(entry["data"])


mcp = FastMCP("medical_ecg")
upload_provider = UserScopedUpload(
    name="ecg_pdf_manager",
    title="Subir PDF ECG Apple Watch",
    description="Carga el PDF de ECG exportado desde Apple Watch y lo asocia a un paciente",
    drop_label="Suelta aquí el PDF ECG del paciente",
)
mcp.add_provider(upload_provider)

repositories = get_repositories()
patient_service = PatientService(repo=repositories.patients)
ecg_service = EcgService(
    ecg_repo=repositories.ecgs,
    patient_repo=repositories.patients,
)


@mcp.tool()
async def create_patient(fullName: str, birthDate: str):
    """Crear un paciente."""
    try:
        patient = PatientCreate(fullName=fullName, birthDate=birthDate)
        return patient_service.create_patient(patient)
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def list_patients():
    """Listar todos los pacientes."""
    return patient_service.list_patients()


@mcp.tool()
async def get_patient(patient_id: int):
    """Consultar un paciente por id."""
    patient = patient_service.get_patient(patient_id)
    if not patient:
        return {"error": "Paciente no encontrado"}
    return patient


@mcp.tool()
async def update_patient(patient_id: int, fullName: str | None = None, birthDate: str | None = None):
    """Actualizar parcialmente los datos de un paciente."""
    try:
        payload = {"fullName": fullName, "birthDate": birthDate}
        payload = {key: value for key, value in payload.items() if value is not None}
        if not payload:
            return {"error": "No se enviaron campos para actualizar"}
        return patient_service.update_patient(patient_id, PatientUpdate(**payload))
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def delete_patient(patient_id: int):
    """Eliminar un paciente por id. También elimina los ECG asociados."""
    try:
        return patient_service.delete_patient(patient_id)
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def upload_patient_ecg(patient_id: int, filename: str, ctx: Any, registeredAt: str | None = None):
    """Asociar un PDF ECG cargado previamente al paciente indicado."""
    try:
        pdf_bytes = upload_provider.get_file_bytes(filename, ctx)
        return ecg_service.upload_ecg_pdf_bytes(
            patient_id=patient_id,
            pdf_bytes=pdf_bytes,
            filename=filename,
            registeredAt=registeredAt,
        )
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def list_patient_ecgs(patient_id: int):
    """Listar todos los PDF ECG asociados a un paciente."""
    return ecg_service.list_patient_ecgs(patient_id)


@mcp.tool()
async def get_ecg(ecg_id: int):
    """Consultar un registro ECG por id."""
    ecg = ecg_service.get_ecg(ecg_id)
    if not ecg:
        return {"error": "ECG no encontrado"}
    return ecg


@mcp.tool()
async def delete_ecg(ecg_id: int):
    """Eliminar un registro ECG por id."""
    return ecg_service.delete_ecg(ecg_id)


@mcp.tool()
async def get_version():
    """Versión del servidor médico."""
    return "2.0.0-medical-ecg"
