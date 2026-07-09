from typing import Any, Dict, List

from sqlalchemy import select

from models.entity.ecg_entity import EcgEntity

from .base_repository import GenericRepository
from .sqlalchemy_models import EcgORM


class EcgRepository(GenericRepository[EcgORM, EcgEntity]):
    """Repositorio específico de ECG.

    Hereda CRUD base y agrega consultas propias del agregado ECG.
    """

    def __init__(self, session_factory: Any) -> None:
        super().__init__(session_factory, EcgORM, EcgEntity)

    def find_by_patient_id(self, patient_id: int) -> List[Dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(EcgORM)
                .where(EcgORM.patientId == int(patient_id))
                .order_by(EcgORM.id.asc())
            ).all()
            return [self._to_dict(row) for row in rows]
