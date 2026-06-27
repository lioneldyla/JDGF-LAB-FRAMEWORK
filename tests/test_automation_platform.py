from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

from jdgf_framework.automation_platform import (
    AutomationPlatformError,
    validate_automation_platform,
)


ROOT = Path(__file__).resolve().parents[1]
SERVICE_PATHS = {
    "n8n": ROOT / "infrastructure" / "n8n",
    "searxng": ROOT / "infrastructure" / "searxng",
    "prometheus": ROOT / "infrastructure" / "monitoring" / "prometheus",
    "grafana": ROOT / "infrastructure" / "monitoring" / "grafana",
    "loki": ROOT / "infrastructure" / "monitoring" / "loki",
}


def _copy_contracts(tmp_path: Path) -> Path:
    for relative in (
        "manifests/automation-platform.yaml",
        "manifests/automation-platform.schema.yaml",
        "registry/automation.yaml",
        "registry/automation.schema.yaml",
        "registry/services.yaml",
        "infrastructure/n8n/.env.example",
        "infrastructure/n8n/compose.yaml",
        "infrastructure/searxng/.env.example",
        "infrastructure/searxng/config/settings.yml",
        "infrastructure/monitoring/grafana/.env.example",
        "infrastructure/monitoring/grafana/compose.yaml",
        "infrastructure/monitoring/prometheus/prometheus.yml",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def test_automation_platform_contracts_are_valid() -> None:
    summary = validate_automation_platform(ROOT)

    assert summary.version == "0.2.0"
    assert summary.lifecycle == "specified"
    assert summary.installable is False
    assert set(summary.service_ids) == set(SERVICE_PATHS)


@pytest.mark.parametrize(("service", "directory"), SERVICE_PATHS.items())
def test_compose_contract_is_hardened(service: str, directory: Path) -> None:
    compose = _load(directory / "compose.yaml")
    definition = compose["services"][service]

    assert definition["image"].startswith("${")
    assert definition["ports"][0].startswith("127.0.0.1:${")
    assert definition["security_opt"] == ["no-new-privileges:true"]
    assert definition["healthcheck"]
    assert compose["networks"]["jdgf-network"]["external"] is True


@pytest.mark.parametrize(("service", "directory"), SERVICE_PATHS.items())
def test_compose_configuration_renders(service: str, directory: Path) -> None:
    if not shutil.which("docker"):
        pytest.skip("Docker CLI is unavailable")
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(directory / ".env.example"),
            "--file",
            str(directory / "compose.yaml"),
            "config",
            "--quiet",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_images_are_pinned_by_version_and_digest() -> None:
    for directory in SERVICE_PATHS.values():
        image_lines = [
            line
            for line in (directory / ".env.example")
            .read_text(encoding="utf-8")
            .splitlines()
            if "_IMAGE=" in line
        ]
        assert len(image_lines) == 1
        image = image_lines[0].split("=", 1)[1]
        assert ":latest" not in image
        assert "@sha256:" in image


def test_non_active_service_cannot_be_enabled(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    registry_path = root / "registry" / "automation.yaml"
    registry = _load(registry_path)
    registry["services"][0]["enabled"] = True
    _write(registry_path, registry)

    with pytest.raises(AutomationPlatformError, match="Non-active"):
        validate_automation_platform(root)


def test_unknown_dependency_is_rejected(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    registry_path = root / "registry" / "automation.yaml"
    registry = _load(registry_path)
    registry["services"][0]["dependencies"].append("unknown-service")
    _write(registry_path, registry)

    with pytest.raises(AutomationPlatformError, match="unknown dependencies"):
        validate_automation_platform(root)


def test_installable_requires_runtime_evidence(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    manifest_path = root / "manifests" / "automation-platform.yaml"
    manifest = _load(manifest_path)
    manifest["spec"]["installable"] = True
    _write(manifest_path, manifest)

    with pytest.raises(AutomationPlatformError, match="runtime tests"):
        validate_automation_platform(root)


def test_schema_rejects_undeclared_readiness_claim(tmp_path: Path) -> None:
    root = _copy_contracts(tmp_path)
    manifest_path = root / "manifests" / "automation-platform.yaml"
    manifest = _load(manifest_path)
    manifest["spec"]["production_ready"] = True
    _write(manifest_path, manifest)

    with pytest.raises(AutomationPlatformError, match="Additional properties"):
        validate_automation_platform(root)


def test_private_and_honest_defaults() -> None:
    manifest = _load(ROOT / "manifests" / "automation-platform.yaml")
    monitoring = manifest["spec"]["monitoring"]
    assert monitoring["dashboards_provisioned"] is False
    assert monitoring["alerting_configured"] is False
    assert monitoring["log_collection_configured"] is False

    searxng = _load(ROOT / "infrastructure" / "searxng" / "config" / "settings.yml")
    assert searxng["server"]["limiter"] is True
    assert searxng["server"]["public_instance"] is False

    grafana = _load(ROOT / "infrastructure" / "monitoring" / "grafana" / "compose.yaml")
    assert (
        grafana["services"]["grafana"]["environment"]["GF_AUTH_ANONYMOUS_ENABLED"]
        == "false"
    )
