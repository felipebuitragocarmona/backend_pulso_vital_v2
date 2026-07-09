from fastapi import APIRouter

from presentation.rest.ecg_routes import router as ecg_router
from presentation.rest.patient_routes import router as patient_router

router = APIRouter()
router.include_router(patient_router)
router.include_router(ecg_router)
