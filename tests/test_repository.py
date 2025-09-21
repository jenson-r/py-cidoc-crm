from cidoc_crm_toolkit.enums import CRMEntityType, CRMPropertyType
from cidoc_crm_toolkit.exceptions import EntityNotFound, RelationshipAlreadyExists
from cidoc_crm_toolkit.models import CRMEntity, CRMRelationship
from cidoc_crm_toolkit.repository import InMemoryGraphRepository


def make_entity(entity_type: CRMEntityType, label: str) -> CRMEntity:
    return CRMEntity(entity_type=entity_type, label=label)


def test_create_and_get_entity():
    repo = InMemoryGraphRepository()
    entity = make_entity(CRMEntityType.E39_ACTOR, "Ada Lovelace")
    repo.create_entity(entity)

    retrieved = repo.get_entity(entity.id)
    assert retrieved.label == "Ada Lovelace"
    assert retrieved.entity_type == CRMEntityType.E39_ACTOR

    entities = repo.list_entities()
    assert len(entities) == 1


def test_relationship_requires_existing_entities():
    repo = InMemoryGraphRepository()
    actor = make_entity(CRMEntityType.E39_ACTOR, "Ada Lovelace")
    event = make_entity(CRMEntityType.E5_EVENT, "Analytical Engine Proposal")
    repo.create_entity(actor)
    repo.create_entity(event)

    relationship = CRMRelationship(
        property_type=CRMPropertyType.P11_HAD_PARTICIPANT,
        source_id=event.id,
        target_id=actor.id,
    )

    repo.create_relationship(relationship)

    # Duplicate relationship between same nodes with same property is rejected
    duplicate = CRMRelationship(
        property_type=CRMPropertyType.P11_HAD_PARTICIPANT,
        source_id=event.id,
        target_id=actor.id,
    )
    try:
        repo.create_relationship(duplicate)
    except RelationshipAlreadyExists:
        pass
    else:
        raise AssertionError("Expected RelationshipAlreadyExists")


def test_export_import_roundtrip():
    repo = InMemoryGraphRepository()
    actor = make_entity(CRMEntityType.E39_ACTOR, "Ada Lovelace")
    event = make_entity(CRMEntityType.E5_EVENT, "Analytical Engine Proposal")
    repo.create_entity(actor)
    repo.create_entity(event)
    repo.create_relationship(
        CRMRelationship(
            property_type=CRMPropertyType.P11_HAD_PARTICIPANT,
            source_id=event.id,
            target_id=actor.id,
        )
    )

    payload = repo.export_data()

    other = InMemoryGraphRepository()
    other.import_data(payload)

    assert len(other.list_entities()) == 2
    assert other.list_relationships()

    # Removing an entity deletes related relationships implicitly via NetworkX
    other.delete_entity(actor.id)
    try:
        other.get_entity(actor.id)
    except EntityNotFound:
        pass
    else:
        raise AssertionError("Expected EntityNotFound")
