"""Graph repository abstractions and in-memory implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional

import networkx as nx

from .enums import CRMEntityType, CRMPropertyType
from .exceptions import (
    CRMError,
    EntityAlreadyExists,
    EntityNotFound,
    RelationshipAlreadyExists,
    RelationshipNotFound,
)
from .models import CRMEntity, CRMRelationship


class GraphRepository(ABC):
    """Abstract graph repository for storing CIDOC CRM entities and relationships."""

    @abstractmethod
    def create_entity(self, entity: CRMEntity) -> CRMEntity:
        raise NotImplementedError

    @abstractmethod
    def upsert_entity(self, entity: CRMEntity) -> CRMEntity:
        raise NotImplementedError

    @abstractmethod
    def get_entity(self, entity_id: str) -> CRMEntity:
        raise NotImplementedError

    @abstractmethod
    def delete_entity(self, entity_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_entities(self, entity_type: Optional[CRMEntityType] = None) -> List[CRMEntity]:
        raise NotImplementedError

    @abstractmethod
    def create_relationship(self, relationship: CRMRelationship) -> CRMRelationship:
        raise NotImplementedError

    @abstractmethod
    def list_relationships(
        self,
        *,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        property_type: Optional[CRMPropertyType] = None,
    ) -> List[CRMRelationship]:
        raise NotImplementedError

    @abstractmethod
    def delete_relationship(self, relationship_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def export_data(self) -> Dict[str, List[Dict[str, object]]]:
        raise NotImplementedError

    @abstractmethod
    def import_data(self, payload: Dict[str, Iterable[Dict[str, object]]]) -> None:
        raise NotImplementedError


class InMemoryGraphRepository(GraphRepository):
    """Simple in-memory graph repository backed by NetworkX."""

    def __init__(self) -> None:
        self._graph = nx.MultiDiGraph()

    # ------------------------------------------------------------------
    # entity operations
    # ------------------------------------------------------------------
    def create_entity(self, entity: CRMEntity) -> CRMEntity:
        if entity.id in self._graph:
            raise EntityAlreadyExists(f"Entity {entity.id} already exists")
        self._graph.add_node(entity.id, entity=entity.model_dump(mode="json"))
        return entity

    def upsert_entity(self, entity: CRMEntity) -> CRMEntity:
        self._graph.add_node(entity.id, entity=entity.model_dump(mode="json"))
        return entity

    def get_entity(self, entity_id: str) -> CRMEntity:
        try:
            data = self._graph.nodes[entity_id]["entity"]
        except KeyError as exc:
            raise EntityNotFound(f"Entity {entity_id} not found") from exc
        return CRMEntity.model_validate(data)

    def delete_entity(self, entity_id: str) -> None:
        if entity_id not in self._graph:
            raise EntityNotFound(f"Entity {entity_id} not found")
        self._graph.remove_node(entity_id)

    def list_entities(self, entity_type: Optional[CRMEntityType] = None) -> List[CRMEntity]:
        results: List[CRMEntity] = []
        for node_id, attributes in self._graph.nodes(data=True):
            entity = CRMEntity.model_validate(attributes["entity"])
            if entity_type and entity.entity_type != entity_type:
                continue
            results.append(entity)
        return sorted(results, key=lambda e: (e.entity_type.value, e.label))

    # ------------------------------------------------------------------
    # relationship operations
    # ------------------------------------------------------------------
    def _relationships_iter(self):
        for source, target, key, data in self._graph.edges(data=True, keys=True):
            relationship_dict = data.get("relationship")
            if not relationship_dict:
                continue
            relationship = CRMRelationship.model_validate(relationship_dict)
            yield source, target, key, relationship

    def _ensure_entity_exists(self, entity_id: str) -> None:
        if entity_id not in self._graph:
            raise EntityNotFound(f"Entity {entity_id} not found")

    def create_relationship(self, relationship: CRMRelationship) -> CRMRelationship:
        self._ensure_entity_exists(relationship.source_id)
        self._ensure_entity_exists(relationship.target_id)

        for _, _, _, existing in self._relationships_iter():
            if (
                existing.id == relationship.id
                or (
                    existing.source_id == relationship.source_id
                    and existing.target_id == relationship.target_id
                    and existing.property_type == relationship.property_type
                )
            ):
                raise RelationshipAlreadyExists(
                    "Relationship already exists between the provided entities with the same property."
                )

        self._graph.add_edge(
            relationship.source_id,
            relationship.target_id,
            key=relationship.id,
            relationship=relationship.model_dump(mode="json"),
        )
        return relationship

    def list_relationships(
        self,
        *,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        property_type: Optional[CRMPropertyType] = None,
    ) -> List[CRMRelationship]:
        matches: List[CRMRelationship] = []
        for _, _, _, relationship in self._relationships_iter():
            if source_id and relationship.source_id != source_id:
                continue
            if target_id and relationship.target_id != target_id:
                continue
            if property_type and relationship.property_type != property_type:
                continue
            matches.append(relationship)
        return sorted(matches, key=lambda rel: (rel.property_type.value, rel.source_id, rel.target_id))

    def delete_relationship(self, relationship_id: str) -> None:
        for source, target, key, relationship in self._relationships_iter():
            if relationship.id == relationship_id:
                self._graph.remove_edge(source, target, key)
                return
        raise RelationshipNotFound(f"Relationship {relationship_id} not found")

    # ------------------------------------------------------------------
    # serialization helpers
    # ------------------------------------------------------------------
    def export_data(self) -> Dict[str, List[Dict[str, object]]]:
        entities = [
            CRMEntity.model_validate(attrs["entity"]).model_dump(mode="json")
            for _, attrs in self._graph.nodes(data=True)
        ]
        relationships = [
            CRMRelationship.model_validate(data["relationship"]).model_dump(mode="json")
            for _, _, data in self._graph.edges(data=True)
            if "relationship" in data
        ]
        return {"entities": entities, "relationships": relationships}

    def import_data(self, payload: Dict[str, Iterable[Dict[str, object]]]) -> None:
        self._graph.clear()
        for entity_payload in payload.get("entities", []) or []:
            entity = CRMEntity.model_validate(entity_payload)
            self._graph.add_node(entity.id, entity=entity.model_dump(mode="json"))
        for relationship_payload in payload.get("relationships", []) or []:
            relationship = CRMRelationship.model_validate(relationship_payload)
            if relationship.source_id not in self._graph or relationship.target_id not in self._graph:
                raise CRMError(
                    "Relationship references missing entities; ensure entities are imported before relationships."
                )
            self._graph.add_edge(
                relationship.source_id,
                relationship.target_id,
                key=relationship.id,
                relationship=relationship.model_dump(mode="json"),
            )
