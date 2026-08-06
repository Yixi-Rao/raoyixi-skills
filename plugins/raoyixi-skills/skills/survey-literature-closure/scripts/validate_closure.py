#!/usr/bin/env python3
"""Fail-closed validator for a literature-survey closure audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SUPPORTED_SCHEMA_VERSION = 1
SUPPORTED_SKILL_VERSION = "1.0.0"


def load_json(path_value: str) -> tuple[Any, bytes]:
    if path_value == "-":
        raw = sys.stdin.buffer.read()
    else:
        raw = Path(path_value).expanduser().resolve().read_bytes()
    return json.loads(raw), raw


def nested(value: Any, path: str, errors: list[str]) -> Any:
    current = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            errors.append(f"missing field: {path}")
            return None
        current = current[part]
    return current


def integer(value: Any, path: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"{path} must be a non-negative integer")
        return None
    return value


def boolean(value: Any, path: str, errors: list[str]) -> bool | None:
    if not isinstance(value, bool):
        errors.append(f"{path} must be a boolean")
        return None
    return value


def non_todo_string(value: Any, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip() or "todo" in value.lower():
        errors.append(f"{path} must be a non-empty finalized string")
        return None
    return value.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument(
        "--seed-manifest",
        help="Defaults to seed_manifest.json beside the contract",
    )
    parser.add_argument("--field-taxonomy", help="Defaults to field_taxonomy.json beside the contract")
    parser.add_argument(
        "--judgment-template",
        help="Defaults to adjudication/judgment_template.json under the project root",
    )
    parser.add_argument(
        "--mutation-plan",
        help="Defaults to reports/mutation_plan.json under the project root",
    )
    parser.add_argument("--audit", required=True, help="JSON path, or - for stdin")
    return parser.parse_args()


def parse_timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be an ISO-8601 timestamp")
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"{path} must be an ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{path} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def main() -> int:
    args = parse_args()
    try:
        contract, contract_raw = load_json(args.contract)
        project_root = Path(args.contract).expanduser().resolve().parent
        seed_path = args.seed_manifest or str(project_root / "seed_manifest.json")
        seed_manifest, seed_manifest_raw = load_json(seed_path)
        field_taxonomy, field_taxonomy_raw = load_json(
            args.field_taxonomy or str(project_root / "field_taxonomy.json")
        )
        judgment_template, judgment_template_raw = load_json(
            args.judgment_template or str(project_root / "adjudication" / "judgment_template.json")
        )
        mutation_plan, mutation_plan_raw = load_json(
            args.mutation_plan or str(project_root / "reports" / "mutation_plan.json")
        )
        audit, _ = load_json(args.audit)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    errors: list[str] = []
    blockers: list[str] = []
    if not isinstance(contract, dict):
        errors.append("contract root must be an object")
    if not isinstance(audit, dict):
        errors.append("audit root must be an object")
    if not isinstance(seed_manifest, dict):
        errors.append("seed manifest root must be an object")
    if not isinstance(field_taxonomy, dict):
        errors.append("field taxonomy root must be an object")
    if not isinstance(judgment_template, dict):
        errors.append("judgment template root must be an object")
    if not isinstance(mutation_plan, dict):
        errors.append("mutation plan root must be an object")
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 2

    if contract.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"contract.schema_version must equal {SUPPORTED_SCHEMA_VERSION}")
    if audit.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"audit.schema_version must equal {SUPPORTED_SCHEMA_VERSION}")
    if seed_manifest.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"seed_manifest.schema_version must equal {SUPPORTED_SCHEMA_VERSION}")
    if field_taxonomy.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"field_taxonomy.schema_version must equal {SUPPORTED_SCHEMA_VERSION}")
    if judgment_template.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"judgment_template.schema_version must equal {SUPPORTED_SCHEMA_VERSION}")
    if mutation_plan.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"mutation_plan.schema_version must equal {SUPPORTED_SCHEMA_VERSION}")
    contract_skill = contract.get("skill")
    if not isinstance(contract_skill, dict):
        errors.append("contract.skill must be an object")
    elif (
        contract_skill.get("name") != "survey-literature-closure"
        or contract_skill.get("version") != SUPPORTED_SKILL_VERSION
    ):
        errors.append(f"contract requires unsupported skill version; expected {SUPPORTED_SKILL_VERSION}")
    if audit.get("skill_version") != SUPPORTED_SKILL_VERSION:
        errors.append(f"audit.skill_version must equal {SUPPORTED_SKILL_VERSION}")
    if seed_manifest.get("skill_version") != SUPPORTED_SKILL_VERSION:
        errors.append(f"seed_manifest.skill_version must equal {SUPPORTED_SKILL_VERSION}")

    topic = non_todo_string(contract.get("topic"), "contract.topic", errors)
    non_todo_string(contract.get("research_question"), "contract.research_question", errors)
    cutoff = contract.get("cutoff")
    try:
        if not isinstance(cutoff, str) or date.fromisoformat(cutoff).isoformat() != cutoff:
            raise ValueError
    except ValueError:
        errors.append("contract.cutoff must be strict YYYY-MM-DD")
        cutoff = None

    if contract.get("mode") != "relevant-subgraph-closure":
        errors.append("contract.mode must equal relevant-subgraph-closure")
    scope = contract.get("scope")
    if not isinstance(scope, dict):
        errors.append("contract.scope must be an object")
    else:
        for key in ("strict_inclusion", "exclusion"):
            clauses = scope.get(key)
            if not isinstance(clauses, list) or not clauses:
                errors.append(f"contract.scope.{key} must be a non-empty array")
            elif any(non_todo_string(item, f"contract.scope.{key}[]", errors) is None for item in clauses):
                pass
        non_todo_string(scope.get("adjacent_rule"), "contract.scope.adjacent_rule", errors)
        if scope.get("expand_classifications") != ["core", "adjacent", "unresolved"]:
            errors.append("contract.scope.expand_classifications must preserve core/adjacent/unresolved expansion")
        if scope.get("leaf_classifications") != ["excluded"]:
            errors.append("contract.scope.leaf_classifications must contain only excluded")

    contract_fields = contract.get("fields")
    expected_fields: list[tuple[str, str, str]] = []
    if not isinstance(contract_fields, list):
        errors.append("contract.fields must be an array")
    else:
        seen_field_names: set[str] = set()
        for index, field in enumerate(contract_fields):
            if not isinstance(field, dict):
                errors.append(f"contract.fields[{index}] must be an object")
                continue
            name = non_todo_string(field.get("name"), f"contract.fields[{index}].name", errors)
            definition = non_todo_string(
                field.get("definition"), f"contract.fields[{index}].definition", errors
            )
            missing_value = non_todo_string(
                field.get("missing_value"), f"contract.fields[{index}].missing_value", errors
            )
            if name is not None:
                key = name.casefold()
                if key in seen_field_names:
                    errors.append(f"duplicate contract field name: {name}")
                seen_field_names.add(key)
            if name is not None and definition is not None and missing_value is not None:
                expected_fields.append((name, definition, missing_value))

    taxonomy_fields = field_taxonomy.get("fields")
    if not isinstance(taxonomy_fields, list):
        errors.append("field_taxonomy.fields must be an array")
    else:
        actual_taxonomy: list[tuple[Any, Any, Any]] = []
        for index, field in enumerate(taxonomy_fields):
            if not isinstance(field, dict):
                errors.append(f"field_taxonomy.fields[{index}] must be an object")
                continue
            actual_taxonomy.append(
                (field.get("name"), field.get("definition"), field.get("missing_value"))
            )
        if actual_taxonomy != expected_fields:
            errors.append("field taxonomy names, definitions, or missing values do not match the contract")

    expected_predicates = scope.get("strict_inclusion", []) if isinstance(scope, dict) else []
    judgment_criteria = judgment_template.get("criteria")
    if not isinstance(judgment_criteria, list):
        errors.append("judgment_template.criteria must be an array")
    else:
        actual_predicates = [
            (item.get("name"), item.get("predicate")) if isinstance(item, dict) else (None, None)
            for item in judgment_criteria
        ]
        expected_criteria = [
            (f"C{index}", predicate) for index, predicate in enumerate(expected_predicates, start=1)
        ]
        if actual_predicates != expected_criteria:
            errors.append("judgment template criteria do not mirror the contract predicates")
    judgment_fields = judgment_template.get("fields")
    if not isinstance(judgment_fields, list):
        errors.append("judgment_template.fields must be an array")
    else:
        actual_judgment_fields = [
            (item.get("name"), item.get("definition")) if isinstance(item, dict) else (None, None)
            for item in judgment_fields
        ]
        if actual_judgment_fields != [(name, definition) for name, definition, _ in expected_fields]:
            errors.append("judgment template fields do not mirror the contract fields")

    expected_hash = hashlib.sha256(contract_raw).hexdigest()
    if audit.get("contract_sha256") != expected_hash:
        errors.append("audit.contract_sha256 does not bind the exact contract bytes")
    artifact_hashes = {
        "field_taxonomy_sha256": hashlib.sha256(field_taxonomy_raw).hexdigest(),
        "judgment_template_sha256": hashlib.sha256(judgment_template_raw).hexdigest(),
        "mutation_plan_sha256": hashlib.sha256(mutation_plan_raw).hexdigest(),
    }
    for key, expected_artifact_hash in artifact_hashes.items():
        if nested(audit, f"artifacts.{key}", errors) != expected_artifact_hash:
            errors.append(f"audit.artifacts.{key} does not bind the exact artifact bytes")
    if topic is not None and audit.get("topic") != topic:
        errors.append("audit.topic does not match contract.topic")
    if cutoff is not None and audit.get("cutoff") != cutoff:
        errors.append("audit.cutoff does not match contract.cutoff")
    if topic is not None and seed_manifest.get("topic") != topic:
        errors.append("seed_manifest.topic does not match contract.topic")
    if cutoff is not None and seed_manifest.get("cutoff") != cutoff:
        errors.append("seed_manifest.cutoff does not match contract.cutoff")

    sources = contract.get("sources")
    if not isinstance(sources, dict):
        errors.append("contract.sources must be an object")
    else:
        for key in ("original", "bibliography", "graph", "identity_only"):
            values = sources.get(key)
            if not isinstance(values, list) or not values or any(
                not isinstance(item, str) or not item.strip() for item in values
            ):
                errors.append(f"contract.sources.{key} must be a non-empty string array")
        if "original_bibliography" not in sources.get("bibliography", []):
            errors.append("contract.sources.bibliography must include original_bibliography")

    phase = audit.get("phase")
    if phase not in {"closure", "refresh", "fixed_point_complete", "incomplete_budget", "blocked"}:
        errors.append("audit.phase is unknown")

    seed_count = integer(nested(audit, "seed_manifest.count", errors), "seed_manifest.count", errors)
    seed_structure_valid = boolean(
        nested(audit, "seed_manifest.structure_valid", errors),
        "seed_manifest.structure_valid",
        errors,
    )
    seed_identities_resolved = boolean(
        nested(audit, "seed_manifest.identities_resolved", errors),
        "seed_manifest.identities_resolved",
        errors,
    )
    seed_duplicates_resolved = boolean(
        nested(audit, "seed_manifest.duplicates_resolved", errors),
        "seed_manifest.duplicates_resolved",
        errors,
    )
    seed_hash = nested(audit, "seed_manifest.sha256", errors)
    expected_seed_hash = hashlib.sha256(seed_manifest_raw).hexdigest()
    if seed_hash != expected_seed_hash:
        errors.append("audit.seed_manifest.sha256 does not bind the exact seed manifest bytes")
    manifest_seeds = seed_manifest.get("seeds")
    if not isinstance(manifest_seeds, list):
        errors.append("seed_manifest.seeds must be an array")
    elif seed_count is not None and len(manifest_seeds) != seed_count:
        errors.append("audit seed count does not match seed_manifest.seeds")
    provenance_values: set[str] = set()
    if isinstance(manifest_seeds, list):
        for index, seed in enumerate(manifest_seeds):
            if not isinstance(seed, dict):
                errors.append(f"seed_manifest.seeds[{index}] must be an object")
                continue
            provenance = seed.get("provenance")
            if not isinstance(provenance, str) or not provenance.strip():
                errors.append(f"seed_manifest.seeds[{index}].provenance must be non-empty")
            else:
                provenance_values.add(provenance.strip().casefold())
    provenance_classes = integer(
        nested(audit, "seed_manifest.provenance_classes", errors),
        "seed_manifest.provenance_classes",
        errors,
    )
    if provenance_classes is not None and provenance_classes != len(provenance_values):
        errors.append("audit seed provenance count does not match the seed manifest")
    seed_policy = contract.get("seed_policy")
    if not isinstance(seed_policy, dict):
        errors.append("contract.seed_policy must be an object")
        minimum_provenance = None
    else:
        minimum_provenance = integer(
            seed_policy.get("min_provenance_classes"),
            "contract.seed_policy.min_provenance_classes",
            errors,
        )
        if minimum_provenance == 0:
            errors.append("contract seed provenance minimum must be positive")
    if (
        provenance_classes is not None
        and minimum_provenance is not None
        and provenance_classes < minimum_provenance
    ):
        blockers.append(
            f"seed_manifest.provenance_classes={provenance_classes}<required={minimum_provenance}"
        )
    if seed_count == 0:
        blockers.append("seed_manifest_empty")
    if seed_structure_valid is False:
        blockers.append("seed_manifest_structure_invalid")
    if seed_identities_resolved is False:
        blockers.append("seed_manifest_identities_unresolved")
    if seed_duplicates_resolved is False:
        blockers.append("seed_manifest_duplicates_unresolved")

    node_count = integer(nested(audit, "counts.nodes", errors), "counts.nodes", errors)
    integer(nested(audit, "counts.edges", errors), "counts.edges", errors)
    classes: dict[str, int | None] = {}
    for name in ("queued", "core", "adjacent", "excluded", "unresolved"):
        classes[name] = integer(
            nested(audit, f"counts.classifications.{name}", errors),
            f"counts.classifications.{name}",
            errors,
        )
    if node_count is not None and all(value is not None for value in classes.values()):
        if sum(value for value in classes.values() if value is not None) != node_count:
            errors.append("classification counts must sum exactly to counts.nodes")
    if node_count == 0:
        blockers.append("no_nodes_processed")
    if classes.get("queued", 0):
        blockers.append(f"queued_nodes={classes['queued']}")
    if classes.get("unresolved", 0):
        blockers.append(f"unresolved_nodes={classes['unresolved']}")

    zero_gates = (
        "queues.screen_pending",
        "queues.expand_pending",
        "queues.refresh_pending",
        "fetch.pending",
        "fetch.failed",
        "fetch.unresolved",
        "identity.conflicts",
        "identity.duplicates",
        "evidence.fulltext_gaps",
        "evidence.date_violations",
        "evidence.field_evidence_gaps",
        "issues.blocking",
        "dedup.taxonomy_collisions",
        "dedup.writeback_duplicates",
        "refresh.orphan_nodes",
    )
    for path in zero_gates:
        value = integer(nested(audit, path, errors), path, errors)
        if value not in (None, 0):
            blockers.append(f"{path}={value}")

    integer(nested(audit, "coverage.expandable_nodes", errors), "coverage.expandable_nodes", errors)
    true_gates = (
        "coverage.references_complete",
        "coverage.citations_complete",
        "coverage.all_required_pagination_complete",
        "coverage.source_union_current",
        "refresh.full_refresh_complete",
        "refresh.edge_snapshot_reconciled",
    )
    for path in true_gates:
        value = boolean(nested(audit, path, errors), path, errors)
        if value is False:
            blockers.append(f"{path}=false")

    refresh_round = integer(nested(audit, "refresh.round", errors), "refresh.round", errors)
    if refresh_round == 0:
        blockers.append("refresh.round=0")
    new_ids = nested(audit, "refresh.new_ids", errors)
    if new_ids is not None:
        new_ids = integer(new_ids, "refresh.new_ids", errors)
    if new_ids is None:
        blockers.append("refresh.new_ids=unknown")
    elif new_ids != 0:
        blockers.append(f"refresh.new_ids={new_ids}")

    budget_triggered = boolean(nested(audit, "budget.triggered", errors), "budget.triggered", errors)
    wallclock_exceeded = boolean(
        nested(audit, "budget.wallclock_exceeded", errors), "budget.wallclock_exceeded", errors
    )
    node_limit = integer(nested(audit, "budget.node_limit", errors), "budget.node_limit", errors)
    wallclock_hours = integer(
        nested(audit, "budget.wallclock_hours", errors), "budget.wallclock_hours", errors
    )
    if node_limit == 0 or wallclock_hours == 0:
        errors.append("budget limits must be positive")
    contract_budgets = contract.get("budgets")
    if not isinstance(contract_budgets, dict):
        errors.append("contract.budgets must be an object")
    else:
        contract_node_limit = integer(contract_budgets.get("unique_nodes"), "contract.budgets.unique_nodes", errors)
        contract_wallclock = integer(
            contract_budgets.get("wallclock_hours"), "contract.budgets.wallclock_hours", errors
        )
        contract_retries = integer(
            contract_budgets.get("http_retries_per_checkpoint"),
            "contract.budgets.http_retries_per_checkpoint",
            errors,
        )
        if contract_node_limit == 0 or contract_wallclock == 0 or contract_retries == 0:
            errors.append("contract budget values must be positive")
        if node_limit is not None and contract_node_limit is not None and node_limit != contract_node_limit:
            errors.append("audit budget.node_limit does not match the contract")
        if wallclock_hours is not None and contract_wallclock is not None and wallclock_hours != contract_wallclock:
            errors.append("audit budget.wallclock_hours does not match the contract")
    started_at = parse_timestamp(contract.get("created_at"), "contract.created_at", errors)
    generated_at = parse_timestamp(audit.get("generated_at"), "audit.generated_at", errors)
    if started_at is not None and generated_at is not None:
        if generated_at < started_at:
            errors.append("audit.generated_at cannot precede contract.created_at")
        elif wallclock_hours is not None:
            computed_exceeded = (generated_at - started_at).total_seconds() > wallclock_hours * 3600
            if wallclock_exceeded is not None and wallclock_exceeded != computed_exceeded:
                errors.append("audit budget.wallclock_exceeded disagrees with contract and audit timestamps")
    if node_count is not None and node_limit is not None and node_count > node_limit:
        blockers.append("budget.node_limit_exceeded")
    if budget_triggered is True:
        blockers.append("budget.triggered=true")
    if wallclock_exceeded is True:
        blockers.append("budget.wallclock_exceeded=true")

    delivery_required = boolean(
        nested(audit, "delivery.required", errors), "delivery.required", errors
    )
    contract_delivery = contract.get("delivery")
    if not isinstance(contract_delivery, dict) or not isinstance(contract_delivery.get("required"), bool):
        errors.append("contract.delivery.required must be a boolean")
    elif delivery_required is not None and delivery_required != contract_delivery["required"]:
        errors.append("audit.delivery.required does not match the contract")
    if isinstance(contract_delivery, dict):
        if mutation_plan.get("target") != contract_delivery.get("target"):
            errors.append("mutation plan target does not match the contract")
        if mutation_plan.get("protected_fields") != contract_delivery.get("protected_fields"):
            errors.append("mutation plan protected fields do not match the contract")
    if mutation_plan.get("mode") != "stage-only":
        errors.append("mutation plan mode must remain stage-only")
    if mutation_plan.get("applied") is not False:
        errors.append("mutation plan cannot serve as applied-write evidence")
    if not isinstance(mutation_plan.get("verified_against_live_schema"), bool):
        errors.append("mutation_plan.verified_against_live_schema must be a boolean")
    for key in ("creates", "updates", "new_options"):
        if not isinstance(mutation_plan.get(key), list):
            errors.append(f"mutation_plan.{key} must be an array")
    for path in (
        "delivery.readback_missing",
        "delivery.readback_duplicates",
        "delivery.readback_mismatches",
        "delivery.protected_field_changes",
    ):
        value = integer(nested(audit, path, errors), path, errors)
        if delivery_required is True and value not in (None, 0):
            blockers.append(f"{path}={value}")
    for path in ("delivery.dry_run_verified", "delivery.applied"):
        value = boolean(nested(audit, path, errors), path, errors)
        if delivery_required is True and value is False:
            blockers.append(f"{path}=false")

    declared_success = boolean(nested(audit, "claim.success", errors), "claim.success", errors)
    scope_qualified = boolean(
        nested(audit, "claim.scope_qualified", errors), "claim.scope_qualified", errors
    )
    disclaims_unindexed = boolean(
        nested(audit, "claim.disclaims_unindexed", errors), "claim.disclaims_unindexed", errors
    )
    statement = nested(audit, "claim.statement", errors)
    if not isinstance(statement, str):
        errors.append("claim.statement must be a string")
        statement = ""
    if scope_qualified is False:
        blockers.append("claim.scope_qualified=false")
    if disclaims_unindexed is False:
        blockers.append("claim.disclaims_unindexed=false")
    if cutoff is not None and cutoff not in statement:
        blockers.append("claim.statement_missing_cutoff")
    if not statement.strip():
        blockers.append("claim.statement_empty")
    if phase != "fixed_point_complete":
        blockers.append(f"phase={phase}")

    operational_blockers = list(dict.fromkeys(blockers))
    operational_complete = not errors and not operational_blockers
    if declared_success is True and not operational_complete:
        errors.append("claim.success=true while one or more completion gates fail")
    if declared_success is False and operational_complete:
        operational_blockers.append("claim.success=false")
    success = not errors and operational_complete and declared_success is True

    sources = contract.get("sources") if isinstance(contract.get("sources"), dict) else {}
    original_sources = ", ".join(sources.get("original", [])) if isinstance(sources.get("original"), list) else ""
    bibliography_sources = (
        ", ".join(sources.get("bibliography", []))
        if isinstance(sources.get("bibliography"), list)
        else ""
    )
    graph_sources = ", ".join(sources.get("graph", [])) if isinstance(sources.get("graph"), list) else ""
    qualified_statement = (
        f"在 {cutoff or '[cutoff]'} 截止快照下，对 {original_sources or '[original sources]'} 原文与 "
        f"{bibliography_sources or '[bibliography source]'}、{graph_sources or '[graph sources]'} "
        "返回并集中的相关子图完成闭包；"
        "该结论不覆盖这些来源均未收录的工作。"
    )
    result = {
        "valid": not errors,
        "operational_complete": operational_complete,
        "declared_success": declared_success,
        "success": success,
        "blockers": operational_blockers,
        "errors": errors,
        "success_statement_template": qualified_statement,
        "success_statement_usable": success,
        "validation_scope": "schema_and_cross_artifact_consistency_plus_completion_gates",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        return 2
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
