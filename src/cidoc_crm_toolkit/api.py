"""FastAPI application exposing CIDOC CRM graph functionality."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status

from .enums import CRMEntityType, CRMPropertyType
from .exceptions import (
    EntityAlreadyExists,
    EntityNotFound,
    RelationshipAlreadyExists,
    RelationshipNotFound,
)
from .models import CRMEntity, CRMRelationship
from .repository import GraphRepository, InMemoryGraphRepository

app = FastAPI(
    title="CIDOC CRM Toolkit API",
    description="JSON API for working with CIDOC CRM entities and relationships",
    version="0.1.0",
)

_repository = InMemoryGraphRepository()


def get_repository() -> GraphRepository:
    """Dependency returning the singleton in-memory repository."""

    return _repository


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Return basic health information."""

    return {"status": "ok"}


@app.post("/entities", response_model=CRMEntity, status_code=status.HTTP_201_CREATED, tags=["entities"])
def create_entity(
    entity: CRMEntity,
    repository: Annotated[GraphRepository, Depends(get_repository)],
) -> CRMEntity:
    try:
        return repository.create_entity(entity)
    except EntityAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.put("/entities/{entity_id}", response_model=CRMEntity, tags=["entities"])
def upsert_entity(
    entity_id: str,
    entity: CRMEntity,
    repository: Annotated[GraphRepository, Depends(get_repository)],
) -> CRMEntity:
    if entity.id != entity_id:
        entity = entity.model_copy(update={"id": entity_id})
    return repository.upsert_entity(entity)


@app.get("/entities", response_model=list[CRMEntity], tags=["entities"])
def list_entities(
    repository: Annotated[GraphRepository, Depends(get_repository)],
    entity_type: Optional[str] = Query(
        default=None,
        description="Filter results by CIDOC CRM entity type (e.g. E39_Actor).",
    ),
) -> list[CRMEntity]:
    entity_type_enum: Optional[CRMEntityType] = None
    if entity_type:
        try:
            entity_type_enum = CRMEntityType.from_any(entity_type)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return repository.list_entities(entity_type_enum)


@app.get("/entities/{entity_id}", response_model=CRMEntity, tags=["entities"])
def get_entity(
    entity_id: str,
    repository: Annotated[GraphRepository, Depends(get_repository)],
) -> CRMEntity:
    try:
        return repository.get_entity(entity_id)
    except EntityNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.delete("/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["entities"])
def delete_entity(
    entity_id: str,
    repository: Annotated[GraphRepository, Depends(get_repository)],
) -> None:
    try:
        repository.delete_entity(entity_id)
    except EntityNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post(
    "/relationships",
    response_model=CRMRelationship,
    status_code=status.HTTP_201_CREATED,
    tags=["relationships"],
)
def create_relationship(
    relationship: CRMRelationship,
    repository: Annotated[GraphRepository, Depends(get_repository)],
) -> CRMRelationship:
    try:
        return repository.create_relationship(relationship)
    except (EntityNotFound, RelationshipAlreadyExists) as exc:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(exc, EntityNotFound) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@app.get("/relationships", response_model=list[CRMRelationship], tags=["relationships"])
def list_relationships(
    repository: Annotated[GraphRepository, Depends(get_repository)],
    source_id: Optional[str] = Query(default=None, description="Filter by source entity identifier."),
    target_id: Optional[str] = Query(default=None, description="Filter by target entity identifier."),
    property_type: Optional[str] = Query(
        default=None, description="Filter by CRM property type (e.g. P11_had_participant)."
    ),
) -> list[CRMRelationship]:
    property_type_enum: Optional[CRMPropertyType] = None
    if property_type:
        try:
            property_type_enum = CRMPropertyType.from_any(property_type)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return repository.list_relationships(
        source_id=source_id, target_id=target_id, property_type=property_type_enum
    )


@app.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["relationships"])
def delete_relationship(
    relationship_id: str,
    repository: Annotated[GraphRepository, Depends(get_repository)],
) -> None:
    try:
        repository.delete_relationship(relationship_id)
    except RelationshipNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.get(
    "/entities/{entity_id}/relationships",
    response_model=list[CRMRelationship],
    tags=["entities", "relationships"],
)
def get_entity_relationships(
    entity_id: str,
    repository: Annotated[GraphRepository, Depends(get_repository)],
) -> list[CRMRelationship]:
    try:
        repository.get_entity(entity_id)
    except EntityNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return repository.list_relationships(source_id=entity_id)
