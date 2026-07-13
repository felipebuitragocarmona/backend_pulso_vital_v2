from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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


# ── Estilo ECG papel ─────────────────────────────────────────────────────────

_ECG_STYLE = {
    "bg_color": "#FFFFFF",
    "grid_major_color": "#FFAAAA",
    "grid_minor_color": "#FFE0E0",
    "signal_color": "#000080",
    "signal_lw": 0.8,
    "dpi": 150,
    "fig_width": 12,
    "fig_height": 3,
    "x_min": 0.0,
    "x_max": 30.0,
    "y_min": -1.5,
    "y_max": 1.5,
}


def _load_apple_ecg_csv(
    csv_path: str,
    start_second: float = 0.0,
    max_seconds: float = 30.0,
    target_fs: float = 300.0,
) -> np.ndarray:
    """Lee un CSV con columnas Time(s) y Voltage(mV) y devuelve
    una señal interpolada a target_fs Hz."""
    csv_file = Path(csv_path).expanduser().resolve()
    if not csv_file.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {csv_file}")

    dataframe = pd.read_csv(csv_file)
    required = {"Time(s)", "Voltage(mV)"}
    missing = required.difference(dataframe.columns)
    if missing:
        raise ValueError(
            "El CSV debe contener las columnas 'Time(s)' y 'Voltage(mV)'. "
            f"Faltan: {sorted(missing)}"
        )

    time = pd.to_numeric(dataframe["Time(s)"], errors="coerce").to_numpy(dtype=np.float64)
    voltage = pd.to_numeric(dataframe["Voltage(mV)"], errors="coerce").to_numpy(dtype=np.float64)

    valid = np.isfinite(time) & np.isfinite(voltage)
    time = time[valid]
    voltage = voltage[valid]

    if len(time) < 2:
        raise ValueError("El CSV no contiene suficientes datos válidos.")

    order = np.argsort(time)
    time = time[order]
    voltage = voltage[order]

    time, unique_idx = np.unique(time, return_index=True)
    voltage = voltage[unique_idx]
    time = time - time[0]

    end_second = min(start_second + max_seconds, time[-1])
    actual_seconds = end_second - start_second

    n_samples = int(actual_seconds * target_fs)
    new_time = np.arange(n_samples) / target_fs + start_second
    signal = np.interp(new_time, time, voltage)
    return signal.astype(np.float32)


def _draw_ecg_grid(ax) -> None:
    """Dibuja la cuadrícula estilo papel milimetrado de ECG."""
    ax.set_facecolor(_ECG_STYLE["bg_color"])
    ax.grid(True, which="minor", color=_ECG_STYLE["grid_minor_color"], linewidth=0.4, linestyle="-")
    ax.grid(True, which="major", color=_ECG_STYLE["grid_major_color"], linewidth=0.8, linestyle="-")
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(plt.MultipleLocator(0.04))
    ax.xaxis.set_major_locator(plt.MultipleLocator(0.2))
    ax.yaxis.set_minor_locator(plt.MultipleLocator(0.1))
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.5))
    ax.set_xlim(_ECG_STYLE["x_min"], _ECG_STYLE["x_max"])
    ax.set_ylim(_ECG_STYLE["y_min"], _ECG_STYLE["y_max"])


def _signal_to_image(
    signal: np.ndarray,
    output_path: str,
    fs: float = 300.0,
    max_seconds: float = 30.0,
) -> str:
    """Guarda la señal como imagen PNG con estilo ECG papel."""
    x_max = _ECG_STYLE["x_max"]
    n_samples = int(min(min(max_seconds, x_max) * fs, len(signal)))
    sig = signal[:n_samples]

    if np.ptp(sig) > 10:
        sig = sig / 1000.0

    time_axis = np.arange(n_samples) / fs

    output_file = Path(output_path).expanduser().resolve()
    if output_file.suffix.lower() != ".png":
        output_file = output_file.with_suffix(".png")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(
        figsize=(_ECG_STYLE["fig_width"], _ECG_STYLE["fig_height"]),
        facecolor=_ECG_STYLE["bg_color"],
    )
    ax = fig.add_axes([0, 0, 1, 1])
    _draw_ecg_grid(ax)
    ax.plot(time_axis, sig, color=_ECG_STYLE["signal_color"], linewidth=_ECG_STYLE["signal_lw"])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.savefig(
        output_file,
        dpi=_ECG_STYLE["dpi"],
        bbox_inches="tight",
        pad_inches=0,
        facecolor=_ECG_STYLE["bg_color"],
    )
    plt.close(fig)
    return str(output_file)


def _generate_paper_image_from_csv(
    csv_path: str,
    output_path: str,
    start_second: float = 0.0,
) -> str:
    """Genera la imagen estilo ECG papel a partir del CSV."""
    signal = _load_apple_ecg_csv(
        csv_path=csv_path,
        start_second=start_second,
        max_seconds=30.0,
        target_fs=300.0,
    )
    return _signal_to_image(
        signal=signal,
        output_path=output_path,
        fs=300.0,
        max_seconds=30.0,
    )


def _convert_csv_to_npy(
    csv_path: str,
    output_path: str,
    target_fs: float = 300.0,
    duration_seconds: float = 30.0,
) -> str:
    """Convierte un CSV de ECG en un archivo NPY de duración fija.

    Si el ECG dura menos de duration_seconds, completa las muestras
    faltantes repitiendo el último valor disponible.
    """
    csv_file = Path(csv_path).expanduser().resolve()
    output_file = Path(output_path).expanduser().resolve()

    if not csv_file.is_file():
        raise FileNotFoundError(f"No se encontró el archivo CSV: {csv_file}")

    dataframe = pd.read_csv(csv_file)
    required_columns = {"Time(s)", "Voltage(mV)"}
    missing_columns = required_columns.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(
            "El CSV debe contener las columnas 'Time(s)' y 'Voltage(mV)'. "
            f"Columnas faltantes: {sorted(missing_columns)}"
        )

    time = pd.to_numeric(dataframe["Time(s)"], errors="coerce").to_numpy(dtype=np.float64)
    voltage = pd.to_numeric(dataframe["Voltage(mV)"], errors="coerce").to_numpy(dtype=np.float64)

    valid = np.isfinite(time) & np.isfinite(voltage)
    time = time[valid]
    voltage = voltage[valid]

    if len(time) < 2:
        raise ValueError("El CSV no contiene suficientes datos válidos.")

    order = np.argsort(time)
    time = time[order]
    voltage = voltage[order]

    time, unique_indices = np.unique(time, return_index=True)
    voltage = voltage[unique_indices]

    if len(time) < 2:
        raise ValueError(
            "Después de eliminar tiempos duplicados no existen suficientes muestras."
        )

    time = time - time[0]

    number_of_samples = int(round(duration_seconds * target_fs))
    target_time = np.arange(number_of_samples, dtype=np.float64) / target_fs

    # right=voltage[-1] rellena con el último valor si la señal es más corta.
    signal = np.interp(
        target_time,
        time,
        voltage,
        left=voltage[0],
        right=voltage[-1],
    ).astype(np.float32)

    if output_file.suffix.lower() != ".npy":
        output_file = output_file.with_suffix(".npy")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    np.save(output_file, signal, allow_pickle=False)
    return str(output_file)


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

            csv_path = output_path / "ecg_data.csv"
            excel_path = output_path / "ecg_data.xlsx"
            image_path = output_path / "ecg_data.png"
            paper_image_path = output_path / "ecg_paper.png"
            npy_path = output_path / "ecg_data.npy"

            _generate_paper_image_from_csv(
                csv_path=csv_path.as_posix(),
                output_path=paper_image_path.as_posix(),
                start_second=0.0,
            )

            _convert_csv_to_npy(
                csv_path=csv_path.as_posix(),
                output_path=npy_path.as_posix(),
                target_fs=300.0,
                duration_seconds=30.0,
            )

            validation = SimpleValidator.validate(df)

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
                    "image": image_path.as_posix(),
                    "imagePaper": paper_image_path.as_posix(),
                    "npy": npy_path.as_posix()
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
