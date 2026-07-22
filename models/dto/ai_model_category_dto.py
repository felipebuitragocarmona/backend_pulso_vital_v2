from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AIModelCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, examples=["Modelos de clasificación"])
    description: Optional[str] = Field(default=None, examples=["Categorías para modelos de IA"])
    category_parent_id: Optional[int] = Field(default=None, examples=[None])


class AIModelCategoryCreate(AIModelCategoryBase):
    pass


class AIModelCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    category_parent_id: Optional[int] = None


class AIModelCategory(AIModelCategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class AIModelCategoryWithChildren(AIModelCategory):
    children: List[AIModelCategory] = Field(default_factory=list)
