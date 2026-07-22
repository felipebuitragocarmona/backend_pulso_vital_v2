from typing import Any, Dict, List, Tuple

from sqlalchemy import func, select

from models.entity.category_entity import CategoryEntity

from .base_repository import GenericRepository
from .sqlalchemy_models import CategoryORM


class CategoryRepository(GenericRepository[CategoryORM, CategoryEntity]):
    """Repositorio específico de categorías.

    Hereda CRUD base y paginación genérica. La relación reflexiva
    (category_parent_id) se resuelve mediante consultas propias del servicio.
    """

    def __init__(self, session_factory: Any) -> None:
        super().__init__(session_factory, CategoryORM, CategoryEntity)

    def find_by_parent_id(self, parent_id: int) -> List[Dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(CategoryORM)
                .where(CategoryORM.category_parent_id == int(parent_id))
                .order_by(CategoryORM.id.asc())
            ).all()
            return [self._to_dict(row) for row in rows]

    def find_roots(self) -> List[Dict[str, Any]]:
        """Retorna solo las categorías raíz (sin category_parent_id)."""
        with self.session_factory() as session:
            rows = session.scalars(
                select(CategoryORM)
                .where(CategoryORM.category_parent_id.is_(None))
                .order_by(CategoryORM.id.asc())
            ).all()
            return [self._to_dict(row) for row in rows]

    def find_roots_paged(self, page: int, page_size: int) -> Tuple[List[Dict[str, Any]], int]:
        """Retorna una página de categorías raíz (sin category_parent_id) y el total."""
        with self.session_factory() as session:
            base_query = select(CategoryORM).where(CategoryORM.category_parent_id.is_(None))
            total: int = (
                session.scalar(select(func.count()).select_from(base_query.subquery())) or 0
            )
            offset = (page - 1) * page_size
            rows = session.scalars(
                base_query.order_by(CategoryORM.id.asc()).offset(offset).limit(page_size)
            ).all()
            return [self._to_dict(row) for row in rows], total

