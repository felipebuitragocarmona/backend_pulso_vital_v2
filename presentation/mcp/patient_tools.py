from business.patient_service import PatientService
from models.dto.patient_dto import PatientCreate, PatientUpdate


def register_patient_tools(mcp, patient_service: PatientService) -> None:
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
        """Eliminar un paciente por id. Tambien elimina los ECG asociados."""
        try:
            return patient_service.delete_patient(patient_id)
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}
