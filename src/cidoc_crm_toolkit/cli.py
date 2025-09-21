"""Command line utilities for the CIDOC CRM toolkit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Optional

import typer

from .enums import CRMEntityType, CRMPropertyType
from .models import CRMEntity, CRMIdentifier, CRMRelationship
from .repository import InMemoryGraphRepository

app = typer.Typer(help="Utilities for working with CIDOC CRM graphs")


def _load_repository(store: Optional[Path]) -> InMemoryGraphRepository:
    repo = InMemoryGraphRepository()
    if store is None:
        return repo
    if store.exists():
        with store.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        repo.import_data(payload)
    return repo


def _save_repository(repo: InMemoryGraphRepository, store: Optional[Path]) -> None:
    if store is None:
        return
    payload = repo.export_data()
    with store.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def _parse_identifiers(values: Iterable[str]) -> list[CRMIdentifier]:
    identifiers: list[CRMIdentifier] = []
    for raw in values:
        if "=" in raw:
            type_part, value = raw.split("=", 1)
            identifier_type = type_part.strip() or None
            identifiers.append(CRMIdentifier(type=identifier_type, value=value.strip()))
        else:
            identifiers.append(CRMIdentifier(value=raw.strip()))
    return identifiers


@app.command("entity-add")
def entity_add(
    entity_type: str = typer.Argument(..., help="CIDOC CRM class, e.g. E39_Actor"),
    label: str = typer.Option(..., "--label", help="Primary label for the entity"),
    description: Optional[str] = typer.Option(None, "--description", help="Optional description"),
    identifier: Optional[list[str]] = typer.Option(
        None,
        "--identifier",
        help="Identifier definition (value or type=value). Repeatable option.",
    ),
    type_tag: Optional[list[str]] = typer.Option(
        None,
        "--type-tag",
        help="Additional rdf:type like information. Repeat option for multiple values.",
    ),
    entity_id: Optional[str] = typer.Option(
        None, "--id", help="Optional custom identifier. Defaults to generated UUID."
    ),
    store: Optional[Path] = typer.Option(
        None, "--store", help="Persist graph state to the given JSON file"
    ),
) -> None:
    repo = _load_repository(store)
    payload = dict(
        entity_type=CRMEntityType.from_any(entity_type),
        label=label,
        description=description,
        identifiers=_parse_identifiers(identifier or []),
        types=list(type_tag or []),
    )
    if entity_id:
        payload["id"] = entity_id
    entity = CRMEntity(**payload)
    repo.create_entity(entity)
    _save_repository(repo, store)
    typer.echo(json.dumps(entity.model_dump(mode="json"), indent=2))


@app.command("entity-list")
def entity_list(
    entity_type: Optional[str] = typer.Option(
        None, "--entity-type", help="Optional filter by CIDOC CRM class"
    ),
    store: Optional[Path] = typer.Option(
        None, "--store", help="Read graph state from the given JSON file"
    ),
) -> None:
    repo = _load_repository(store)
    entity_type_enum = CRMEntityType.from_any(entity_type) if entity_type else None
    entities = repo.list_entities(entity_type_enum)
    typer.echo(json.dumps([entity.model_dump(mode="json") for entity in entities], indent=2))


@app.command("relationship-add")
def relationship_add(
    property_type: str = typer.Argument(..., help="CIDOC CRM property, e.g. P11_had_participant"),
    source: str = typer.Option(..., "--source", help="Identifier of the subject entity"),
    target: str = typer.Option(..., "--target", help="Identifier of the object entity"),
    description: Optional[str] = typer.Option(None, "--description", help="Optional note"),
    relationship_id: Optional[str] = typer.Option(None, "--id", help="Optional relationship identifier"),
    store: Optional[Path] = typer.Option(
        None, "--store", help="Persist graph state to the given JSON file"
    ),
) -> None:
    repo = _load_repository(store)
    payload = dict(
        property_type=CRMPropertyType.from_any(property_type),
        source_id=source,
        target_id=target,
        description=description,
    )
    if relationship_id:
        payload["id"] = relationship_id
    relationship = CRMRelationship(**payload)
    repo.create_relationship(relationship)
    _save_repository(repo, store)
    typer.echo(json.dumps(relationship.model_dump(mode="json"), indent=2))


@app.command("relationship-list")
def relationship_list(
    source: Optional[str] = typer.Option(None, "--source", help="Filter by subject entity"),
    target: Optional[str] = typer.Option(None, "--target", help="Filter by object entity"),
    property_type: Optional[str] = typer.Option(
        None, "--property-type", help="Filter by property type"
    ),
    store: Optional[Path] = typer.Option(
        None, "--store", help="Read graph state from the given JSON file"
    ),
) -> None:
    repo = _load_repository(store)
    property_enum = CRMPropertyType.from_any(property_type) if property_type else None
    relationships = repo.list_relationships(
        source_id=source, target_id=target, property_type=property_enum
    )
    typer.echo(
        json.dumps([relationship.model_dump(mode="json") for relationship in relationships], indent=2)
    )


@app.command()
def export(
    store: Optional[Path] = typer.Option(
        None, "--store", help="Read graph state from the given JSON file"
    ),
    output: typer.FileTextWrite = typer.Option(sys.stdout, "--output", help="Destination file"),
) -> None:
    repo = _load_repository(store)
    payload = repo.export_data()
    json.dump(payload, output, indent=2)
    output.write("\n")


@app.command()
def import_data(
    store: Optional[Path] = typer.Option(
        None, "--store", help="Persist imported graph to the given JSON file"
    ),
    source: typer.FileText = typer.Option(sys.stdin, "--source", help="Input JSON document"),
) -> None:
    payload = json.load(source)
    repo = InMemoryGraphRepository()
    repo.import_data(payload)
    _save_repository(repo, store)
    typer.echo("Imported graph with " + str(len(payload.get("entities", []))) + " entities")


if __name__ == "__main__":
    app()
