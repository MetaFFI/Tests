#!/usr/bin/env python3
"""
Consolidates per-pair JSON result files into a single consolidated report.

Reads all results/<host>_to_<guest>_<mechanism>.json files and produces
results/consolidated.json with cross-pair comparison data.

FAIL-FAST: If any result file is malformed, this script aborts immediately.

Explicitly reports:
  - Missing result files (expected triples with no data)
  - Failed benchmarks/correctness within existing result files
  - Scenarios with no data across all mechanisms for a pair
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RESULTS_DIR = Path(__file__).resolve().parent / "results"
CONSOLIDATED_FILE = RESULTS_DIR / "consolidated.json"

# All 18 expected (host, guest, mechanism) triples
HOSTS = ["go", "python3", "java"]

NATIVE_MECHANISMS = {
    ("go", "python3"): "cpython",
    ("go", "java"): "jni",
    ("python3", "go"): "ctypes",
    ("python3", "java"): "jpype",
    ("java", "go"): "jni",
    ("java", "python3"): "jep",
}

ALL_EXPECTED_TRIPLES: list[tuple[str, str, str]] = []
for h in HOSTS:
    for g in HOSTS:
        if h == g:
            continue
        ALL_EXPECTED_TRIPLES.append((h, g, "metaffi"))
        ALL_EXPECTED_TRIPLES.append((h, g, NATIVE_MECHANISMS[(h, g)]))
        ALL_EXPECTED_TRIPLES.append((h, g, "grpc"))


class ConsolidationError(Exception):
    """Raised when a result file cannot be processed."""


def load_result_files() -> list[dict[str, Any]]:
    """Load all per-pair JSON files from the results directory."""

    result_files = sorted(RESULTS_DIR.glob("*_to_*.json"))
    if not result_files:
        raise ConsolidationError(f"No result files found in {RESULTS_DIR}")

    results = []
    for path in result_files:
        if path.name == "consolidated.json":
            continue

        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConsolidationError(f"Malformed JSON in {path}: {e}")

        # Validate required top-level fields
        if "metadata" not in data:
            raise ConsolidationError(f"Missing 'metadata' in {path}")

        results.append(data)

    return results


def _native_mechanisms_for_pair(host: str, guest: str) -> list[str]:
    """Return the native-direct mechanism name(s) for a (host, guest) pair."""
    return [NATIVE_MECHANISMS[(host, guest)]] if (host, guest) in NATIVE_MECHANISMS else []


def _find_benchmark(result: dict, scenario_key: str) -> dict[str, Any] | None:
    """Find a benchmark entry matching a scenario key (possibly with data_size suffix)."""

    for b in result.get("benchmarks", []):
        key = b["scenario"]
        if b.get("data_size") is not None:
            key += f"_{b['data_size']}"
        if key == scenario_key:
            return b

    return None


def compute_comparison_table(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Build a cross-pair comparison table.

    For each (host, guest, scenario) group, compare MetaFFI vs. native vs. gRPC
    total call times. Missing data is explicitly marked.
    """

    # Index results by (host, guest, mechanism)
    indexed: dict[tuple[str, str, str], dict] = {}
    for r in results:
        meta = r["metadata"]
        key = (meta["host"], meta["guest"], meta["mechanism"])
        indexed[key] = r

    # Collect all unique (host, guest) pairs from expected triples
    pairs = sorted({(h, g) for h, g, _ in ALL_EXPECTED_TRIPLES})

    # Collect scenarios per (host, guest) pair — only scenarios that exist
    # in at least one mechanism for that pair
    pair_scenarios: dict[tuple[str, str], set[str]] = {p: set() for p in pairs}
    for r in results:
        meta = r["metadata"]
        pair_key = (meta["host"], meta["guest"])
        if pair_key not in pair_scenarios:
            continue
        for b in r.get("benchmarks", []):
            scenario_key = b["scenario"]
            if b.get("data_size") is not None:
                scenario_key += f"_{b['data_size']}"
            pair_scenarios[pair_key].add(scenario_key)

    comparisons = []

    for host, guest in pairs:
        for scenario in sorted(pair_scenarios[(host, guest)]):
            row: dict[str, Any] = {
                "host": host,
                "guest": guest,
                "scenario": scenario,
            }

            # For each mechanism, find the matching benchmark
            for mechanism in ["metaffi", *_native_mechanisms_for_pair(host, guest), "grpc"]:
                result = indexed.get((host, guest, mechanism))
                if result is None:
                    # Explicitly mark as MISSING (no result file)
                    row[mechanism] = {"status": "MISSING", "reason": "no result file"}
                    continue

                benchmark = _find_benchmark(result, scenario)
                if benchmark is None:
                    # Result file exists but no data for this scenario
                    row[mechanism] = {"status": "MISSING", "reason": "scenario not in result file"}
                    continue

                phases = benchmark.get("phases") or {}
                total_stats = phases.get("total")
                if total_stats:
                    row[mechanism] = {
                        "mean_ns": total_stats.get("mean_ns"),
                        "median_ns": total_stats.get("median_ns"),
                        "p95_ns": total_stats.get("p95_ns"),
                        "status": benchmark.get("status"),
                    }
                else:
                    row[mechanism] = {"status": benchmark.get("status", "FAIL")}

            comparisons.append(row)

    return comparisons


def find_missing_triples(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Identify expected triples with no result file."""

    present = set()
    for r in results:
        meta = r["metadata"]
        present.add((meta["host"], meta["guest"], meta["mechanism"]))

    missing = []
    for host, guest, mechanism in ALL_EXPECTED_TRIPLES:
        if (host, guest, mechanism) not in present:
            missing.append({
                "host": host,
                "guest": guest,
                "mechanism": mechanism,
                "expected_file": f"{host}_to_{guest}_{mechanism}.json",
            })

    return missing


def find_failed_benchmarks(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect all benchmark entries with FAIL status across all result files."""

    failures = []
    for r in results:
        meta = r["metadata"]
        for b in r.get("benchmarks", []):
            if b.get("status") == "FAIL":
                scenario_key = b["scenario"]
                if b.get("data_size") is not None:
                    scenario_key += f"_{b['data_size']}"
                failures.append({
                    "host": meta["host"],
                    "guest": meta["guest"],
                    "mechanism": meta["mechanism"],
                    "scenario": scenario_key,
                    "error": b.get("error", ""),
                })

    return failures


def build_summary(results: list[dict[str, Any]],
                  missing_triples: list[dict],
                  failed_benchmarks: list[dict]) -> dict[str, Any]:
    """Build top-level summary statistics."""

    total_correctness_pass = 0
    total_correctness_fail = 0
    total_benchmarks_pass = 0
    total_benchmarks_fail = 0

    for r in results:
        correctness = r.get("correctness")
        if correctness is not None:
            if correctness.get("status") == "PASS":
                total_correctness_pass += 1
            elif correctness.get("status") == "FAIL":
                total_correctness_fail += 1

        for b in r.get("benchmarks", []):
            if b.get("status") == "PASS":
                total_benchmarks_pass += 1
            elif b.get("status") == "FAIL":
                total_benchmarks_fail += 1

    return {
        "expected_triples": len(ALL_EXPECTED_TRIPLES),
        "total_result_files": len(results),
        "missing_result_files": len(missing_triples),
        "correctness": {
            "passed": total_correctness_pass,
            "failed": total_correctness_fail,
        },
        "benchmarks": {
            "passed": total_benchmarks_pass,
            "failed": total_benchmarks_fail,
        },
    }


def main() -> int:
    try:
        results = load_result_files()
    except ConsolidationError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        return 1

    print(f"Loaded {len(results)} result file(s) (expected: {len(ALL_EXPECTED_TRIPLES)}).")

    # Identify missing and failed data
    missing_triples = find_missing_triples(results)
    failed_benchmarks = find_failed_benchmarks(results)

    comparisons = compute_comparison_table(results)
    summary = build_summary(results, missing_triples, failed_benchmarks)

    consolidated = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "missing_triples": missing_triples,
        "failed_benchmarks": failed_benchmarks,
        "comparisons": comparisons,
        "results": results,
    }

    CONSOLIDATED_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CONSOLIDATED_FILE, "w") as f:
        json.dump(consolidated, f, indent=2)

    # Print report
    print(f"Consolidated report written to {CONSOLIDATED_FILE}")
    print()
    print(f"  Expected triples:  {summary['expected_triples']}")
    print(f"  Result files:      {summary['total_result_files']}")
    print(f"  Missing files:     {summary['missing_result_files']}")
    print(f"  Correctness:       {summary['correctness']['passed']} passed, {summary['correctness']['failed']} failed")
    print(f"  Benchmarks:        {summary['benchmarks']['passed']} passed, {summary['benchmarks']['failed']} failed")

    # Explicitly report missing triples
    if missing_triples:
        print()
        print("MISSING RESULT FILES (no data):")
        for m in missing_triples:
            print(f"  {m['host']}->{m['guest']} [{m['mechanism']}]  expected: {m['expected_file']}")

    # Explicitly report failed benchmarks
    if failed_benchmarks:
        print()
        print("FAILED BENCHMARKS:")
        for f_item in failed_benchmarks:
            label = f"  {f_item['host']}->{f_item['guest']} [{f_item['mechanism']}] {f_item['scenario']}"
            if f_item.get("error"):
                label += f"  -- {f_item['error'][:80]}"
            print(label)

    # Count MISSING entries in comparison table
    missing_data_points = 0
    for row in comparisons:
        for key, val in row.items():
            if key in ("host", "guest", "scenario"):
                continue
            if isinstance(val, dict) and val.get("status") == "MISSING":
                missing_data_points += 1

    if missing_data_points > 0:
        print()
        print(f"  Comparison table has {missing_data_points} MISSING data points "
              f"(out of {len(comparisons) * 3} total cells)")

    has_issues = (summary["missing_result_files"] > 0
                  or summary["correctness"]["failed"] > 0
                  or summary["benchmarks"]["failed"] > 0)

    # Generate tables
    tables_script = Path(__file__).resolve().parent / "generate_tables.py"
    if tables_script.is_file():
        print()
        import subprocess
        subprocess.run([sys.executable, str(tables_script)], cwd=str(tables_script.parent))

    if has_issues:
        print()
        print("WARNING: Issues detected. See details above.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
