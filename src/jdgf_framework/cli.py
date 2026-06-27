"""Command-line interface for the JDGF control plane."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .ai_platform import AiPlatformError, validate_ai_platform
from .agent_platform import AgentPlatformError, validate_agent_platform
from .automation_platform import (
    AutomationPlatformError,
    validate_automation_platform,
)
from .catalogs import CatalogError, validate_bootstrap_catalogs
from .data_platform import DataPlatformError, validate_data_platform
from .governance_platform import GovernancePlatformError, validate_governance_platform
from .knowledge_platform import KnowledgePlatformError, validate_knowledge_platform
from .orchestration_platform import (
    OrchestrationPlatformError,
    validate_orchestration_platform,
)
from .projects import (
    RegistryError,
    load_project_registry,
    repository_root,
    validate_projects_platform,
)
from .rag import RagContractError, validate_rag_contracts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jdgf", description="JDGF control plane")
    parser.add_argument("--root", type=Path, help="Framework repository root")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", help="Validate framework contracts")
    subcommands.add_parser("projects", help="List registered projects")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = args.root.resolve() if args.root else repository_root()
        projects = load_project_registry(root)
        rag = validate_rag_contracts(root) if args.command == "validate" else None
        catalogs = (
            validate_bootstrap_catalogs(root) if args.command == "validate" else None
        )
        ai_platform = validate_ai_platform(root) if args.command == "validate" else None
        data_platform = (
            validate_data_platform(root) if args.command == "validate" else None
        )
        automation_platform = (
            validate_automation_platform(root) if args.command == "validate" else None
        )
        knowledge_platform = (
            validate_knowledge_platform(root) if args.command == "validate" else None
        )
        projects_platform = (
            validate_projects_platform(root) if args.command == "validate" else None
        )
        agent_platform = (
            validate_agent_platform(root) if args.command == "validate" else None
        )
        orchestration_platform = (
            validate_orchestration_platform(root)
            if args.command == "validate"
            else None
        )
        governance_platform = (
            validate_governance_platform(root) if args.command == "validate" else None
        )
    except (
        AiPlatformError,
        AgentPlatformError,
        AutomationPlatformError,
        CatalogError,
        DataPlatformError,
        GovernancePlatformError,
        KnowledgePlatformError,
        OrchestrationPlatformError,
        RegistryError,
        RagContractError,
    ) as exc:
        print(f"JDGF validation failed: {exc}", file=sys.stderr)
        return 1

    if args.command == "validate":
        assert rag is not None
        assert catalogs is not None
        assert ai_platform is not None
        assert data_platform is not None
        assert automation_platform is not None
        assert knowledge_platform is not None
        assert projects_platform is not None
        assert agent_platform is not None
        assert orchestration_platform is not None
        assert governance_platform is not None
        print(
            "JDGF validation passed: "
            f"{len(projects)} project(s), "
            f"{len(rag.component_ids)} RAG component(s), "
            f"{catalogs.manifest_count} bootstrap manifest(s), "
            f"{catalogs.registry_count} bootstrap registry catalog(s), "
            f"{len(ai_platform.service_ids)} AI service contract(s), "
            f"{len(data_platform.service_ids)} data service contract(s), "
            f"{len(automation_platform.service_ids)} automation/monitoring "
            "service contract(s), "
            f"{len(knowledge_platform.collection_ids)} knowledge collection "
            "contract(s), "
            f"{len(projects_platform.project_ids)} registered project contract(s), "
            f"{len(agent_platform.agent_ids)} agent profile contract(s), "
            f"{len(orchestration_platform.workflow_ids)} workflow contract(s), "
            f"{len(governance_platform.policy_ids)} governance policy contract(s)."
        )
    else:
        if not projects:
            print("No projects registered.")
        for project in projects:
            print(f"{project.project_id}\t{project.lifecycle}\t{project.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
