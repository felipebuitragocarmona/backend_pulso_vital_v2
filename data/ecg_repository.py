from typing import Any, Dict, List, Tuple

from sqlalchemy import func, select

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

    def find_by_patient_id_paged(
        self, patient_id: int, page: int, page_size: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retorna una página de ECGs de un paciente y el total de registros."""
        with self.session_factory() as session:
            base_query = select(EcgORM).where(EcgORM.patientId == int(patient_id))
            total: int = (
                session.scalar(select(func.count()).select_from(base_query.subquery())) or 0
            )
            offset = (page - 1) * page_size
            rows = session.scalars(
                base_query.order_by(EcgORM.id.asc()).offset(offset).limit(page_size)
            ).all()
            return [self._to_dict(row) for row in rows], total
