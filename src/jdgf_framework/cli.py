"""Command-line interface for the JDGF control plane."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .projects import RegistryError, load_project_registry, repository_root


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jdgf", description="JDGF control plane")
    parser.add_argument("--root", type=Path, help="Framework repository root")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", help="Validate registries and manifests")
    subcommands.add_parser("projects", help="List registered projects")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = args.root.resolve() if args.root else repository_root()
        projects = load_project_registry(root)
    except RegistryError as exc:
        print(f"JDGF validation failed: {exc}", file=sys.stderr)
        return 1

    if args.command == "validate":
        print(f"JDGF validation passed: {len(projects)} project(s) registered.")
    else:
        if not projects:
            print("No projects registered.")
        for project in projects:
            print(f"{project.project_id}\t{project.lifecycle}\t{project.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
