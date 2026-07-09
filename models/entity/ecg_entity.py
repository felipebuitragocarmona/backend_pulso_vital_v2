from dataclasses import dataclass
from typing import Optional


@dataclass
class EcgEntity:
    patientId: int
    registeredAt: str
    pdfUrl: str
    originalFilename: Optional[str] = None
    uploadedAt: Optional[str] = None
    id: Optional[int] = None
