import logging
import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

from .category_repository import CategoryRepository
from .database import Database
from .ecg_repository import EcgRepository
from .patient_repository import PatientRepository

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class RepositoryProvider:
    """Contenedor de repositorios de la aplicación.

    No es una interfaz gigante. Solo agrupa repositorios concretos que comparten
    la misma configuración de base de datos.
    """

    database: Database
    patients: PatientRepository
    ecgs: EcgRepository
    categories: CategoryRepository


class RelationalRepositoryFactory:
    """Factory Method para construir repositorios sobre bases relacionales."""

    def __init__(self, database_url: str | None = None, sqlite_path: str | None = None) -> None:
        self.database = Database(database_url=database_url, sqlite_path=sqlite_path)

    def create_repositories(self) -> RepositoryProvider:
        logger.info("Creating relational repositories -> %s", self.database.database_url)
        return RepositoryProvider(
            database=self.database,
            patients=PatientRepository(self.database.SessionLocal),
            ecgs=EcgRepository(self.database.SessionLocal),
            categories=CategoryRepository(self.database.SessionLocal),
        )


FACTORIES: dict[str, type[RelationalRepositoryFactory]] = {
    "relational": RelationalRepositoryFactory,
    "sqlalchemy": RelationalRepositoryFactory,
    "sqlite": RelationalRepositoryFactory,
    "postgres": RelationalRepositoryFactory,
    "postgresql": RelationalRepositoryFactory,
    "mysql": RelationalRepositoryFactory,
}

REQUIRES_DATABASE_URL = {"postgres", "postgresql", "mysql"}


def get_factory(repo_type: str | None = None) -> RelationalRepositoryFactory:
    key = (repo_type or os.getenv("REPO_TYPE", "sqlite")).lower()

    if key in REQUIRES_DATABASE_URL and not os.getenv("DATABASE_URL"):
        raise ValueError(
            f"REPO_TYPE={key} requiere DATABASE_URL. "
            "Ejemplos: "
            "postgresql+psycopg://user:pass@localhost:5432/medical_ecg | "
            "mysql+pymysql://user:pass@localhost:3306/medical_ecg"
        )

    factory_class = FACTORIES.get(key)
    if factory_class is None:
        raise ValueError(
            f"REPO_TYPE '{key}' no soportado. "
            f"Opciones relacionales: {', '.join(FACTORIES.keys())}"
        )

    return factory_class()


@lru_cache(maxsize=1)
def get_repositories() -> RepositoryProvider:
    return get_factory().create_repositories()

