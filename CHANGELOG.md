# Changelog

## 0.1.0 - 2026-06-27

- Added executable JSON Schema validation for project manifests and their
  registry.
- Added a deterministic verification entry point.
- Locked Python 3.12 dependencies with `uv.lock` and made bootstrap consume the
  lock without editable-install artifacts.
- Removed generated files, empty placeholders and inactive platform skeletons.
- Reconciled the historical v2 specification archive with the autonomous
  framework boundary; project-specific and inactive runtime artifacts remain
  excluded.
