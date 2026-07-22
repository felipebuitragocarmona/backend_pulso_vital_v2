from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from business.category_service import CategoryService
from data.repository_factory import get_repositories
from models.dto.category_dto import Category, CategoryCreate, CategoryUpdate, CategoryWithChildren

router = APIRouter(tags=["categories"])

repositories = get_repositories()
category_service = CategoryService(repo=repositories.categories)


@router.post("/categories", response_model=Category)
def create_category(data: CategoryCreate):
    result = category_service.create_category(data)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/categories", response_model=Dict[str, Any])
def list_categories(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
):
    return category_service.list_categories_paged(page, pageSize)


@router.get("/categories/{category_id}", response_model=CategoryWithChildren)
def get_category(category_id: int):
    category = category_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@router.put("/categories/{category_id}", response_model=Category)
def update_category(category_id: int, data: CategoryUpdate):
    result = category_service.update_category(category_id, data)
    if isinstance(result, dict) and result.get("error"):
        status_code = 404 if result["error"] == "Categoría no encontrada" else 400
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.delete("/categories/{category_id}")
def delete_category(category_id: int):
    result = category_service.delete_category(category_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
