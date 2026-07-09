from typing import Any

from business.ecg_service import EcgService


def register_ecg_tools(mcp, ecg_service: EcgService, upload_provider) -> None:
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
