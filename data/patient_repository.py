from typing import Any, Dict, List

from sqlalchemy import select

from models.entity.patient_entity import PatientEntity

from .base_repository import GenericRepository
from .sqlalchemy_models import PatientORM


class PatientRepository(GenericRepository[PatientORM, PatientEntity]):
    """Repositorio específico de pacientes.

    Hereda CRUD base desde GenericRepository. Aquí se agregan consultas propias
    del agregado Patient cuando sean necesarias.
    """

    def __init__(self, session_factory: Any) -> None:
        super().__init__(session_factory, PatientORM, PatientEntity)

    def find_by_name_contains(self, text: str) -> List[Dict[str, Any]]:
        """Ejemplo de método personalizado que no pertenece al repositorio genérico."""

        with self.session_factory() as session:
            rows = session.scalars(
                select(PatientORM)
                .where(PatientORM.fullName.ilike(f"%{text}%"))
                .order_by(PatientORM.id.asc())
            ).all()
            return [self._to_dict(row) for row in rows]
