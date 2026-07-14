import os
import numpy as np
import pandas as pd
import neurokit2 as nk


FS = 300

FEATURES = [
    "rr_mean_seconds",
    "rr_std_seconds",
    "r_peaks_detected",
    "heart_rate_bpm",
    "p_rate_detected_ratio",
    "qrs_narrow_ratio",
]


class NpyEcgFeatureExtractor:
    """
    Extrae un subconjunto de features clínicas desde un archivo .npy que
    contiene una señal ECG de un solo canal muestreada a FS Hz.

    Uso:
        extractor = NpyEcgFeatureExtractor()
        csv_path  = extractor.extract_and_save("/ruta/al/ecg_data.npy")
    """

    def __init__(self, sampling_rate: int = FS):
        self.fs = sampling_rate

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def extract_and_save(self, npy_path: str) -> str:
        """
        Procesa *npy_path*, calcula las features y guarda un CSV con el
        mismo nombre base en el mismo directorio.

        Devuelve la ruta absoluta del CSV generado.
        """
        features = self._compute_features(npy_path)
        csv_path = self._save_csv(npy_path, features)
        return csv_path

    def compute(self, npy_path: str) -> dict:
        """Devuelve las features como diccionario sin guardar nada."""
        return self._compute_features(npy_path)

    # ------------------------------------------------------------------
    # Cálculo de features
    # ------------------------------------------------------------------

    def _compute_features(self, npy_path: str) -> dict:
        result = {k: None for k in FEATURES}
        result["r_peaks_detected"] = 0
        result["error"] = ""

        try:
            ecg = np.load(npy_path)
            ecg = np.asarray(ecg, dtype=float).flatten()

            if len(ecg) < self.fs * 3:
                result["error"] = "signal_too_short"
                return result

            signals, info = nk.ecg_process(ecg, sampling_rate=self.fs)

            r_peaks = self._clean_peaks(info.get("ECG_R_Peaks", []))
            p_peaks = self._clean_peaks(info.get("ECG_P_Peaks", []))
            ecg_clean = np.asarray(signals["ECG_Clean"], dtype=float)

            result["r_peaks_detected"] = int(len(r_peaks))

            # RR + HR
            if len(r_peaks) >= 2:
                rr = np.diff(r_peaks) / self.fs
                rr = rr[np.isfinite(rr)]
                if len(rr) > 0:
                    rr_mean = float(np.mean(rr))
                    result["rr_mean_seconds"] = round(rr_mean, 4)
                    result["rr_std_seconds"] = round(float(np.std(rr)), 4)
                    if rr_mean > 0:
                        result["heart_rate_bpm"] = round(60.0 / rr_mean, 4)

            # Ratio P detectadas / R detectadas
            if len(r_peaks) > 0:
                result["p_rate_detected_ratio"] = round(
                    float(len(p_peaks) / len(r_peaks)), 4
                )

            # QRS narrow ratio
            qrs_durations = self._estimate_qrs_durations(ecg_clean, r_peaks)
            if len(qrs_durations) > 0:
                result["qrs_narrow_ratio"] = round(
                    float(np.mean(np.array(qrs_durations) < 0.12)), 4
                )

            if len(r_peaks) < 2:
                result["error"] = "too_few_r_peaks"

        except Exception as exc:
            result["error"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_peaks(x) -> np.ndarray:
        if x is None:
            return np.array([], dtype=int)
        arr = np.asarray(x, dtype=float).flatten()
        arr = arr[np.isfinite(arr)]
        return arr.astype(int)

    def _estimate_qrs_durations(self, ecg_clean: np.ndarray, r_peaks: np.ndarray) -> list:
        """
        Estima la duración de cada complejo QRS buscando cruces de pendiente
        alrededor de cada pico R. Devuelve lista de duraciones en segundos.
        """
        if len(r_peaks) == 0:
            return []

        deriv = np.abs(np.gradient(ecg_clean))
        global_ref = (
            np.percentile(deriv[np.isfinite(deriv)], 75)
            if np.any(np.isfinite(deriv))
            else 0
        )

        durations = []
        for rp in r_peaks:
            left_limit = max(0, rp - int(0.12 * self.fs))
            right_limit = min(len(ecg_clean) - 1, rp + int(0.12 * self.fs))

            local = deriv[left_limit : right_limit + 1]
            if len(local) < 5:
                continue

            local_ref = max(np.percentile(local, 35), global_ref * 0.2)

            qrs_on = rp
            for i in range(rp, left_limit, -1):
                if deriv[i] < local_ref:
                    qrs_on = i
                    break

            qrs_off = rp
            for i in range(rp, right_limit):
                if deriv[i] < local_ref:
                    qrs_off = i
                    break

            dur = (qrs_off - qrs_on) / self.fs
            if 0.04 <= dur <= 0.20:
                durations.append(float(dur))

        return durations

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _save_csv(self, npy_path: str, features: dict) -> str:
        output_dir = os.path.dirname(os.path.abspath(npy_path))
        base_name = os.path.splitext(os.path.basename(npy_path))[0]
        csv_path = os.path.join(output_dir, f"{base_name}_features.csv")

        row = {k: features.get(k) for k in FEATURES}
        pd.DataFrame([row]).to_csv(csv_path, index=False)
        return csv_path
