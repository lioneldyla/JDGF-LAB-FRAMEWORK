# OpenHands adapter

## Status

Specified, disabled by default and isolated behind the Compose profile
`dangerous-local-agent`.

## Preferred installation

The upstream project recommends its `uv` launcher for local use:

```bash
uv tool install openhands --python 3.12
openhands serve
```

## Docker risk boundary

The optional Compose deployment mounts the Docker socket. This grants the agent
effective control over the host Docker daemon; a read-only socket mount would
not remove that authority. The installer therefore requires explicit risk
acceptance and a dedicated absolute workspace path.

```bash
cp infrastructure/openhands/.env.example infrastructure/openhands/.env
# Set OPENHANDS_WORKSPACE and OPENHANDS_ACCEPT_DOCKER_SOCKET_RISK=yes.
scripts/install/12_install_openhands.sh
```

The default URL is `http://127.0.0.1:3002`.

## Verify

```bash
tests/verify-openhands.sh
```
