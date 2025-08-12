"""
Database-related utility functions.
"""

from __future__ import annotations

from typing import Any
from typing import Type
from typing import TypeVar

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import Base


ModelType = TypeVar("ModelType", bound=Base)


async def upsert_entity(
    db: AsyncSession,
    entity_model: Type[ModelType],
    name: str,
    name_field: str = "name",
) -> ModelType:
    """Upsert a single entity into the database and return the entity."""
    # Perform upsert (insert if not exists)
    insert_stmt = (
        insert(entity_model).values({name_field: name}).on_conflict_do_nothing()
    )
    await db.execute(insert_stmt)

    # Fetch the entity and return it
    column: Column[Any] = getattr(entity_model, name_field)
    select_stmt = select(entity_model).where(column == name)
    result = await db.execute(select_stmt)

    return result.scalar_one()


async def upsert_entities(
    db: AsyncSession,
    entity_model: Type[ModelType],
    names: list[str],
    name_field: str = "name",
) -> list[ModelType]:
    """Upsert multiple entities, ensuring they exist and returning them."""
    entities: list[ModelType] = []

    # Ensure the name_field is valid in the model
    if name_field not in entity_model.__table__.columns:
        err_msg = f"Invalid column name for model {entity_model.__name__}: {name_field}"
        raise ValueError(err_msg)

    # Upsert entities one by one and collect results
    for name in names:
        try:
            entity = await upsert_entity(db, entity_model, name, name_field)
            entities.append(entity)
        except IntegrityError as e:  # noqa: PERF203
            exc_msg = (
                f"Integrity error on {name} with model {entity_model.__name__}: {e}"
            )
            raise ValueError(exc_msg) from e

    return entities
