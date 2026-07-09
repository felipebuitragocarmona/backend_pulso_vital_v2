from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class EcgExtractorInterface(ABC):

    @abstractmethod
    def extract_from_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        pass