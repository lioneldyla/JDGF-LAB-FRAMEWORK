from pathlib import Path
import shutil
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SERVICES = (
    "ollama",
    "litellm",
    "open-webui",
    "openhands",
    "postgres",
    "redis",
    "neo4j",
    "qdrant",
)


@pytest.mark.parametrize("service", SERVICES)
def test_compose_contract_is_hardened(service: str) -> None:
    path = ROOT / "infrastructure" / service / "compose.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    definition = document["services"][service]

    assert definition["image"].startswith("${")
    assert definition["ports"][0].startswith('127.0.0.1:${')
    assert definition["security_opt"] == ["no-new-privileges:true"]
    assert definition["healthcheck"]
    assert document["networks"]["jdgf-network"]["external"] is True


@pytest.mark.parametrize("service", SERVICES)
def test_compose_configuration_renders(service: str) -> None:
    if not shutil.which("docker"):
        pytest.skip("Docker CLI is unavailable")
    directory = ROOT / "infrastructure" / service
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
    for service in SERVICES:
        env_path = ROOT / "infrastructure" / service / ".env.example"
        image_lines = [
            line for line in env_path.read_text(encoding="utf-8").splitlines()
            if line.endswith(tuple("0123456789abcdef")) and "_IMAGE=" in line
        ]
        assert len(image_lines) == 1
        image = image_lines[0].split("=", 1)[1]
        assert ":latest" not in image
        assert ":main" not in image
        assert "@sha256:" in image


def test_litellm_routes_are_local_and_secret_free() -> None:
    config_path = ROOT / "infrastructure" / "litellm" / "config" / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["model_list"]
    for route in config["model_list"]:
        params = route["litellm_params"]
        assert params["model"].startswith("ollama/")
        assert params["api_base"] == "os.environ/OLLAMA_API_BASE"
        assert "api_key" not in params


def test_docker_services_are_specified_but_disabled() -> None:
    registry_path = ROOT / "registry" / "services.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    services = {entry["id"]: entry for entry in registry["services"]}

    for service in ("docker", *SERVICES):
        assert services[service]["lifecycle"] == "specified"
        assert services[service]["enabled"] is False


def test_open_webui_has_private_defaults() -> None:
    env_path = ROOT / "infrastructure" / "open-webui" / ".env.example"
    values = dict(
        line.split("=", 1)
        for line in env_path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    )

    assert values["WEBUI_SECRET_KEY"] == ""
    assert values["ENABLE_SIGNUP"] == "false"
    assert values["ENABLE_COMMUNITY_SHARING"] == "false"
    assert values["ENABLE_RAG_WEB_SEARCH"] == "false"


def test_openhands_requires_explicit_dangerous_profile() -> None:
    compose_path = ROOT / "infrastructure" / "openhands" / "compose.yaml"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    service = compose["services"]["openhands"]

    assert service["profiles"] == ["dangerous-local-agent"]
    assert "/var/run/docker.sock:/var/run/docker.sock" in service["volumes"]
    assert service["environment"]["LOG_ALL_EVENTS"] == "${LOG_ALL_EVENTS:-false}"

    env_text = (ROOT / "infrastructure" / "openhands" / ".env.example").read_text(
        encoding="utf-8"
    )
    assert "OPENHANDS_ACCEPT_DOCKER_SOCKET_RISK=no" in env_text
    assert "AGENT_SERVER_IMAGE_TAG=1.26.0-python@sha256:" in env_text


@pytest.mark.parametrize(
    ("service", "secret"),
    (
        ("postgres", "POSTGRES_PASSWORD"),
        ("redis", "REDIS_PASSWORD"),
        ("neo4j", "NEO4J_PASSWORD"),
        ("qdrant", "QDRANT_API_KEY"),
    ),
)
def test_data_service_examples_do_not_ship_credentials(
    service: str, secret: str
) -> None:
    env_text = (ROOT / "infrastructure" / service / ".env.example").read_text(
        encoding="utf-8"
    )
    assert f"{secret}=\n" in env_text


def test_data_services_have_secure_defaults() -> None:
    postgres_config = (
        ROOT / "infrastructure" / "postgres" / "config" / "postgresql.conf"
    ).read_text(encoding="utf-8")
    redis_compose = (
        ROOT / "infrastructure" / "redis" / "compose.yaml"
    ).read_text(encoding="utf-8")
    qdrant = yaml.safe_load(
        (ROOT / "infrastructure" / "qdrant" / "compose.yaml").read_text(
            encoding="utf-8"
        )
    )

    assert "password_encryption = 'scram-sha-256'" in postgres_config
    assert "--requirepass" in redis_compose
    assert (
        qdrant["services"]["qdrant"]["environment"][
            "QDRANT__SERVICE__ENABLE_CORS"
        ]
        == "false"
    )
