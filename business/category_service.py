import math
from typing import Any, Dict, List, Optional, Union

from data.category_repository import CategoryRepository
from data.repository_factory import get_repositories
from models.dto.category_dto import Category, CategoryCreate, CategoryUpdate, CategoryWithChildren
from models.entity.category_entity import CategoryEntity


class CategoryService:
    """Casos de uso de categorías.

    Incluye una relación reflexiva (category_parent_id) para modelar
    categorías padre/hijo dentro de la misma entidad.
    """

    def __init__(self, repo: Optional[CategoryRepository] = None) -> None:
        self.repo = repo if repo is not None else get_repositories().categories

    def _to_dict(self, entity: CategoryEntity) -> Dict[str, Any]:
        return {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "category_parent_id": entity.category_parent_id,
        }

    def create_category(self, category: CategoryCreate) -> Union[Dict[str, Any], Category]:
        if category.category_parent_id is not None:
            if not self.repo.exists_by_id(int(category.category_parent_id)):
                return {"error": "La categoría padre no existe"}

        entity = CategoryEntity(
            name=category.name,
            description=category.description,
            category_parent_id=category.category_parent_id,
        )
        created = self.repo.save(self._to_dict(entity))
        return Category(**created)

    def list_categories(self) -> List[Category]:
        return [Category(**category) for category in self.repo.find_roots()]

    def list_categories_paged(self, page: int, page_size: int) -> Dict[str, Any]:
        items, total = self.repo.find_roots_paged(page, page_size)
        return {
            "data": [Category(**c) for c in items],
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": math.ceil(total / page_size) if page_size > 0 else 0,
        }

    def get_category(self, category_id: int) -> Optional[CategoryWithChildren]:
        category_id = int(category_id)
        category = self.repo.find_by_id(category_id)
        if not category:
            return None

        children = self.repo.find_by_parent_id(category_id)
        return CategoryWithChildren(
            **category,
            children=[Category(**child) for child in children],
        )

    def update_category(self, category_id: int, update: CategoryUpdate) -> Union[Dict[str, Any], Category]:
        category_id = int(category_id)
        data = update.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            return {"error": "No se enviaron campos para actualizar"}

        if "category_parent_id" in data:
            parent_id = int(data["category_parent_id"])
            if parent_id == category_id:
                return {"error": "Una categoría no puede ser su propio padre"}
            if not self.repo.exists_by_id(parent_id):
                return {"error": "La categoría padre no existe"}

        updated = self.repo.update(category_id, data)
        if not updated:
            return {"error": "Categoría no encontrada"}
        return Category(**updated)

    def delete_category(self, category_id: int) -> Dict[str, Any]:
        category_id = int(category_id)
        ok = self.repo.delete_by_id(category_id)
        if not ok:
            return {"error": "Categoría no encontrada"}
        return {"deleted": True, "id": category_id}
