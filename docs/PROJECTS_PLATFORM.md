# Projects platform

The projects platform is the first active JDGF control-plane slice. A project
joins the framework only through a manifest under `projects/` and an explicit
entry in `registry/projects.yaml`.

The CLI validates both documents against their JSON Schemas, rejects duplicate
or mismatched identifiers, and prevents manifest resolution outside the
projects directory. Templates remain unregistered.

Named product repositories are independent consumers. Their source code,
machine-specific paths and business rules do not belong in the framework core.
