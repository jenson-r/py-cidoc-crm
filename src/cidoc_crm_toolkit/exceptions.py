"""Custom exceptions for the CIDOC CRM toolkit."""

from __future__ import annotations


class CRMError(Exception):
    """Base exception for toolkit errors."""


class EntityAlreadyExists(CRMError):
    """Raised when attempting to create an entity that already exists."""


class EntityNotFound(CRMError):
    """Raised when the requested entity cannot be found."""


class RelationshipAlreadyExists(CRMError):
    """Raised when attempting to add a duplicate relationship."""


class RelationshipNotFound(CRMError):
    """Raised when a relationship could not be located."""
