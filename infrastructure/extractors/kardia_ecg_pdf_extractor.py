from pathlib import Path
from typing import Any, Dict, Optional

from business.extraction.ecg_extractor_interface import EcgExtractorInterface
from infrastructure.extractors.ecg_processing_core import (
    Config,
    ECGExtractor,
    ECGExtractorError,
    PDFType,
    SimpleValidator,
)


class KardiaEcgPdfExtractor(EcgExtractorInterface):
    """Extractor concreto para procesar PDFs de ECG de Kardia."""

    def extract_from_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        pdf_file = Path(pdf_path)

        if output_dir is None:
            output_path = pdf_file.parent / f"{pdf_file.stem}_output"
        else:
            output_path = Path(output_dir)

        output_path.mkdir(parents=True, exist_ok=True)

        try:
            config = Config(output_dir=output_path.as_posix())
            extractor = ECGExtractor(config)

            df, _processor = extractor.extract(
                pdf_path=pdf_file.as_posix(),
                pdf_type=PDFType.KARDIA,
            )

            extractor.save_results(df=df, output_dir=output_path.as_posix())
            extractor.plot_ecg(df=df, output_dir=output_path.as_posix())

            validation = SimpleValidator.validate(df)

            csv_path = output_path / "ecg_data.csv"
            excel_path = output_path / "ecg_data.xlsx"
            image_path = output_path / "ecg_data.png"

            return {
                "processed": True,
                "extractor": "KardiaEcgPdfExtractor",
                "pdfType": PDFType.KARDIA.value,
                "points": int(len(df)),
                "durationSeconds": float(df["Time(s)"].iloc[-1]),
                "voltageMinMv": float(df["Voltage(mV)"].min()),
                "voltageMaxMv": float(df["Voltage(mV)"].max()),
                "voltageRangeMv": float(df["Voltage(mV)"].max() - df["Voltage(mV)"].min()),
                "validation": validation,
                "files": {
                    "csv": csv_path.as_posix(),
                    "excel": excel_path.as_posix(),
                    "image": image_path.as_posix(),
                },
            }

        except ECGExtractorError as error:
            return {
                "processed": False,
                "extractor": "KardiaEcgPdfExtractor",
                "error": str(error),
            }

        except Exception as error:
            return {
                "processed": False,
                "extractor": "KardiaEcgPdfExtractor",
                "error": f"Error inesperado procesando ECG de Kardia: {str(error)}",
            }
