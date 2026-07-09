import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .sqlalchemy_models import Base

load_dotenv()


class Database:
    """Configuración de la base de datos relacional.

    SQLite es la opción inicial por defecto, pero la misma capa funciona con
    PostgreSQL o MySQL cambiando DATABASE_URL.
    """

    def __init__(self, database_url: str | None = None, sqlite_path: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL") or self._sqlite_url(sqlite_path)
        self.engine = self._create_engine(self.database_url)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        Base.metadata.create_all(bind=self.engine)

    def _sqlite_url(self, sqlite_path: str | None = None) -> str:
        file_path = Path(sqlite_path or os.getenv("SQLITE_PATH", "medical_ecg.db")).as_posix()
        return f"sqlite:///{file_path}"

    def _create_engine(self, database_url: str) -> Engine:
        connect_args: dict[str, Any] = {}
        if database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        engine = create_engine(
            database_url,
            future=True,
            connect_args=connect_args,
        )

        if engine.dialect.name == "sqlite":
            self._enable_sqlite_foreign_keys(engine)

        return engine

    def _enable_sqlite_foreign_keys(self, engine: Engine) -> None:
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
