from business.medical_category_service import MedicalCategoryService
from models.dto.medical_category_dto import MedicalCategoryCreate, MedicalCategoryUpdate


def register_medical_category_tools(mcp, medical_category_service: MedicalCategoryService) -> None:
    @mcp.tool()
    async def create_medical_category(
        name: str,
        description: str | None = None,
        category_parent_id: int | None = None,
    ):
        """Crear una MedicalCategory. category_parent_id es opcional (relación reflexiva)."""
        try:
            category = MedicalCategoryCreate(
                name=name,
                description=description,
                category_parent_id=category_parent_id,
            )
            return medical_category_service.create_medical_category(category)
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    @mcp.tool()
    async def list_medical_categories():
        """Listar todas las MedicalCategory."""
        return medical_category_service.list_medical_categories()

    @mcp.tool()
    async def get_medical_category(category_id: int):
        """Consultar una MedicalCategory por id."""
        category = medical_category_service.get_medical_category(category_id)
        if not category:
            return {"error": "Categoría no encontrada"}
        return category

    @mcp.tool()
    async def update_medical_category(
        category_id: int,
        name: str | None = None,
        description: str | None = None,
        category_parent_id: int | None = None,
    ):
        """Actualizar parcialmente los datos de una MedicalCategory."""
        try:
            payload = {
                "name": name,
                "description": description,
                "category_parent_id": category_parent_id,
            }
            payload = {key: value for key, value in payload.items() if value is not None}
            if not payload:
                return {"error": "No se enviaron campos para actualizar"}
            return medical_category_service.update_medical_category(category_id, MedicalCategoryUpdate(**payload))
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    @mcp.tool()
    async def delete_medical_category(category_id: int):
        """Eliminar una MedicalCategory por id."""
        try:
            return medical_category_service.delete_medical_category(category_id)
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}
