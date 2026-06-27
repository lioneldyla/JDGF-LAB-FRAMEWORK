# Open WebUI adapter

## Status

Specified and disabled by default. The Docker contract is pinned to Open WebUI
`v0.9.6` and binds only to `127.0.0.1`.

## Security defaults

- public registration disabled;
- community sharing disabled;
- web search disabled;
- persistent `WEBUI_SECRET_KEY` required by the installer;
- persistent named data volume;
- no project directory or Docker socket mount.

## Start

```bash
cp infrastructure/open-webui/.env.example infrastructure/open-webui/.env
openssl rand -hex 32
# Store the result as WEBUI_SECRET_KEY in the local .env file.
scripts/install/11_install_openwebui.sh
```

The default URL is `http://127.0.0.1:3000`.

## Policy

`config/config.yaml` is a JDGF policy contract. Open WebUI runtime settings are
passed through environment variables and persisted in its data volume.

## Verify

```bash
tests/verify-openwebui.sh
```
