import math
from typing import Any, Dict, List, Optional, Union

from data.medical_category_repository import MedicalCategoryRepository
from data.repository_factory import get_repositories
from models.dto.medical_category_dto import (
    MedicalCategory,
    MedicalCategoryCreate,
    MedicalCategoryUpdate,
    MedicalCategoryWithChildren,
)
from models.entity.medical_category_entity import MedicalCategoryEntity


class MedicalCategoryService:
    def __init__(self, repo: Optional[MedicalCategoryRepository] = None) -> None:
        self.repo = repo if repo is not None else get_repositories().medical_categories

    def _to_dict(self, entity: MedicalCategoryEntity) -> Dict[str, Any]:
        return {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "category_parent_id": entity.category_parent_id,
        }

    def create_medical_category(self, category: MedicalCategoryCreate) -> Union[Dict[str, Any], MedicalCategory]:
        if category.category_parent_id is not None and not self.repo.exists_by_id(int(category.category_parent_id)):
            return {"error": "La categoría padre no existe"}

        entity = MedicalCategoryEntity(
            name=category.name,
            description=category.description,
            category_parent_id=category.category_parent_id,
        )
        created = self.repo.save(self._to_dict(entity))
        return MedicalCategory(**created)

    def list_medical_categories(self) -> List[MedicalCategory]:
        return [MedicalCategory(**category) for category in self.repo.find_roots()]

    def list_medical_categories_paged(self, page: int, page_size: int) -> Dict[str, Any]:
        items, total = self.repo.find_roots_paged(page, page_size)
        return {
            "data": [MedicalCategory(**c) for c in items],
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": math.ceil(total / page_size) if page_size > 0 else 0,
        }

    def get_medical_category(self, category_id: int) -> Optional[MedicalCategoryWithChildren]:
        category_id = int(category_id)
        category = self.repo.find_by_id(category_id)
        if not category:
            return None

        children = self.repo.find_by_parent_id(category_id)
        return MedicalCategoryWithChildren(
            **category,
            children=[MedicalCategory(**child) for child in children],
        )

    def update_medical_category(
        self, category_id: int, update: MedicalCategoryUpdate
    ) -> Union[Dict[str, Any], MedicalCategory]:
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
        return MedicalCategory(**updated)

    def delete_medical_category(self, category_id: int) -> Dict[str, Any]:
        category_id = int(category_id)
        ok = self.repo.delete_by_id(category_id)
        if not ok:
            return {"error": "Categoría no encontrada"}
        return {"deleted": True, "id": category_id}
