from typing import Any, Dict, Optional

from business.extraction.ecg_extractor_interface import EcgExtractorInterface


class SamsungHealthEcgPdfExtractor(EcgExtractorInterface):
    """Extractor placeholder para Samsung Health (pendiente de implementacion)."""

    def extract_from_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            "SamsungHealthEcgPdfExtractor aun no esta implementado para este formato de PDF."
        )
