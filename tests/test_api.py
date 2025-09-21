from fastapi.testclient import TestClient

from cidoc_crm_toolkit import api
from cidoc_crm_toolkit.enums import CRMEntityType, CRMPropertyType
from cidoc_crm_toolkit.repository import InMemoryGraphRepository


def get_client_with_repo():
    repo = InMemoryGraphRepository()

    def override_repo():
        return repo

    api.app.dependency_overrides[api.get_repository] = override_repo
    return TestClient(api.app), repo


def test_create_entity_and_relationship_via_api():
    client, repo = get_client_with_repo()

    response = client.post(
        "/entities",
        json={
            "entity_type": CRMEntityType.E39_ACTOR.value,
            "label": "Ada Lovelace",
        },
    )
    assert response.status_code == 201
    actor = response.json()

    response = client.post(
        "/entities",
        json={
            "entity_type": CRMEntityType.E5_EVENT.value,
            "label": "Analytical Engine Proposal",
        },
    )
    assert response.status_code == 201
    event = response.json()

    relationship_payload = {
        "property_type": CRMPropertyType.P11_HAD_PARTICIPANT.value,
        "source_id": event["id"],
        "target_id": actor["id"],
    }
    response = client.post("/relationships", json=relationship_payload)
    assert response.status_code == 201

    relationships = client.get("/relationships").json()
    assert len(relationships) == 1
    assert relationships[0]["source_id"] == event["id"]

    entity_relationships = client.get(f"/entities/{event['id']}/relationships").json()
    assert len(entity_relationships) == 1


def test_get_missing_entity_returns_404():
    client, repo = get_client_with_repo()
    response = client.get("/entities/non-existent")
    assert response.status_code == 404
