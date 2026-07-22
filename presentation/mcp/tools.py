from presentation.mcp.category_tools import register_category_tools
from presentation.mcp.core import category_service, ecg_service, mcp, patient_service, upload_provider
from presentation.mcp.ecg_tools import register_ecg_tools
from presentation.mcp.patient_tools import register_patient_tools

register_patient_tools(mcp, patient_service)
register_ecg_tools(mcp, ecg_service, upload_provider)
register_category_tools(mcp, category_service)


@mcp.tool()
async def get_version():
    """Versión del servidor médico."""
    return "2.0.0-medical-ecg"
