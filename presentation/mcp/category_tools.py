from business.category_service import CategoryService
from models.dto.category_dto import CategoryCreate, CategoryUpdate


def register_category_tools(mcp, category_service: CategoryService) -> None:
    @mcp.tool()
    async def create_category(
        name: str,
        description: str | None = None,
        category_parent_id: int | None = None,
    ):
        """Crear una categoría. category_parent_id es opcional (relación reflexiva)."""
        try:
            category = CategoryCreate(
                name=name,
                description=description,
                category_parent_id=category_parent_id,
            )
            return category_service.create_category(category)
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    @mcp.tool()
    async def list_categories():
        """Listar todas las categorías."""
        return category_service.list_categories()

    @mcp.tool()
    async def get_category(category_id: int):
        """Consultar una categoría por id."""
        category = category_service.get_category(category_id)
        if not category:
            return {"error": "Categoría no encontrada"}
        return category

    @mcp.tool()
    async def update_category(
        category_id: int,
        name: str | None = None,
        description: str | None = None,
        category_parent_id: int | None = None,
    ):
        """Actualizar parcialmente los datos de una categoría."""
        try:
            payload = {
                "name": name,
                "description": description,
                "category_parent_id": category_parent_id,
            }
            payload = {key: value for key, value in payload.items() if value is not None}
            if not payload:
                return {"error": "No se enviaron campos para actualizar"}
            return category_service.update_category(category_id, CategoryUpdate(**payload))
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    @mcp.tool()
    async def delete_category(category_id: int):
        """Eliminar una categoría por id."""
        try:
            return category_service.delete_category(category_id)
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}
