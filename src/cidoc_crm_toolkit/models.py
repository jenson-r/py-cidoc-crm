"""Pydantic models representing CIDOC CRM concepts."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import CRMEntityType, CRMPropertyType


class CRMIdentifier(BaseModel):
    """Identifier associated with a CIDOC CRM entity."""

    type: Optional[str] = Field(
        default=None,
        description="Type of identifier, e.g. inventory number or external authority."
    )
    value: str = Field(..., description="Identifier value")
    issued_by: Optional[str] = Field(
        default=None, description="Authority or institution responsible for the identifier."
    )

    model_config = ConfigDict(extra="forbid")


class TimeSpan(BaseModel):
    """Represents CIDOC CRM E52 Time-Span values for temporal entities."""

    begin_of_begin: Optional[datetime] = Field(
        default=None, description="Lower bound for the start of the timespan."
    )
    end_of_end: Optional[datetime] = Field(
        default=None, description="Upper bound for the end of the timespan."
    )
    label: Optional[str] = Field(default=None, description="Human readable label for the timespan.")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_range(self) -> "TimeSpan":
        if self.begin_of_begin and self.end_of_end:
            if self.begin_of_begin > self.end_of_end:
                raise ValueError("begin_of_begin must be before end_of_end")
        return self


class CRMEntity(BaseModel):
    """Base model for CIDOC CRM entities."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Globally unique identifier for the entity."
    )
    entity_type: CRMEntityType = Field(..., description="CIDOC CRM class of the entity.")
    label: str = Field(..., description="Primary human-readable label for the entity.")
    description: Optional[str] = Field(default=None, description="Optional descriptive text.")
    identifiers: List[CRMIdentifier] = Field(
        default_factory=list, description="Collection of identifiers associated with the entity."
    )
    types: List[str] = Field(
        default_factory=list,
        description="Additional rdf:type like designations complementing the CRM class.",
    )
    time_span: Optional[TimeSpan] = Field(
        default=None,
        description="Temporal information relevant to temporal entities (e.g. E5 Event).",
    )
    data: Dict[str, object] = Field(
        default_factory=dict,
        description="Arbitrary extensible payload to attach domain specific attributes.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("entity_type", mode="before")
    @classmethod
    def parse_entity_type(cls, value: str | CRMEntityType) -> CRMEntityType:
        if isinstance(value, CRMEntityType):
            return value
        return CRMEntityType.from_any(str(value))


class CRMRelationship(BaseModel):
    """Model for CIDOC CRM properties connecting two entities."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Identifier for the relationship edge."
    )
    property_type: CRMPropertyType = Field(..., description="CIDOC CRM property type.")
    source_id: str = Field(..., description="Identifier of the subject entity.")
    target_id: str = Field(..., description="Identifier of the object entity.")
    description: Optional[str] = Field(default=None, description="Optional note about the relation.")
    data: Dict[str, object] = Field(
        default_factory=dict, description="Extensible property payload for custom applications."
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("property_type", mode="before")
    @classmethod
    def parse_property_type(cls, value: str | CRMPropertyType) -> CRMPropertyType:
        if isinstance(value, CRMPropertyType):
            return value
        return CRMPropertyType.from_any(str(value))
