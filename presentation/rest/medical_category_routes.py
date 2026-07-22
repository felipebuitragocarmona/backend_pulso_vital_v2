from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from business.medical_category_service import MedicalCategoryService
from data.repository_factory import get_repositories
from models.dto.medical_category_dto import (
    MedicalCategory,
    MedicalCategoryCreate,
    MedicalCategoryUpdate,
    MedicalCategoryWithChildren,
)

router = APIRouter(tags=["medical-categories"])

repositories = get_repositories()
medical_category_service = MedicalCategoryService(repo=repositories.medical_categories)


@router.post("/medical-categories", response_model=MedicalCategory)
def create_medical_category(data: MedicalCategoryCreate):
    result = medical_category_service.create_medical_category(data)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/medical-categories", response_model=Dict[str, Any])
def list_medical_categories(page: int = Query(default=1, ge=1), pageSize: int = Query(default=10, ge=1, le=100)):
    return medical_category_service.list_medical_categories_paged(page, pageSize)


@router.get("/medical-categories/{category_id}", response_model=MedicalCategoryWithChildren)
def get_medical_category(category_id: int):
    category = medical_category_service.get_medical_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@router.put("/medical-categories/{category_id}", response_model=MedicalCategory)
def update_medical_category(category_id: int, data: MedicalCategoryUpdate):
    result = medical_category_service.update_medical_category(category_id, data)
    if isinstance(result, dict) and result.get("error"):
        status_code = 404 if result["error"] == "Categoría no encontrada" else 400
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.delete("/medical-categories/{category_id}")
def delete_medical_category(category_id: int):
    result = medical_category_service.delete_medical_category(category_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
