from pathlib import Path
from typing import Any, Dict, Optional

from business.extraction.ecg_extractor_interface import EcgExtractorInterface

# Estas clases vienen de tu script actual.
# Puedes dejarlas en este mismo archivo o moverlas a un archivo común.
from infrastructure.extractors.ecg_processing_core import (
    Config,
    ECGExtractor,
    PDFType,
    SimpleValidator,
    ECGExtractorError,
)


class AppleWatchEcgPdfExtractor(EcgExtractorInterface):
    """
    Extractor concreto para procesar PDFs de ECG generados por Apple Watch.

    Esta clase pertenece a infrastructure porque usa librerías técnicas como:
    - PyMuPDF
    - NumPy
    - Pandas
    - Matplotlib
    - SciPy

    La capa business solo la invoca mediante la interfaz.
    """

    def extract_from_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa un PDF de ECG de Apple Watch y genera archivos de salida.

        Args:
            pdf_path: Ruta del PDF guardado en el servidor.
            output_dir: Carpeta donde se guardarán CSV, Excel y PNG.

        Returns:
            Diccionario con métricas, rutas de archivos y estado del procesamiento.
        """

        pdf_file = Path(pdf_path)

        if output_dir is None:
            output_path = pdf_file.parent / f"{pdf_file.stem}_output"
        else:
            output_path = Path(output_dir)

        output_path.mkdir(parents=True, exist_ok=True)

        try:
            config = Config(
                output_dir=output_path.as_posix()
            )

            extractor = ECGExtractor(config)

            # Forzamos el tipo Apple Watch.
            # Así esta clase no procesa Kardia ni otros formatos.
            df, processor = extractor.extract(
                pdf_path=pdf_file.as_posix(),
                pdf_type=PDFType.APPLE_WATCH
            )

            extractor.save_results(
                df=df,
                output_dir=output_path.as_posix()
            )

            extractor.plot_ecg(
                df=df,
                output_dir=output_path.as_posix()
            )

            validation = SimpleValidator.validate(df)

            csv_path = output_path / "ecg_data.csv"
            excel_path = output_path / "ecg_data.xlsx"
            image_path = output_path / "ecg_data.png"

            return {
                "processed": True,
                "extractor": "AppleWatchEcgPdfExtractor",
                "pdfType": PDFType.APPLE_WATCH.value,
                "points": int(len(df)),
                "durationSeconds": float(df["Time(s)"].iloc[-1]),
                "voltageMinMv": float(df["Voltage(mV)"].min()),
                "voltageMaxMv": float(df["Voltage(mV)"].max()),
                "voltageRangeMv": float(
                    df["Voltage(mV)"].max() - df["Voltage(mV)"].min()
                ),
                "validation": validation,
                "files": {
                    "csv": csv_path.as_posix(),
                    "excel": excel_path.as_posix(),
                    "image": image_path.as_posix()
                }
            }

        except ECGExtractorError as error:
            return {
                "processed": False,
                "extractor": "AppleWatchEcgPdfExtractor",
                "error": str(error)
            }

        except Exception as error:
            return {
                "processed": False,
                "extractor": "AppleWatchEcgPdfExtractor",
                "error": f"Error inesperado procesando ECG de Apple Watch: {str(error)}"
            }
