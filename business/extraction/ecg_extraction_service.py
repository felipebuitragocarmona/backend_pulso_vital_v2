from pathlib import Path
from typing import Any, Dict, Optional

from infrastructure.extractors.ecg_extractor_factory import EcgExtractorFactory


class EcgExtractionService:
    """
    Servicio de negocio encargado de coordinar la extracción de datos
    desde un PDF de ECG.

    Este servicio NO debe tener lógica directa de PyMuPDF, NumPy,
    Pandas o Matplotlib. Esa lógica queda en el extractor concreto.
    """

    def __init__(self, extractor_factory: Optional[EcgExtractorFactory] = None) -> None:
        self.extractor_factory = extractor_factory or EcgExtractorFactory()

    def extract_from_pdf(
        self,
        pdf_path: str,
        source: str = "apple_watch",
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        pdf_file = Path(pdf_path)

        self._validate_pdf_file(pdf_file)

        final_output_dir = self._prepare_output_dir(
            pdf_file=pdf_file,
            output_dir=output_dir
        )

        extractor = self.extractor_factory.create(source)

        extraction_result = extractor.extract_from_pdf(
            pdf_path=pdf_file.as_posix(),
            output_dir=final_output_dir.as_posix()
        )

        return {
            "processed": True,
            "source": source,
            "pdfPath": pdf_file.as_posix(),
            "outputDir": final_output_dir.as_posix(),
            "result": extraction_result
        }

    def _validate_pdf_file(self, pdf_file: Path) -> None:
        if not pdf_file.exists():
            raise FileNotFoundError(f"No se encontró el archivo PDF: {pdf_file}")

        if not pdf_file.is_file():
            raise ValueError(f"La ruta no corresponde a un archivo válido: {pdf_file}")

        if pdf_file.suffix.lower() != ".pdf":
            raise ValueError("El archivo debe tener extensión .pdf")

    def _prepare_output_dir(
        self,
        pdf_file: Path,
        output_dir: Optional[str]
    ) -> Path:
        if output_dir:
            final_output_dir = Path(output_dir)
        else:
            final_output_dir = pdf_file.parent / f"{pdf_file.stem}_output"

        final_output_dir.mkdir(parents=True, exist_ok=True)

        return final_output_dir