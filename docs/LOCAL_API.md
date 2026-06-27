# Local API Preview

## Scope

The executable FastAPI service exposes only capabilities already implemented by
the framework:

- `GET /healthz` — local framework diagnostics;
- `GET /api/v1/projects` — read-only registered project projection;
- `POST /api/v1/retrieval/lexical` — bounded, in-memory lexical retrieval.

Run it from the repository:

```bash
.venv/bin/jdgf serve --port 8765
```

The CLI always binds to `127.0.0.1`. Interactive OpenAPI documentation is
available at `http://127.0.0.1:8765/docs`.

## Security boundary

The preview has no authentication because it is loopback-only and exposes no
state-changing endpoint. CORS is not enabled. Retrieval requests accept at most
50 documents, 100,000 characters per document, a 500-character query and a
`top_k` of 20.

Do not place this service behind a proxy or bind it to another interface.
Authentication, authorization, request-body limits at the server boundary,
rate limiting and durable audit are prerequisites for any non-local deployment.

## Non-goals

There is no database, user account, tenant, agent execution, model provider,
upload, persistence, WebSocket, GraphQL or enterprise administration endpoint.
