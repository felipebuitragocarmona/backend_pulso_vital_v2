from abc import ABC, abstractmethod

from business.extraction.ecg_extractor_interface import EcgExtractorInterface


class EcgExtractorCreatorInterface(ABC):
    """Interfaz Factory Method para crear extractores de ECG."""

    @abstractmethod
    def create(self) -> EcgExtractorInterface:
        pass
