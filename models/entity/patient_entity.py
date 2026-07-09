from dataclasses import dataclass
from typing import Optional


@dataclass
class PatientEntity:
    fullName: str
    birthDate: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    id: Optional[int] = None
