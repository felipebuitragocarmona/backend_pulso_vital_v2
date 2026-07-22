from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from business.ai_model_category_service import AIModelCategoryService
from data.repository_factory import get_repositories
from models.dto.ai_model_category_dto import (
    AIModelCategory,
    AIModelCategoryCreate,
    AIModelCategoryUpdate,
    AIModelCategoryWithChildren,
)

router = APIRouter(tags=["ai-model-categories"])

repositories = get_repositories()
ai_model_category_service = AIModelCategoryService(repo=repositories.ai_model_categories)


@router.post("/ai-model-categories", response_model=AIModelCategory)
def create_ai_model_category(data: AIModelCategoryCreate):
    result = ai_model_category_service.create_category(data)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/ai-model-categories", response_model=Dict[str, Any])
def list_ai_model_categories(page: int = Query(default=1, ge=1), pageSize: int = Query(default=10, ge=1, le=100)):
    return ai_model_category_service.list_categories_paged(page, pageSize)


@router.get("/ai-model-categories/{category_id}", response_model=AIModelCategoryWithChildren)
def get_ai_model_category(category_id: int):
    category = ai_model_category_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@router.put("/ai-model-categories/{category_id}", response_model=AIModelCategory)
def update_ai_model_category(category_id: int, data: AIModelCategoryUpdate):
    result = ai_model_category_service.update_category(category_id, data)
    if isinstance(result, dict) and result.get("error"):
        status_code = 404 if result["error"] == "Categoría no encontrada" else 400
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.delete("/ai-model-categories/{category_id}")
def delete_ai_model_category(category_id: int):
    result = ai_model_category_service.delete_category(category_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
