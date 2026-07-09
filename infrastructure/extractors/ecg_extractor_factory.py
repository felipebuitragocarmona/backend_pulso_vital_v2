from infrastructure.extractors.apple_watch_ecg_pdf_extractor import AppleWatchEcgPdfExtractor


class EcgExtractorFactory:

    def create(self, source: str = "apple_watch"):

        if source == "apple_watch":
            return AppleWatchEcgPdfExtractor()

        raise ValueError(f"Fuente de ECG no soportada: {source}")