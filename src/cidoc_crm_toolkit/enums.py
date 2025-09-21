"""Enumerations for CIDOC CRM entity and property types."""

from __future__ import annotations

from enum import Enum


class CRMEntityType(str, Enum):
    """Subset of CIDOC CRM entity types supported by the toolkit."""

    E2_TEMPORAL_ENTITY = "E2_Temporal_Entity"
    E5_EVENT = "E5_Event"
    E39_ACTOR = "E39_Actor"
    E53_PLACE = "E53_Place"
    E55_TYPE = "E55_Type"
    E7_ACTIVITY = "E7_Activity"

    @classmethod
    def from_any(cls, value: str) -> "CRMEntityType":
        """Parse a string into a :class:`CRMEntityType` ignoring case and underscores."""

        normalized = value.strip().lower().replace(" ", "_")
        for member in cls:
            if member.value.lower() == normalized or member.name.lower() == normalized:
                return member
        raise ValueError(f"Unknown CRM entity type: {value}")


class CRMPropertyType(str, Enum):
    """Subset of CIDOC CRM property types supported by the toolkit."""

    P1_IS_IDENTIFIED_BY = "P1_is_identified_by"
    P7_TOOK_PLACE_AT = "P7_took_place_at"
    P11_HAD_PARTICIPANT = "P11_had_participant"
    P14_CARRIED_OUT_BY = "P14_carried_out_by"

    @classmethod
    def from_any(cls, value: str) -> "CRMPropertyType":
        """Parse a string into a :class:`CRMPropertyType` ignoring case and underscores."""

        normalized = value.strip().lower().replace(" ", "_")
        for member in cls:
            if member.value.lower() == normalized or member.name.lower() == normalized:
                return member
        raise ValueError(f"Unknown CRM property type: {value}")
