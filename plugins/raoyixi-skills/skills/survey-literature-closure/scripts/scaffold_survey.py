#!/usr/bin/env python3
"""Create a non-overwriting, persistent literature-survey project scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
SKILL_VERSION = "1.0.0"
SEED_KINDS = {"arxiv", "doi", "s2", "openalex", "title", "url"}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_cutoff(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("cutoff must be strict YYYY-MM-DD") from exc
    return parsed.isoformat()


def parse_seed(value: str) -> tuple[str, str, str]:
    provenance, provenance_separator, identity = value.partition("|")
    if not provenance_separator:
        provenance, identity = "user_seed", value
    provenance = provenance.strip().casefold()
    kind, separator, raw = identity.partition(":")
    kind = kind.strip().lower()
    raw = raw.strip()
    if not provenance or len(provenance) > 100:
        raise argparse.ArgumentTypeError("seed provenance must be 1-100 characters")
    if not separator or kind not in SEED_KINDS or not raw:
        allowed = ", ".join(sorted(SEED_KINDS))
        raise argparse.ArgumentTypeError(
            f"seed must be [PROVENANCE|]KIND:VALUE where KIND is one of: {allowed}"
        )
    return provenance, kind, raw


def parse_field(value: str) -> tuple[str, str]:
    name, separator, definition = value.partition("=")
    name = name.strip()
    definition = definition.strip()
    if not separator or not name or not definition:
        raise argparse.ArgumentTypeError("field must be NAME=DEFINITION with both parts non-empty")
    return name, definition


def require_nonblank(values: list[str], label: str) -> list[str]:
    cleaned = [value.strip() for value in values if value.strip()]
    if not cleaned:
        raise ValueError(f"at least one non-empty {label} is required")
    return cleaned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New output directory; existing paths are refused")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--research-question", required=True)
    parser.add_argument("--cutoff", required=True, type=parse_cutoff)
    parser.add_argument("--include", action="append", default=[], help="Repeat for each strict inclusion predicate")
    parser.add_argument("--exclude", action="append", default=[], help="Repeat for each explicit exclusion predicate")
    parser.add_argument("--adjacent-rule", required=True)
    parser.add_argument(
        "--seed",
        action="append",
        type=parse_seed,
        default=[],
        help="Repeat [PROVENANCE|]KIND:VALUE seeds; quote values containing |",
    )
    parser.add_argument("--min-seed-provenance-classes", type=int, default=2)
    parser.add_argument(
        "--field",
        action="append",
        type=parse_field,
        default=[],
        help="Repeat NAME=DEFINITION extraction fields",
    )
    parser.add_argument("--graph-source", action="append", default=[], help="Override default graph sources")
    parser.add_argument("--delivery-target", default="local evidence package")
    parser.add_argument("--delivery-required", action="store_true")
    parser.add_argument("--protected-field", action="append", default=[])
    parser.add_argument("--node-limit", type=int, default=50_000)
    parser.add_argument("--wallclock-hours", type=int, default=72)
    parser.add_argument("--http-retries", type=int, default=6)
    return parser


def validate_args(args: argparse.Namespace) -> None:
    args.topic = args.topic.strip()
    args.research_question = args.research_question.strip()
    args.adjacent_rule = args.adjacent_rule.strip()
    args.include = require_nonblank(args.include, "--include predicate")
    args.exclude = require_nonblank(args.exclude, "--exclude predicate")
    args.fields = args.field
    args.graph_source = [item.strip() for item in args.graph_source if item.strip()]
    args.protected_field = [item.strip() for item in args.protected_field if item.strip()]
    if not args.topic or not args.research_question or not args.adjacent_rule:
        raise ValueError("topic, research question, and adjacent rule must be non-empty")
    if len({name.casefold() for name, _ in args.fields}) != len(args.fields):
        raise ValueError("duplicate --field names are not allowed")
    if not args.seed:
        raise ValueError("at least one --seed is required")
    seed_identities = [(kind, raw) for _, kind, raw in args.seed]
    if len(set(seed_identities)) != len(seed_identities):
        raise ValueError("duplicate seed KIND:VALUE entries are not allowed")
    for name in ("node_limit", "wallclock_hours", "http_retries", "min_seed_provenance_classes"):
        if getattr(args, name) <= 0:
            raise ValueError(f"--{name.replace('_', '-')} must be a positive integer")


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE nodes (
  id INTEGER PRIMARY KEY,
  canonical_title TEXT,
  arxiv_id TEXT,
  doi TEXT,
  s2_id TEXT,
  openalex_id TEXT,
  classification TEXT NOT NULL DEFAULT 'queued'
    CHECK (classification IN ('queued','core','adjacent','excluded','unresolved')),
  evidence_level TEXT NOT NULL DEFAULT 'metadata_only',
  fulltext_status TEXT NOT NULL DEFAULT 'pending',
  depth INTEGER NOT NULL DEFAULT 0 CHECK (depth >= 0),
  is_seed INTEGER NOT NULL DEFAULT 0 CHECK (is_seed IN (0,1)),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX nodes_arxiv_unique ON nodes(arxiv_id) WHERE arxiv_id IS NOT NULL;
CREATE UNIQUE INDEX nodes_doi_unique ON nodes(doi) WHERE doi IS NOT NULL;
CREATE TABLE aliases (
  kind TEXT NOT NULL,
  value TEXT NOT NULL,
  node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  provenance TEXT NOT NULL,
  PRIMARY KEY (kind, value)
);
CREATE TABLE edges (
  id INTEGER PRIMARY KEY,
  source_node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  target_node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  direction TEXT NOT NULL CHECK (direction IN ('references','citations')),
  provider TEXT NOT NULL,
  raw_identifier TEXT,
  snapshot_token TEXT,
  UNIQUE(source_node_id, target_node_id, direction, provider, snapshot_token)
);
CREATE TABLE discovery_paths (
  id INTEGER PRIMARY KEY,
  node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  parent_node_id INTEGER REFERENCES nodes(id) ON DELETE SET NULL,
  provider TEXT NOT NULL,
  direction TEXT,
  depth INTEGER NOT NULL CHECK (depth >= 0),
  raw_identifier TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE queues (
  kind TEXT NOT NULL CHECK (kind IN ('screen','expand','refresh')),
  node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending','processing','done','failed')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  available_at TEXT,
  last_error TEXT,
  PRIMARY KEY (kind, node_id)
);
CREATE TABLE judgments (
  id INTEGER PRIMARY KEY,
  node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  classification TEXT NOT NULL,
  criteria_json TEXT NOT NULL,
  fields_json TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_sha256 TEXT,
  evidence_level TEXT NOT NULL,
  reviewer TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE evidence (
  id INTEGER PRIMARY KEY,
  node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  source_kind TEXT NOT NULL,
  source_url TEXT NOT NULL,
  local_path TEXT,
  sha256 TEXT,
  complete INTEGER NOT NULL DEFAULT 0 CHECK (complete IN (0,1)),
  identity_verified INTEGER NOT NULL DEFAULT 0 CHECK (identity_verified IN (0,1)),
  created_at TEXT NOT NULL
);
CREATE TABLE coverage (
  node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  direction TEXT NOT NULL CHECK (direction IN ('references','citations')),
  provider TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending','processing','complete','not_indexed','failed','cooldown')),
  cursor TEXT,
  pages INTEGER NOT NULL DEFAULT 0,
  items INTEGER NOT NULL DEFAULT 0,
  expected_items INTEGER,
  snapshot_token TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  PRIMARY KEY (node_id, direction, provider)
);
CREATE TABLE identity_conflicts (
  id INTEGER PRIMARY KEY,
  left_node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  right_node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved')),
  evidence_json TEXT NOT NULL
);
CREATE TABLE issues (
  id INTEGER PRIMARY KEY,
  node_id INTEGER REFERENCES nodes(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  blocking INTEGER NOT NULL DEFAULT 1 CHECK (blocking IN (0,1)),
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved')),
  detail TEXT NOT NULL,
  created_at TEXT NOT NULL,
  resolved_at TEXT
);
CREATE TABLE refresh_rounds (
  round INTEGER PRIMARY KEY,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  new_ids INTEGER,
  edge_snapshot_reconciled INTEGER NOT NULL DEFAULT 0,
  orphan_nodes INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE delivery_audit (
  id INTEGER PRIMARY KEY,
  mode TEXT NOT NULL,
  applied INTEGER NOT NULL DEFAULT 0 CHECK (applied IN (0,1)),
  plan_json TEXT NOT NULL,
  readback_json TEXT,
  created_at TEXT NOT NULL
);
"""


def create_project(args: argparse.Namespace) -> Path:
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing path: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    created_at = utc_now()
    try:
        for relative in ("cache", "evidence", "adjudication", "reports"):
            (temp_root / relative).mkdir()

        graph_sources = args.graph_source or ["semantic_scholar", "openalex"]
        contract = {
            "schema_version": SCHEMA_VERSION,
            "skill": {"name": "survey-literature-closure", "version": SKILL_VERSION},
            "topic": args.topic,
            "research_question": args.research_question,
            "cutoff": args.cutoff,
            "mode": "relevant-subgraph-closure",
            "scope": {
                "strict_inclusion": args.include,
                "adjacent_rule": args.adjacent_rule,
                "exclusion": args.exclude,
                "expand_classifications": ["core", "adjacent", "unresolved"],
                "leaf_classifications": ["excluded"],
            },
            "seed_policy": {
                "min_provenance_classes": args.min_seed_provenance_classes,
            },
            "sources": {
                "original": ["arxiv_html", "arxiv_pdf", "author_or_publisher_fulltext"],
                "bibliography": ["original_bibliography"],
                "graph": graph_sources,
                "identity_only": ["crossref"],
            },
            "fields": [
                {"name": name, "definition": definition, "missing_value": "论文未披露"}
                for name, definition in args.fields
            ],
            "delivery": {
                "target": args.delivery_target.strip(),
                "required": args.delivery_required,
                "mutation_policy": "stage-only-until-fixed-point",
                "protected_fields": args.protected_field,
            },
            "budgets": {
                "unique_nodes": args.node_limit,
                "wallclock_hours": args.wallclock_hours,
                "http_retries_per_checkpoint": args.http_retries,
            },
            "created_at": created_at,
        }
        contract_raw = json_bytes(contract)
        contract_hash = hashlib.sha256(contract_raw).hexdigest()
        (temp_root / "survey_contract.json").write_bytes(contract_raw)

        seeds = [
            {"seed_id": index, "kind": kind, "value": value, "provenance": provenance}
            for index, (provenance, kind, value) in enumerate(args.seed, start=1)
        ]
        seed_manifest = {
            "schema_version": SCHEMA_VERSION,
            "skill_version": SKILL_VERSION,
            "topic": args.topic,
            "cutoff": args.cutoff,
            "created_at": created_at,
            "seeds": seeds,
        }
        seed_manifest_raw = json_bytes(seed_manifest)
        seed_manifest_hash = hashlib.sha256(seed_manifest_raw).hexdigest()
        (temp_root / "seed_manifest.json").write_bytes(seed_manifest_raw)

        database = temp_root / "ledger.sqlite"
        with sqlite3.connect(database) as connection:
            connection.executescript(SCHEMA)
            connection.executemany(
                "INSERT INTO meta(key, value) VALUES (?, ?)",
                [
                    ("schema_version", "1"),
                    ("skill_version", SKILL_VERSION),
                    ("topic", args.topic),
                    ("cutoff", args.cutoff),
                    ("contract_sha256", contract_hash),
                    ("run_started_at", created_at),
                ],
            )
            for seed in seeds:
                kind, value, node_id = seed["kind"], seed["value"], seed["seed_id"]
                canonical_title = value if kind == "title" else None
                identifiers = {
                    "arxiv_id": value if kind == "arxiv" else None,
                    "doi": value if kind == "doi" else None,
                    "s2_id": value if kind == "s2" else None,
                    "openalex_id": value if kind == "openalex" else None,
                }
                connection.execute(
                    """INSERT INTO nodes(
                         id, canonical_title, arxiv_id, doi, s2_id, openalex_id,
                         classification, evidence_level, fulltext_status, depth,
                         is_seed, created_at, updated_at
                       ) VALUES (?, ?, ?, ?, ?, ?, 'queued', 'metadata_only', 'pending', 0, 1, ?, ?)""",
                    (
                        node_id,
                        canonical_title,
                        identifiers["arxiv_id"],
                        identifiers["doi"],
                        identifiers["s2_id"],
                        identifiers["openalex_id"],
                        created_at,
                        created_at,
                    ),
                )
                connection.execute(
                    "INSERT INTO aliases(kind, value, node_id, provenance) VALUES (?, ?, ?, ?)",
                    (kind, value, node_id, f"seed:{seed['provenance']}"),
                )
                connection.execute(
                    "INSERT INTO discovery_paths(node_id, parent_node_id, provider, direction, depth, raw_identifier, created_at) VALUES (?, NULL, 'seed_manifest', NULL, 0, ?, ?)",
                    (node_id, f"{kind}:{value}", created_at),
                )
                connection.execute(
                    "INSERT INTO queues(kind, node_id, status, attempts) VALUES ('screen', ?, 'pending', 0)",
                    (node_id,),
                )

        audit = {
            "schema_version": SCHEMA_VERSION,
            "skill_version": SKILL_VERSION,
            "contract_sha256": contract_hash,
            "topic": args.topic,
            "cutoff": args.cutoff,
            "generated_at": created_at,
            "phase": "closure",
            "seed_manifest": {
                "count": len(seeds),
                "sha256": seed_manifest_hash,
                "structure_valid": True,
                "identities_resolved": False,
                "duplicates_resolved": False,
                "provenance_classes": len({seed["provenance"] for seed in seeds}),
            },
            "counts": {
                "nodes": len(seeds),
                "edges": 0,
                "classifications": {
                    "queued": len(seeds),
                    "core": 0,
                    "adjacent": 0,
                    "excluded": 0,
                    "unresolved": 0,
                },
            },
            "queues": {"screen_pending": len(seeds), "expand_pending": 0, "refresh_pending": 0},
            "fetch": {"pending": 0, "failed": 0, "unresolved": 0},
            "identity": {"conflicts": 0, "duplicates": 0},
            "evidence": {
                "fulltext_gaps": len(seeds),
                "date_violations": 0,
                "field_evidence_gaps": len(seeds) * len(args.fields),
            },
            "coverage": {
                "expandable_nodes": 0,
                "references_complete": False,
                "citations_complete": False,
                "all_required_pagination_complete": False,
                "source_union_current": False,
            },
            "refresh": {
                "round": 0,
                "full_refresh_complete": False,
                "new_ids": None,
                "edge_snapshot_reconciled": False,
                "orphan_nodes": 0,
            },
            "issues": {"blocking": 0},
            "dedup": {"taxonomy_collisions": 0, "writeback_duplicates": 0},
            "budget": {
                "node_limit": args.node_limit,
                "wallclock_hours": args.wallclock_hours,
                "triggered": False,
                "wallclock_exceeded": False,
                "reason": None,
            },
            "delivery": {
                "required": args.delivery_required,
                "dry_run_verified": False,
                "applied": False,
                "readback_missing": 0,
                "readback_duplicates": 0,
                "readback_mismatches": 0,
                "protected_field_changes": 0,
            },
            "claim": {
                "success": False,
                "scope_qualified": False,
                "disclaims_unindexed": False,
                "statement": "",
            },
        }
        judgment_template = {
            "schema_version": SCHEMA_VERSION,
            "node_id": None,
            "identity": {"title": "", "arxiv": None, "doi": None, "s2": None, "openalex": None},
            "source": {"url": "", "kind": "", "sha256": "", "complete": False},
            "classification": "unresolved",
            "criteria": [
                {
                    "name": f"C{index}",
                    "predicate": predicate,
                    "value": "unknown",
                    "location": "",
                    "evidence": "",
                }
                for index, predicate in enumerate(args.include, start=1)
            ],
            "fields": [
                {
                    "name": name,
                    "definition": definition,
                    "value": None,
                    "location": "",
                    "evidence": "",
                }
                for name, definition in args.fields
            ],
            "uncertainties": [],
            "reviewer": "",
        }
        judgment_template_raw = json_bytes(judgment_template)
        (temp_root / "adjudication" / "judgment_template.json").write_bytes(judgment_template_raw)
        field_taxonomy = {
            "schema_version": SCHEMA_VERSION,
            "fields": [
                {
                    "name": name,
                    "definition": definition,
                    "missing_value": "论文未披露",
                    "canonical_options": [],
                    "aliases": {},
                }
                for name, definition in args.fields
            ],
        }
        field_taxonomy_raw = json_bytes(field_taxonomy)
        (temp_root / "field_taxonomy.json").write_bytes(field_taxonomy_raw)
        mutation_plan = {
            "schema_version": SCHEMA_VERSION,
            "mode": "stage-only",
            "target": contract["delivery"]["target"],
            "creates": [],
            "updates": [],
            "new_options": [],
            "protected_fields": contract["delivery"]["protected_fields"],
            "verified_against_live_schema": False,
            "applied": False,
        }
        mutation_plan_raw = json_bytes(mutation_plan)
        (temp_root / "reports" / "mutation_plan.json").write_bytes(mutation_plan_raw)
        audit["artifacts"] = {
            "judgment_template_sha256": hashlib.sha256(judgment_template_raw).hexdigest(),
            "field_taxonomy_sha256": hashlib.sha256(field_taxonomy_raw).hexdigest(),
            "mutation_plan_sha256": hashlib.sha256(mutation_plan_raw).hexdigest(),
        }
        (temp_root / "reports" / "closure_audit.json").write_bytes(json_bytes(audit))
        os.replace(temp_root, output)
        return output
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        validate_args(args)
        output = create_project(args)
    except (ValueError, FileExistsError, OSError, sqlite3.Error) as exc:
        parser.error(str(exc))
    result = {
        "created": str(output),
        "contract": str(output / "survey_contract.json"),
        "seed_manifest": str(output / "seed_manifest.json"),
        "field_taxonomy": str(output / "field_taxonomy.json"),
        "judgment_template": str(output / "adjudication" / "judgment_template.json"),
        "ledger": str(output / "ledger.sqlite"),
        "audit": str(output / "reports" / "closure_audit.json"),
        "mutation_plan": str(output / "reports" / "mutation_plan.json"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
