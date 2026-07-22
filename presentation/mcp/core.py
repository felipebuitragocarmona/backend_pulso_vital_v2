import base64
from typing import Any

from fastmcp import FastMCP
from fastmcp.apps.file_upload import FileUpload

from business.category_service import CategoryService
from business.ecg_service import EcgService
from business.patient_service import PatientService
from data.repository_factory import get_repositories


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
category_service = CategoryService(repo=repositories.categories)
