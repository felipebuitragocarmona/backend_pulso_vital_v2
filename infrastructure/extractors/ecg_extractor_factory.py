import os

from business.extraction.ecg_extractor_interface import EcgExtractorInterface
from infrastructure.extractors.apple_watch_ecg_pdf_extractor import AppleWatchEcgPdfExtractor
from infrastructure.extractors.ecg_extractor_creator_interface import EcgExtractorCreatorInterface
from infrastructure.extractors.kardia_ecg_pdf_extractor import KardiaEcgPdfExtractor
from infrastructure.extractors.samsung_health_ecg_pdf_extractor import SamsungHealthEcgPdfExtractor


class AppleWatchCreator(EcgExtractorCreatorInterface):
    def create(self) -> EcgExtractorInterface:
        return AppleWatchEcgPdfExtractor()


class KardiaCreator(EcgExtractorCreatorInterface):
    def create(self) -> EcgExtractorInterface:
        return KardiaEcgPdfExtractor()


class SamsungHealthCreator(EcgExtractorCreatorInterface):
    def create(self) -> EcgExtractorInterface:
        return SamsungHealthEcgPdfExtractor()


class EcgExtractorCreator:
    """Selecciona un creator por source y construye el extractor concreto."""

    SOURCE_ENV_VAR = "ECG_EXTRACTOR_SOURCE"

    def __init__(self, source_env_var: str | None = None) -> None:
        self.source_env_var = source_env_var or self.SOURCE_ENV_VAR
        self._creators: dict[str, EcgExtractorCreatorInterface] = {
            "apple_watch": AppleWatchCreator(),
            "kardia": KardiaCreator(),
            "samsung": SamsungHealthCreator(),
        }
        self._aliases: dict[str, str] = {
            "apple": "apple_watch",
            "applewatch": "apple_watch",
            "alivecor": "kardia",
            "kardia_mobile": "kardia",
            "samsung_health": "samsung",
        }

    def resolve_source(self, source: str | None = None) -> str:
        key = (source or os.getenv(self.source_env_var, "apple_watch")).strip().lower()
        return self._aliases.get(key, key)

    def get_creator(self, source: str | None = None) -> EcgExtractorCreatorInterface:
        resolved_source = self.resolve_source(source)
        creator = self._creators.get(resolved_source)
        if creator is None:
            supported = ", ".join(sorted(self._creators.keys()))
            raise ValueError(
                f"Fuente de ECG no soportada: {resolved_source}. Soportadas: {supported}"
            )
        return creator

    def create(self, source: str | None = None) -> EcgExtractorInterface:
        return self.get_creator(source).create()