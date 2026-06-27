"""Command-line interface for the JDGF control plane."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .api_platform import ApiPlatformError, validate_api_platform
from .ai_platform import AiPlatformError, validate_ai_platform
from .agent_platform import AgentPlatformError, validate_agent_platform
from .automation_platform import (
    AutomationPlatformError,
    validate_automation_platform,
)
from .catalogs import CatalogError, validate_bootstrap_catalogs
from .core_platform import CorePlatformError, run_doctor, validate_core_platform
from .data_platform import DataPlatformError, validate_data_platform
from .devsecops_platform import DevSecOpsPlatformError, validate_devsecops_platform
from .document_processing import (
    DocumentProcessingError,
    process_document,
    validate_document_processing,
)
from .governance_platform import GovernancePlatformError, validate_governance_platform
from .judicial_intelligence import (
    JudicialIntelligenceError,
    validate_judicial_intelligence,
)
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
from .runtime_platform import RuntimePlatformError, validate_runtime_platform
from .sdk_platform import SdkPlatformError, scaffold_project, validate_sdk_platform


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jdgf", description="JDGF control plane")
    parser.add_argument("--root", type=Path, help="Framework repository root")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", help="Validate framework contracts")
    subcommands.add_parser("projects", help="List registered projects")
    subcommands.add_parser("doctor", help="Diagnose the local framework state")
    scaffold = subcommands.add_parser(
        "scaffold-project", help="Create a validated, unregistered project"
    )
    scaffold.add_argument("project_id", help="Lowercase project identifier")
    scaffold.add_argument("--name", required=True, help="Human-readable project name")
    scaffold.add_argument("--owner", required=True, help="Accountable project owner")
    process = subcommands.add_parser(
        "process-document", help="Process a repository-bound TXT or Markdown file"
    )
    process.add_argument("path", type=Path, help="Path relative to the framework root")
    serve = subcommands.add_parser("serve", help="Run the local preview API")
    serve.add_argument("--port", type=int, default=8765, choices=range(1024, 65536))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = args.root.resolve() if args.root else repository_root()
        if args.command == "doctor":
            report = run_doctor(root)
            print(f"JDGF {report.version} doctor passed: " + ", ".join(report.checks))
            return 0
        if args.command == "scaffold-project":
            destination = scaffold_project(root, args.project_id, args.name, args.owner)
            print(f"Created proposed project at {destination}")
            return 0
        if args.command == "process-document":
            processing = validate_document_processing(root)
            document = process_document(
                root / args.path,
                root,
                max_bytes=processing.max_bytes,
            )
            print(
                f"Processed {document.source}: {document.id}, "
                f"{len(document.chunks)} chunk(s), {document.checksum}"
            )
            return 0
        if args.command == "serve":
            import uvicorn

            from .api import create_app

            uvicorn.run(
                create_app(root),
                host="127.0.0.1",
                port=args.port,
                access_log=True,
                server_header=False,
            )
            return 0
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
        devsecops_platform = (
            validate_devsecops_platform(root) if args.command == "validate" else None
        )
        sdk_platform = (
            validate_sdk_platform(root) if args.command == "validate" else None
        )
        core_platform = (
            validate_core_platform(root) if args.command == "validate" else None
        )
        judicial_intelligence = (
            validate_judicial_intelligence(root) if args.command == "validate" else None
        )
        document_processing = (
            validate_document_processing(root) if args.command == "validate" else None
        )
        runtime_platform = (
            validate_runtime_platform(root) if args.command == "validate" else None
        )
        api_platform = (
            validate_api_platform(root) if args.command == "validate" else None
        )
    except (
        AiPlatformError,
        ApiPlatformError,
        AgentPlatformError,
        AutomationPlatformError,
        CatalogError,
        CorePlatformError,
        DataPlatformError,
        DevSecOpsPlatformError,
        DocumentProcessingError,
        GovernancePlatformError,
        JudicialIntelligenceError,
        KnowledgePlatformError,
        OrchestrationPlatformError,
        RegistryError,
        RagContractError,
        RuntimePlatformError,
        SdkPlatformError,
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
        assert devsecops_platform is not None
        assert sdk_platform is not None
        assert core_platform is not None
        assert judicial_intelligence is not None
        assert document_processing is not None
        assert runtime_platform is not None
        assert api_platform is not None
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
            f"{len(governance_platform.policy_ids)} governance policy contract(s), "
            f"{len(devsecops_platform.workflow_ids)} CI workflow contract(s), "
            f"{len(sdk_platform.active_generators)} active SDK generator(s), "
            f"{len(core_platform.active_operations)} core operation(s), "
            f"{len(judicial_intelligence.outputs)} judicial intelligence output "
            f"contract(s), {len(document_processing.active_formats)} document "
            f"format(s), {len(rag.runtime_capabilities)} active local RAG "
            f"capability(s), {len(runtime_platform.active_components)} runtime "
            f"control component(s), {len(api_platform.endpoint_ids)} local API "
            "endpoint(s)."
        )
    else:
        if not projects:
            print("No projects registered.")
        for project in projects:
            print(f"{project.project_id}\t{project.lifecycle}\t{project.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
