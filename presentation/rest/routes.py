from fastapi import APIRouter

from presentation.rest.ai_model_category_routes import router as ai_model_category_router
from presentation.rest.ecg_routes import router as ecg_router
from presentation.rest.medical_category_routes import router as medical_category_router
from presentation.rest.patient_routes import router as patient_router

router = APIRouter()
router.include_router(patient_router)
router.include_router(ecg_router)
router.include_router(medical_category_router)
router.include_router(ai_model_category_router)
