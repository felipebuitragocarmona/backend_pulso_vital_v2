from dataclasses import asdict, fields as dataclass_fields, is_dataclass
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ORMType = TypeVar("ORMType")
EntityType = TypeVar("EntityType")


class GenericRepository(Generic[ORMType, EntityType]):
    """Repositorio genérico para operaciones CRUD comunes.

    Es similar a la idea de un JpaRepository/CrudRepository: ofrece métodos
    reutilizables y permite que cada repositorio concreto agregue o sobrescriba
    solo lo que necesite.
    """

    def __init__(
        self,
        session_factory: Any,
        orm_model: Type[ORMType],
        entity_type: Type[EntityType],
        id_field: str = "id",
    ) -> None:
        self.session_factory = session_factory
        self.orm_model = orm_model
        self.entity_type = entity_type
        self.id_field = id_field
        self.column_names = tuple(column.name for column in orm_model.__table__.columns)
        self.entity_field_names = self._resolve_entity_field_names(entity_type)

    def _resolve_entity_field_names(self, entity_type: Type[EntityType]) -> tuple[str, ...]:
        if is_dataclass(entity_type):
            return tuple(field.name for field in dataclass_fields(entity_type))
        return self.column_names

    def _to_dict(self, row: ORMType) -> Dict[str, Any]:
        payload = {
            field_name: getattr(row, field_name)
            for field_name in self.entity_field_names
            if hasattr(row, field_name)
        }

        if is_dataclass(self.entity_type):
            return asdict(self.entity_type(**payload))

        return payload

    def _assign_values(self, row: ORMType, data: Dict[str, Any], include_id: bool = False) -> None:
        for key, value in data.items():
            if key == self.id_field and not include_id:
                continue
            if key in self.column_names:
                setattr(row, key, value)

    def find_all(self) -> List[Dict[str, Any]]:
        with self.session_factory() as session:
            order_column = getattr(self.orm_model, self.id_field)
            rows = session.scalars(select(self.orm_model).order_by(order_column.asc())).all()
            return [self._to_dict(row) for row in rows]

    def find_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        with self.session_factory() as session:
            row = session.get(self.orm_model, int(entity_id))
            if row is None:
                return None
            return self._to_dict(row)

    def exists_by_id(self, entity_id: int) -> bool:
        return self.find_by_id(entity_id) is not None

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un registro y retorna el dato persistido.

        Si el diccionario trae id, se ignora por defecto para permitir que la
        base de datos relacional genere la llave primaria.
        """

        with self.session_factory.begin() as session:
            assert isinstance(session, Session)
            row = self.orm_model()
            self._assign_values(row, data, include_id=False)
            session.add(row)
            session.flush()
            session.refresh(row)
            return self._to_dict(row)

    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.session_factory.begin() as session:
            assert isinstance(session, Session)
            row = session.get(self.orm_model, int(entity_id))
            if row is None:
                return None

            self._assign_values(row, data, include_id=False)
            session.flush()
            session.refresh(row)
            return self._to_dict(row)

    def delete_by_id(self, entity_id: int) -> bool:
        with self.session_factory.begin() as session:
            assert isinstance(session, Session)
            row = session.get(self.orm_model, int(entity_id))
            if row is None:
                return False
            session.delete(row)
            return True

    def find_by_fields(self, **filters: Any) -> List[Dict[str, Any]]:
        """Consulta genérica por igualdad para campos existentes del modelo."""

        valid_filters = {
            key: value
            for key, value in filters.items()
            if key in self.column_names
        }

        with self.session_factory() as session:
            statement = select(self.orm_model)
            for key, value in valid_filters.items():
                statement = statement.where(getattr(self.orm_model, key) == value)

            order_column = getattr(self.orm_model, self.id_field)
            rows = session.scalars(statement.order_by(order_column.asc())).all()
            return [self._to_dict(row) for row in rows]
