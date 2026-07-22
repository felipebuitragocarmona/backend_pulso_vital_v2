from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MedicalCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, examples=["Cardiología"])
    description: Optional[str] = Field(default=None, examples=["Enfermedades del corazón"])
    category_parent_id: Optional[int] = Field(default=None, examples=[None])


class MedicalCategoryCreate(MedicalCategoryBase):
    pass


class MedicalCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    category_parent_id: Optional[int] = None


class MedicalCategory(MedicalCategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MedicalCategoryWithChildren(MedicalCategory):
    children: List[MedicalCategory] = Field(default_factory=list)
