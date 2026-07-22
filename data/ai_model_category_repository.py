from typing import Any, Dict, List, Tuple

from sqlalchemy import func, select

from models.entity.ai_model_category_entity import AIModelCategoryEntity

from .base_repository import GenericRepository
from .sqlalchemy_models import AIModelCategoryORM


class AIModelCategoryRepository(GenericRepository[AIModelCategoryORM, AIModelCategoryEntity]):
    def __init__(self, session_factory: Any) -> None:
        super().__init__(session_factory, AIModelCategoryORM, AIModelCategoryEntity)

    def find_by_parent_id(self, parent_id: int) -> List[Dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(AIModelCategoryORM)
                .where(AIModelCategoryORM.category_parent_id == int(parent_id))
                .order_by(AIModelCategoryORM.id.asc())
            ).all()
            return [self._to_dict(row) for row in rows]

    def find_roots(self) -> List[Dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(AIModelCategoryORM)
                .where(AIModelCategoryORM.category_parent_id.is_(None))
                .order_by(AIModelCategoryORM.id.asc())
            ).all()
            return [self._to_dict(row) for row in rows]

    def find_roots_paged(self, page: int, page_size: int) -> Tuple[List[Dict[str, Any]], int]:
        with self.session_factory() as session:
            base_query = select(AIModelCategoryORM).where(AIModelCategoryORM.category_parent_id.is_(None))
            total: int = session.scalar(select(func.count()).select_from(base_query.subquery())) or 0
            offset = (page - 1) * page_size
            rows = session.scalars(
                base_query.order_by(AIModelCategoryORM.id.asc()).offset(offset).limit(page_size)
            ).all()
            return [self._to_dict(row) for row in rows], total
