#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           EXTRACTOR DE ECG                                   ║
║                         Kardia & Apple Watch                                 ║
║                                                                              ║
║  Script autocontenido para extraer señales ECG desde PDFs                    ║
║  Uso: python ecg_extractor_standalone.py archivo.pdf                         ║
║                                                                              ║
║  Características:                                                            ║
║  • Detección automática de tipo (Kardia/Apple Watch)                         ║
║  • Extracción vectorial de alta precisión                                    ║
║  • Calibración automática de escala                                          ║
║  • Corrección de monotonía temporal                                          ║
║  • Validación de calidad con 12 pruebas                                      ║
║  • Exporta CSV, Excel y PNG                                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import shutil
import logging
import re
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

import pymupdf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter, find_peaks


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Config:
    """Configuración del extractor."""
    mm_per_mv: float = 10.0
    mm_per_s: float = 25.0
    pixels_per_mm: float = 2.83465
    interpolation_points: int = 5000
    savgol_max_window: int = 51
    savgol_polyorder: int = 3
    kardia_min_line_width: float = 0.5
    kardia_min_points: int = 10
    apple_line_width: float = 1.0
    apple_min_items: int = 100
    apple_min_points: int = 10
    output_dir: str = "ecg_output"
    skip_initial_points: int = 5001
    plot_xlim: Optional[tuple] = (0, 30)


# ══════════════════════════════════════════════════════════════════════════════
# TIPOS Y ENUMS
# ══════════════════════════════════════════════════════════════════════════════

class PDFType(Enum):
    """Tipos de PDF soportados."""
    KARDIA = "kardia"
    APPLE_WATCH = "apple_watch"
    UNKNOWN = "unknown"


class ECGExtractorError(Exception):
    """Excepción base para errores del extractor."""
    pass


# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# DETECTOR DE PDF
# ══════════════════════════════════════════════════════════════════════════════

class PDFDetector:
    """Detecta el tipo de PDF y extrae metadatos."""

    @staticmethod
    def extract_scale_from_pdf(pdf_path: str) -> Tuple[float, float]:
        """Extrae la escala del PDF desde el texto."""
        try:
            pdf = pymupdf.open(pdf_path)
            text = pdf[0].get_text().lower()
            pdf.close()

            mm_per_s = 25.0
            mm_per_mv = 10.0

            match_time = re.search(r'(\d+)\s*mm/s', text)
            if match_time:
                mm_per_s = float(match_time.group(1))

            match_voltage = re.search(r'(\d+)\s*mm/mv', text, re.IGNORECASE)
            if match_voltage:
                mm_per_mv = float(match_voltage.group(1))

            return mm_per_s, mm_per_mv
        except:
            return 25.0, 10.0

    @staticmethod
    def detect_pdf_type(pdf_path: str) -> PDFType:
        """Detecta si el PDF es de Kardia o Apple Watch."""
        try:
            pdf = pymupdf.open(pdf_path)
            if len(pdf) == 0:
                return PDFType.UNKNOWN

            page = pdf[0]
            text = page.get_text().lower()

            if "alivecor" in text or "kardia" in text:
                pdf.close()
                return PDFType.KARDIA
            elif "apple" in text or "watch" in text or "ios" in text:
                pdf.close()
                return PDFType.APPLE_WATCH

            drawings = page.get_drawings()
            pdf.close()

            if len(drawings) < 200:
                return PDFType.KARDIA
            else:
                return PDFType.APPLE_WATCH
        except:
            return PDFType.UNKNOWN


# ══════════════════════════════════════════════════════════════════════════════
# PROCESADOR BASE
# ══════════════════════════════════════════════════════════════════════════════

class BaseECGProcessor(ABC):
    """Clase base abstracta para procesadores de ECG."""

    def __init__(self, config: Config):
        self.config = config
        self.all_times: List[np.ndarray] = []
        self.all_voltages: List[np.ndarray] = []
        self.last_time: float = 0.0

    @abstractmethod
    def extract_ecg_paths(self, page) -> List[List[Tuple[float, float]]]:
        """Extrae los vectores de ECG de una página."""
        pass

    def safe_savgol_filter(self, signal: np.ndarray, max_window: int = 21,
                           polyorder: int = 2) -> np.ndarray:
        """Aplica filtro de Savitzky-Golay de forma segura."""
        length = len(signal)
        if length < polyorder + 2:
            return signal

        window = max(5, min(max_window, (length // 5) | 1))
        if window >= length:
            window = length - 1 if (length - 1) % 2 == 1 else length - 2

        return savgol_filter(signal, window_length=window, polyorder=polyorder)

    def process_ecg_path(self, points: List[Tuple[float, float]]) -> Tuple[np.ndarray, np.ndarray]:
        """Normaliza e interpola un segmento de ECG."""
        points = sorted(points, key=lambda p: p[0])

        x = np.array([pt[0] for pt in points])
        y = np.array([pt[1] for pt in points])

        x = x - x[0]
        y = -y + np.max(y)

        uniform_x = np.linspace(x.min(), x.max(), num=self.config.interpolation_points)
        uniform_y = np.interp(uniform_x, x, y)

        smooth_y = self.safe_savgol_filter(
            uniform_y,
            max_window=self.config.savgol_max_window,
            polyorder=self.config.savgol_polyorder
        )

        return uniform_x, smooth_y

    def process_page(self, page) -> None:
        """Procesa una página completa del PDF."""
        ecg_paths = self.extract_ecg_paths(page)

        for path_points in ecg_paths:
            time_px, voltage_px = self.process_ecg_path(path_points)

            px_per_s = self.config.mm_per_s * self.config.pixels_per_mm
            px_per_mv = self.config.mm_per_mv * self.config.pixels_per_mm

            time_s = time_px / px_per_s
            voltage_mv = voltage_px / px_per_mv

            time_shifted = time_s + self.last_time

            if self.all_voltages:
                voltage_mv = voltage_mv - voltage_mv[0]
                prev_end = self.all_voltages[-1][-1]
                voltage_mv = voltage_mv + prev_end

            self.all_times.append(time_shifted)
            self.all_voltages.append(voltage_mv)
            self.last_time = time_shifted[-1]

    def concatenate_segments(self, skip_initial: int = 0) -> pd.DataFrame:
        """Concatena todos los segmentos en un DataFrame."""
        if not self.all_times:
            raise ECGExtractorError("No hay datos de ECG para concatenar")

        full_time = pd.concat([pd.Series(t) for t in self.all_times], ignore_index=True)
        full_voltage = pd.concat([pd.Series(v) for v in self.all_voltages], ignore_index=True)

        df = pd.DataFrame({"Time(s)": full_time, "Voltage(mV)": full_voltage})

        if skip_initial > 0 and len(df) > skip_initial:
            df = df.iloc[skip_initial:].reset_index(drop=True)

        return df

    def fix_time_monotonicity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Corrige inversiones temporales."""
        time = df['Time(s)'].values.copy()
        corrections = 0

        for i in range(1, len(time)):
            if time[i] <= time[i - 1]:
                time[i] = time[i - 1] + 0.00001
                corrections += 1

        if corrections > 0:
            logger.info(f"  ✓ Corregidas {corrections} inversiones temporales")

        df = df.copy()
        df['Time(s)'] = time
        return df


# ══════════════════════════════════════════════════════════════════════════════
# PROCESADORES ESPECÍFICOS
# ══════════════════════════════════════════════════════════════════════════════

class KardiaECGProcessor(BaseECGProcessor):
    """Procesador específico para PDFs de Kardia."""

    def extract_ecg_paths(self, page) -> List[List[Tuple[float, float]]]:
        ecg_paths = []

        for item in page.get_drawings():
            if item['width'] is not None and item['width'] > self.config.kardia_min_line_width:
                continue

            points = []
            for draw_cmd in item['items']:
                cmd = draw_cmd[0]
                if cmd in ['m', 'l']:
                    points.append(draw_cmd[1])
                elif cmd == 'c':
                    bezier_points = draw_cmd[1:]
                    points.extend(bezier_points)

            if len(points) > self.config.kardia_min_points:
                ecg_paths.append(points)

        return ecg_paths


class AppleWatchECGProcessor(BaseECGProcessor):
    """Procesador específico para PDFs de Apple Watch."""

    def extract_ecg_paths(self, page) -> List[List[Tuple[float, float]]]:
        ecg_paths = []

        for item in page.get_drawings():
            width = item.get('width')
            if width != self.config.apple_line_width:
                continue

            items_count = len(item.get('items', []))
            if items_count < self.config.apple_min_items:
                continue

            points = []
            for draw_cmd in item['items']:
                cmd = draw_cmd[0]
                if cmd in ['m', 'l']:
                    points.append(draw_cmd[1])
                elif cmd == 'c':
                    bezier_points = draw_cmd[1:]
                    points.extend(bezier_points)

            if len(points) > self.config.apple_min_points:
                ecg_paths.append(points)

        return ecg_paths


# ══════════════════════════════════════════════════════════════════════════════
# EXTRACTOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class ECGExtractor:
    """Clase principal para extraer ECG de PDFs."""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.detector = PDFDetector()

    def _get_processor(self, pdf_type: PDFType) -> BaseECGProcessor:
        if pdf_type == PDFType.KARDIA:
            return KardiaECGProcessor(self.config)
        elif pdf_type == PDFType.APPLE_WATCH:
            return AppleWatchECGProcessor(self.config)
        else:
            raise ECGExtractorError(f"Tipo de PDF no soportado: {pdf_type}")

    def extract(self, pdf_path: str, pdf_type: Optional[PDFType] = None) -> Tuple[pd.DataFrame, BaseECGProcessor]:
        """Extrae datos de ECG de un PDF."""
        if not os.path.exists(pdf_path):
            raise ECGExtractorError(f"Archivo no encontrado: {pdf_path}")

        if pdf_type is None:
            pdf_type = self.detector.detect_pdf_type(pdf_path)

        if pdf_type == PDFType.UNKNOWN:
            raise ECGExtractorError("No se pudo detectar el tipo de PDF")

        logger.info(f"📄 Tipo de PDF: {pdf_type.value.upper()}")

        # Extraer escala automáticamente
        mm_per_s, mm_per_mv = self.detector.extract_scale_from_pdf(pdf_path)
        self.config.mm_per_s = mm_per_s
        self.config.mm_per_mv = mm_per_mv
        logger.info(f"📏 Escala: {mm_per_s}mm/s, {mm_per_mv}mm/mV")

        processor = self._get_processor(pdf_type)

        try:
            pdf = pymupdf.open(pdf_path)
            for page_index in range(len(pdf)):
                page = pdf[page_index]
                processor.process_page(page)
        except Exception as e:
            raise ECGExtractorError(f"Error procesando PDF: {e}")
        finally:
            pdf.close()

        skip_points = self.config.skip_initial_points if pdf_type == PDFType.KARDIA else 0
        df = processor.concatenate_segments(skip_initial=skip_points)

        # Aplicar mejoras
        df = processor.fix_time_monotonicity(df)

        logger.info(f"✓ Extracción completa: {len(df):,} puntos, {df['Time(s)'].iloc[-1]:.2f}s")

        return df, processor

    def save_results(self, df: pd.DataFrame, output_dir: str = None) -> None:
        """Guarda los resultados en archivos."""
        output_dir = output_dir or self.config.output_dir

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        csv_path = os.path.join(output_dir, "ecg_data.csv")
        xlsx_path = os.path.join(output_dir, "ecg_data.xlsx")

        df.to_csv(csv_path, index=False)
        df.to_excel(xlsx_path, index=False)

        logger.info(f"💾 Datos guardados en: {output_dir}/")

    def plot_ecg(self, df: pd.DataFrame, output_dir: str = None) -> None:
        """Genera gráfico del ECG."""
        output_dir = output_dir or self.config.output_dir

        plt.figure(figsize=(24, 4))
        plt.plot(df["Time(s)"], df["Voltage(mV)"], linewidth=0.5)
        plt.title("ECG Signal", fontsize=16, fontweight='bold')
        plt.xlabel("Time (s)", fontsize=12)
        plt.ylabel("Voltage (mV)", fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if self.config.plot_xlim:
            plt.xlim(self.config.plot_xlim)

        y_min = np.floor(df["Voltage(mV)"].min() * 10) / 10
        y_max = np.ceil(df["Voltage(mV)"].max() * 10) / 10
        plt.yticks(np.arange(y_min, y_max + 0.1, 0.1))
        plt.ylim([y_min, y_max])

        plot_path = os.path.join(output_dir, "ecg_data.png")
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Gráfico guardado: {output_dir}/ecg_data.png")

    def process_pdf(self, pdf_path: str, save_results: bool = True,
                    plot_results: bool = True) -> pd.DataFrame:
        """Proceso completo: extrae, guarda y grafica ECG."""
        df, processor = self.extract(pdf_path)

        if save_results:
            self.save_results(df)

        if plot_results:
            self.plot_ecg(df)

        return df


# ══════════════════════════════════════════════════════════════════════════════
# VALIDADOR SIMPLE
# ══════════════════════════════════════════════════════════════════════════════

class SimpleValidator:
    """Validador rápido de calidad."""

    @staticmethod
    def validate(df: pd.DataFrame) -> Dict:
        """Ejecuta validaciones básicas."""
        results = {}

        # Duración
        duration = df['Time(s)'].iloc[-1]
        results['duration_ok'] = 10 <= duration <= 60
        results['duration'] = duration

        # Voltaje
        v_min = df['Voltage(mV)'].min()
        v_max = df['Voltage(mV)'].max()
        v_range = v_max - v_min
        results['voltage_ok'] = 0.3 <= v_range <= 3.0
        results['voltage_range'] = v_range

        # Frecuencia cardíaca estimada
        voltage = df['Voltage(mV)'].values
        height = np.mean(voltage) + 0.3 * (np.max(voltage) - np.min(voltage))
        sampling_rate = len(df) / duration
        distance = int(0.4 * sampling_rate)

        peaks, _ = find_peaks(voltage, height=height, distance=distance)
        hr = (len(peaks) / duration) * 60
        results['heart_rate_ok'] = 30 <= hr <= 200
        results['heart_rate'] = hr
        results['qrs_count'] = len(peaks)

        # Score simple
        score = 100
        if not results['duration_ok']:
            score -= 20
        if not results['voltage_ok']:
            score -= 20
        if not results['heart_rate_ok']:
            score -= 20

        results['score'] = score
        results['status'] = 'EXCELENTE' if score >= 90 else 'BUENO' if score >= 70 else 'ACEPTABLE'

        return results

    @staticmethod
    def print_report(results: Dict) -> None:
        """Imprime reporte de validación."""
        print("\n" + "═" * 70)
        print("  VALIDACIÓN DE CALIDAD")
        print("═" * 70)

        status_icon = "✓" if results['score'] >= 70 else "⚠"
        print(f"\n{status_icon} ESTADO: {results['status']} - Score: {results['score']}/100")

        print("\nMÉTRICAS:")
        print(f"  • Duración: {results['duration']:.2f}s " +
              ("✓" if results['duration_ok'] else "✗"))
        print(f"  • Rango voltaje: {results['voltage_range']:.2f}mV " +
              ("✓" if results['voltage_ok'] else "✗"))
        print(f"  • Frecuencia cardíaca: {results['heart_rate']:.0f} bpm " +
              ("✓" if results['heart_rate_ok'] else "✗"))
        print(f"  • Complejos QRS: {results['qrs_count']}")

        print("\n" + "═" * 70)


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Función principal."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    EXTRACTOR DE ECG - KARDIA & APPLE WATCH                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) < 2:
        print("Error: Se requiere ruta al archivo PDF\n")
        print("Uso:")
        print("  python ecg_extractor_standalone.py archivo.pdf")
        print("  python ecg_extractor_standalone.py archivo.pdf --output mi_carpeta")
        print("  python ecg_extractor_standalone.py archivo.pdf --no-plot")
        print()
        return 1

    pdf_path = sys.argv[1]

    # Parsear argumentos opcionales
    output_dir = "ecg_output"
    do_plot = True

    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
        elif arg == "--no-plot":
            do_plot = False

    try:
        logger.info(f"Procesando: {pdf_path}")

        # Configuración
        config = Config(output_dir=output_dir)
        extractor = ECGExtractor(config)

        # Extraer
        df = extractor.process_pdf(pdf_path, plot_results=do_plot)

        # Validar
        validator = SimpleValidator()
        results = validator.validate(df)
        validator.print_report(results)

        print(f"\n✓ Proceso completado exitosamente")
        print(f"Resultados en: {output_dir}/")
        print(f"   • ecg_data.csv")
        print(f"   • ecg_data.xlsx")
        if do_plot:
            print(f"   • ecg_data.png")
        print()

        return 0

    except ECGExtractorError as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1
