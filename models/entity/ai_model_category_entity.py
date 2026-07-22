from dataclasses import dataclass
from typing import Optional


@dataclass
class AIModelCategoryEntity:
    name: str
    description: Optional[str] = None
    category_parent_id: Optional[int] = None
    id: Optional[int] = None
