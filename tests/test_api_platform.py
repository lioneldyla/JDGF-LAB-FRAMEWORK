import shutil
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from jdgf_framework.api import create_app
from jdgf_framework.api_platform import ApiPlatformError, validate_api_platform

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(create_app(ROOT))


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _copy_contracts(tmp_path: Path) -> Path:
    for relative in (
        "manifests/api-platform.yaml",
        "manifests/api-platform.schema.yaml",
        "registry/api.yaml",
        "registry/api.schema.yaml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def test_api_contracts_match_implemented_routes() -> None:
    summary = validate_api_platform(ROOT)

    assert summary.version == "0.10.1"
    assert summary.lifecycle == "preview"
    assert summary.endpoint_ids == ("health", "list-projects", "lexical-retrieval")


def test_health_reports_local_framework_state() -> None:
    response = CLIENT.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.10.1"


def test_projects_endpoint_is_read_only_projection() -> None:
    response = CLIENT.get("/api/v1/projects")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "jdgf-framework"
    assert response.json()[0]["version"] == "0.10.1"
    assert CLIENT.put("/api/v1/projects", json={}).status_code == 405


def test_lexical_endpoint_returns_cited_results() -> None:
    response = CLIENT.post(
        "/api/v1/retrieval/lexical",
        json={
            "query": "governed evidence",
            "documents": [
                {
                    "id": "doc-one",
                    "title": "Evidence",
                    "source": "docs/evidence.md",
                    "content": "Governed systems preserve evidence.",
                },
                {
                    "id": "doc-two",
                    "title": "Other",
                    "source": "docs/other.md",
                    "content": "Unrelated content.",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["hits"][0]["source"] == "docs/evidence.md"
    assert response.json()["hits"][0]["score"] == 1.0


def test_lexical_endpoint_rejects_duplicate_ids() -> None:
    document = {
        "id": "doc-one",
        "title": "Evidence",
        "source": "docs/evidence.md",
        "content": "Governed evidence.",
    }
    response = CLIENT.post(
        "/api/v1/retrieval/lexical",
        json={"query": "evidence", "documents": [document, document]},
    )

    assert response.status_code == 422
    assert "Duplicate" in response.json()["detail"]


def test_request_limits_are_enforced() -> None:
    response = CLIENT.post(
        "/api/v1/retrieval/lexical",
        json={
            "query": "x" * 501,
            "documents": [
                {
                    "id": "doc-one",
                    "title": "Evidence",
                    "source": "docs/evidence.md",
                    "content": "Evidence.",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_api_has_no_cors_or_authentication_claim() -> None:
    response = CLIENT.get("/healthz", headers={"Origin": "https://example.invalid"})
    openapi = CLIENT.get("/openapi.json").json()

    assert "access-control-allow-origin" not in response.headers
    assert "securitySchemes" not in openapi.get("components", {})


def test_registry_cannot_claim_unimplemented_endpoint(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    path = root / "registry" / "api.yaml"
    registry = _load(path)
    registry["endpoints"].append(
        {
            "id": "admin",
            "method": "GET",
            "path": "/api/v1/admin",
            "mutating": False,
            "authentication": "none",
        }
    )
    _write(path, registry)

    with pytest.raises(ApiPlatformError, match="implemented routes differ"):
        validate_api_platform(root)


def test_registry_rejects_mutating_endpoint(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    schema_path = root / "registry" / "api.schema.yaml"
    schema = _load(schema_path)
    schema["properties"]["endpoints"]["items"]["properties"]["mutating"] = {
        "type": "boolean"
    }
    _write(schema_path, schema)
    path = root / "registry" / "api.yaml"
    registry = _load(path)
    registry["endpoints"][2]["mutating"] = True
    _write(path, registry)

    with pytest.raises(ApiPlatformError, match="mutating"):
        validate_api_platform(root)
