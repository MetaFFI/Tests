#!/usr/bin/env python3
"""
Generate human-readable comparison tables from consolidated.json and complexity.json.

Outputs:
  - results/tables.md: Markdown tables suitable for thesis inclusion
  - Console: Summary tables
"""

import json
import sys
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_json(name: str) -> dict:
    path = RESULTS_DIR / name
    if not path.is_file():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def fmt_ns(ns) -> str:
    """Format nanoseconds to human-readable string."""
    if ns is None:
        return "—"
    ns = float(ns)
    if ns < 1000:
        return f"{ns:.0f} ns"
    elif ns < 1_000_000:
        return f"{ns/1000:.1f} us"
    elif ns < 1_000_000_000:
        return f"{ns/1_000_000:.2f} ms"
    else:
        return f"{ns/1_000_000_000:.2f} s"


def fmt_ns_raw(ns) -> str:
    """Format nanoseconds as raw number with units for table alignment."""
    if ns is None:
        return "—"
    ns = float(ns)
    if ns < 1000:
        return f"{ns:.0f}"
    elif ns < 1_000_000:
        return f"{ns/1000:.1f}"
    else:
        return f"{ns/1_000_000:.2f}"


def get_unit(ns) -> str:
    if ns is None:
        return ""
    ns = float(ns)
    if ns < 1000:
        return "ns"
    elif ns < 1_000_000:
        return "us"
    else:
        return "ms"


def generate_performance_tables(consolidated: dict) -> str:
    """Generate per-scenario performance comparison tables."""

    lines = []
    lines.append("# MetaFFI Cross-Language Performance Comparison\n")
    lines.append("## Benchmark Results Summary\n")
    summary = consolidated['summary']
    lines.append(f"- **Result files**: {summary['total_result_files']} of {summary.get('expected_triples', '?')} expected")
    lines.append(f"- **Missing result files**: {summary.get('missing_result_files', 0)}")
    lines.append(f"- **Benchmarks passed**: {summary['benchmarks']['passed']}")
    lines.append(f"- **Benchmarks failed**: {summary['benchmarks']['failed']}")
    lines.append("")

    # Report missing triples if any
    missing = consolidated.get("missing_triples", [])
    if missing:
        lines.append("### Missing Result Files\n")
        for m in missing:
            lines.append(f"- **{m['host']}->{m['guest']} [{m['mechanism']}]**: `{m['expected_file']}`")
        lines.append("")

    # Report failed benchmarks if any
    failed = consolidated.get("failed_benchmarks", [])
    if failed:
        lines.append("### Failed Benchmarks\n")
        for f_item in failed:
            label = f"- **{f_item['host']}->{f_item['guest']} [{f_item['mechanism']}]** {f_item['scenario']}"
            if f_item.get("error"):
                label += f": {f_item['error'][:100]}"
            lines.append(label)
        lines.append("")

    # Group comparisons by (host, guest)
    pairs: dict[tuple[str, str], list[dict]] = {}
    for comp in consolidated["comparisons"]:
        key = (comp["host"], comp["guest"])
        if key not in pairs:
            pairs[key] = []
        pairs[key].append(comp)

    # For each pair, build a table: scenario vs mechanism
    for (host, guest), scenarios in sorted(pairs.items()):
        lines.append(f"\n## {host.title()} -> {guest.title()}\n")

        # Determine which mechanisms exist for this pair
        all_mechs = set()
        for s in scenarios:
            for k in s:
                if k not in ("host", "guest", "scenario") and s[k] is not None:
                    all_mechs.add(k)

        # Order: metaffi first, then native, then grpc
        native_mechs = [m for m in all_mechs if m not in ("metaffi", "grpc")]
        mech_order = []
        if "metaffi" in all_mechs:
            mech_order.append("metaffi")
        mech_order.extend(sorted(native_mechs))
        if "grpc" in all_mechs:
            mech_order.append("grpc")

        # Header
        header = f"| Scenario | " + " | ".join(f"{m} (mean)" for m in mech_order) + " |"
        sep = "|" + "|".join("---" for _ in range(len(mech_order) + 1)) + "|"
        lines.append(header)
        lines.append(sep)

        # Rows
        for s in sorted(scenarios, key=lambda x: x["scenario"]):
            row = f"| {s['scenario']} |"
            for mech in mech_order:
                data = s.get(mech)
                if data and "mean_ns" in data:
                    row += f" {fmt_ns(data['mean_ns'])} |"
                elif data and "status" in data:
                    row += f" {data['status']} |"
                else:
                    row += " — |"
            lines.append(row)

    return "\n".join(lines)


def generate_complexity_tables(complexity: dict) -> str:
    """Generate code complexity comparison tables."""

    lines = []
    lines.append("\n\n# Code Complexity Comparison\n")

    # Aggregate summary
    agg = complexity["aggregate_by_mechanism"]
    lines.append("## Summary by Mechanism\n")
    lines.append("| Mechanism | Count | Avg SLOC | Avg Benchmark SLOC | Avg Languages | Avg Files | Avg Max CC |")
    lines.append("|---|---|---|---|---|---|---|")
    for mech, stats in sorted(agg.items()):
        lines.append(
            f"| {mech} | {stats['count']} | {stats['avg_source_sloc']:.0f} | "
            f"{stats['avg_benchmark_sloc']:.0f} | {stats['avg_language_count']:.1f} | "
            f"{stats['avg_file_count']:.1f} | {stats['avg_max_cc']:.1f} |"
        )

    # Per-pair comparison
    lines.append("\n## Per-Pair Comparison (Benchmark-Only SLOC)\n")
    lines.append("Excludes MetaFFI correctness tests for fair cross-mechanism comparison.\n")
    lines.append("| Pair | MetaFFI | Native | gRPC |")
    lines.append("|---|---|---|---|")

    for comp in complexity["pair_comparisons"]:
        host = comp["host"]
        guest = comp["guest"]
        mechs = comp["mechanisms"]

        metaffi_sloc = mechs.get("metaffi", {}).get("benchmark_only_sloc", "—")
        grpc_sloc = mechs.get("grpc", {}).get("benchmark_only_sloc", "—")

        native_sloc = "—"
        native_name = ""
        for m, d in mechs.items():
            if m not in ("metaffi", "grpc"):
                native_sloc = d.get("benchmark_only_sloc", "—")
                native_name = m
                break

        native_label = f"{native_sloc} ({native_name})" if native_name else str(native_sloc)
        lines.append(f"| {host}->{guest} | {metaffi_sloc} | {native_label} | {grpc_sloc} |")

    # Languages required
    lines.append("\n## Languages Required per Pair\n")
    lines.append("| Pair | MetaFFI | Native | gRPC |")
    lines.append("|---|---|---|---|")

    for comp in complexity["pair_comparisons"]:
        host = comp["host"]
        guest = comp["guest"]
        mechs = comp["mechanisms"]

        metaffi_langs = mechs.get("metaffi", {}).get("languages", [])
        grpc_langs = mechs.get("grpc", {}).get("languages", [])

        native_langs = []
        for m, d in mechs.items():
            if m not in ("metaffi", "grpc"):
                native_langs = d.get("languages", [])
                break

        lines.append(
            f"| {host}->{guest} | {len(metaffi_langs)} ({', '.join(metaffi_langs)}) | "
            f"{len(native_langs)} ({', '.join(native_langs)}) | "
            f"{len(grpc_langs)} ({', '.join(grpc_langs)}) |"
        )

    return "\n".join(lines)


def main() -> int:
    consolidated = load_json("consolidated.json")
    complexity = load_json("complexity.json")

    perf_tables = generate_performance_tables(consolidated)
    complexity_tables = generate_complexity_tables(complexity)

    output = perf_tables + "\n" + complexity_tables + "\n"

    # Write to file
    output_path = RESULTS_DIR / "tables.md"
    with open(output_path, "w") as f:
        f.write(output)

    print(f"Tables written to {output_path}")
    print()
    print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
