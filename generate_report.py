#!/usr/bin/env python3
"""
Generate a thesis-oriented Markdown report from the consolidated test outputs.

Inputs:
  - results/tables.md
  - results/consolidated.json
  - results/complexity.json

Outputs:
  - results/report.md
  - results/report_figures/*.png

FAIL-FAST:
  - Any malformed table, unknown format, missing file, or plotting failure aborts
    report generation immediately.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


RESULTS_DIR = Path(__file__).resolve().parent / "results"
TABLES_FILE = RESULTS_DIR / "tables.md"
CONSOLIDATED_FILE = RESULTS_DIR / "consolidated.json"
COMPLEXITY_FILE = RESULTS_DIR / "complexity.json"
REPORT_FILE = RESULTS_DIR / "report.md"
FIGURES_DIR = RESULTS_DIR / "report_figures"


class ReportGenerationError(Exception):
    """Raised on any report-generation issue (fail-fast)."""


@dataclass
class TableBlock:
    title: str
    header: list[str]
    rows: list[list[str]]
    markdown: str


DEDICATED_PACKAGE_NAMES = {
    ("go", "java"): "CGo+JNI",
    ("go", "python3"): "CGo+CPython",
    ("java", "go"): "JNI+CGo",
    ("java", "python3"): "JEP",
    ("python3", "go"): "ctypes",
    ("python3", "java"): "JPype",
}

LATENCY_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*(ns|us|µs|μs|ms|s)\s*$", re.IGNORECASE)
LEADING_NUM_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)")
PAIR_TITLE_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*->\s*([A-Za-z0-9_]+)\s*$")


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise ReportGenerationError(f"Missing required input file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ReportGenerationError(f"Malformed JSON in {path}: {e}") from e


def split_markdown_row(line: str) -> list[str]:
    line = line.strip()
    if not (line.startswith("|") and line.endswith("|")):
        raise ReportGenerationError(f"Invalid markdown table row (must start/end with '|'): {line}")
    parts = [p.strip() for p in line[1:-1].split("|")]
    if any(p == "" for p in parts):
        # Empty cells are valid only for separators; data rows must be explicit.
        return parts
    return parts


def is_separator_row(line: str) -> bool:
    line = line.strip()
    if not (line.startswith("|") and line.endswith("|")):
        return False
    cells = [c.strip() for c in line[1:-1].split("|")]
    if not cells:
        return False
    return all(c and set(c) <= {"-", ":"} for c in cells)


def parse_tables(markdown_text: str) -> list[TableBlock]:
    lines = markdown_text.splitlines()
    current_heading = ""
    tables: list[TableBlock] = []
    i = 0

    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()

        if stripped.startswith("#"):
            current_heading = stripped.lstrip("#").strip()
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and is_separator_row(lines[i + 1]):
            table_lines = [lines[i], lines[i + 1]]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1

            header = split_markdown_row(table_lines[0])
            sep = split_markdown_row(table_lines[1])
            if len(header) != len(sep):
                raise ReportGenerationError(
                    f"Table header/separator column mismatch under '{current_heading}'"
                )

            rows: list[list[str]] = []
            for row_line in table_lines[2:]:
                row = split_markdown_row(row_line)
                if len(row) != len(header):
                    raise ReportGenerationError(
                        f"Table row has {len(row)} columns, expected {len(header)} under '{current_heading}'"
                    )
                rows.append(row)

            if not current_heading:
                raise ReportGenerationError("Encountered table without preceding heading")
            if not rows:
                raise ReportGenerationError(f"Table '{current_heading}' has no data rows")

            tables.append(
                TableBlock(
                    title=current_heading,
                    header=header,
                    rows=rows,
                    markdown="\n".join(table_lines),
                )
            )
            continue

        i += 1

    if not tables:
        raise ReportGenerationError("No markdown tables found in tables.md")
    return tables


def _convert_us_to_micro_sign(text: str) -> str:
    return re.sub(r"(\d+(?:\.\d+)?)\s+us\b", r"\1 µs", text)


def _parse_sized_scenario(scenario: str, prefix: str) -> int | None:
    marker = f"{prefix}_"
    if not scenario.startswith(marker):
        return None
    suffix = scenario[len(marker):]
    if not suffix.isdigit():
        raise ReportGenerationError(f"Invalid sized scenario key '{scenario}' (expected integer suffix)")
    return int(suffix)


def scenario_display_name(host: str, guest: str, scenario: str) -> str:
    pair = (host.strip().lower(), guest.strip().lower())
    base_map = {
        "void_call": "void_call_void_void",
        "primitive_echo": "primitive_echo_int64_int64_to_float64",
        "string_echo": "string_echo_string8_utf8",
        "object_method": "object_method_ctor_plus_instance_call",
        "callback": "callback_callable_int_int_to_int",
        "error_propagation": "error_propagation_exception_path",
    }
    if scenario in base_map:
        return base_map[scenario]

    arr_sum_size = _parse_sized_scenario(scenario, "array_sum")
    if arr_sum_size is not None:
        int32_pairs = {("go", "java"), ("python3", "java")}
        int64_pairs = {("go", "python3"), ("java", "python3")}
        if pair in int32_pairs:
            return f"array_sum_ragged_int32_2d_n{arr_sum_size}"
        if pair in int64_pairs:
            return f"array_sum_ragged_int64_2d_n{arr_sum_size}"
        raise ReportGenerationError(
            f"array_sum scenario found for unsupported pair {host}->{guest}; add explicit mapping"
        )

    packed_arr_sum_size = _parse_sized_scenario(scenario, "packed_array_sum")
    if packed_arr_sum_size is not None:
        int32_pairs = {("go", "java"), ("python3", "java")}
        int64_pairs = {("go", "python3"), ("java", "python3")}
        if pair in int32_pairs:
            return f"packed_array_sum_int32_1d_n{packed_arr_sum_size}"
        if pair in int64_pairs:
            return f"packed_array_sum_int64_1d_n{packed_arr_sum_size}"
        raise ReportGenerationError(
            f"packed_array_sum scenario found for unsupported pair {host}->{guest}; add explicit mapping"
        )

    arr_echo_size = _parse_sized_scenario(scenario, "array_echo")
    if arr_echo_size is not None:
        return f"array_echo_uint8_1d_n{arr_echo_size}"

    any_echo_size = _parse_sized_scenario(scenario, "any_echo")
    if any_echo_size is not None:
        return f"any_echo_mixed_dynamic_n{any_echo_size}"

    return scenario


def _render_markdown_table(header: list[str], rows: list[list[str]]) -> str:
    if not header:
        raise ReportGenerationError("Cannot render markdown table with empty header")
    sep = "|" + "|".join("---" for _ in header) + "|"
    lines = ["| " + " | ".join(header) + " |", sep]
    for row in rows:
        if len(row) != len(header):
            raise ReportGenerationError("Cannot render markdown table: row/header length mismatch")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def extract_benchmark_protocol(
    consolidated: dict,
) -> tuple[set[tuple[int, int, int, int, int]], list[tuple[str, str, str, int, int, int, int, int]]]:
    results = consolidated.get("results")
    if not isinstance(results, list) or not results:
        raise ReportGenerationError("consolidated.json missing non-empty 'results' for benchmark protocol extraction")

    entries: list[tuple[str, str, str, int, int, int, int, int]] = []
    for idx, result in enumerate(results, start=1):
        if not isinstance(result, dict):
            raise ReportGenerationError(f"Invalid result entry type at index {idx}")
        meta = result.get("metadata")
        if not isinstance(meta, dict):
            raise ReportGenerationError(f"Missing metadata in result entry index {idx}")
        for key in ("host", "guest", "mechanism", "config"):
            if key not in meta:
                raise ReportGenerationError(f"Result metadata missing '{key}' in entry index {idx}")
        config = meta["config"]
        if not isinstance(config, dict):
            raise ReportGenerationError(f"Result metadata.config must be object in entry index {idx}")
        for key in ("warmup_iterations", "measured_iterations"):
            if key not in config:
                raise ReportGenerationError(f"Result metadata.config missing '{key}' in entry index {idx}")

        try:
            warmup = int(config["warmup_iterations"])
            measured = int(config["measured_iterations"])
        except (TypeError, ValueError) as e:
            raise ReportGenerationError(
                f"Invalid warmup/measured iteration values in entry index {idx}: {config}"
            ) from e
        if warmup < 0 or measured <= 0:
            raise ReportGenerationError(
                f"Invalid iteration counts in entry index {idx}: warmup={warmup}, measured={measured}"
            )

        host = str(meta["host"]).strip().lower()
        guest = str(meta["guest"]).strip().lower()
        mechanism = normalize_mechanism_label(str(meta["mechanism"]))
        repeat_count_raw = config.get("repeat_count", 1)
        batch_min_raw = config.get("batch_min_elapsed_ns", 0)
        batch_max_raw = config.get("batch_max_calls", 0)
        try:
            repeat_count = int(repeat_count_raw)
            batch_min = int(batch_min_raw)
            batch_max = int(batch_max_raw)
        except (TypeError, ValueError) as e:
            raise ReportGenerationError(
                f"Invalid repeat/batch values in entry index {idx}: {config}"
            ) from e
        if repeat_count <= 0 or batch_min < 0 or batch_max < 0:
            raise ReportGenerationError(
                f"Invalid repeat/batch counts in entry index {idx}: "
                f"repeat={repeat_count}, batch_min={batch_min}, batch_max={batch_max}"
            )

        entries.append((host, guest, mechanism, warmup, measured, repeat_count, batch_min, batch_max))

    unique_configs = {(w, m, r, bmin, bmax) for _, _, _, w, m, r, bmin, bmax in entries}
    entries.sort(key=lambda e: (e[0], e[1], e[2]))
    return unique_configs, entries


def format_latency_ns(ns: float) -> str:
    if ns < 1:
        return f"{ns:.3f} ns"
    if ns < 1000:
        return f"{ns:.1f} ns"
    if ns < 1_000_000:
        return f"{ns/1000.0:.1f} µs"
    if ns < 1_000_000_000:
        return f"{ns/1_000_000.0:.2f} ms"
    return f"{ns/1_000_000_000.0:.2f} s"


def build_repeat_analysis_tables(consolidated: dict) -> list[str]:
    results = consolidated.get("results")
    if not isinstance(results, list):
        raise ReportGenerationError("consolidated.json missing 'results' for repeat analysis")

    blocks: list[str] = []
    for r in sorted(
        (x for x in results if isinstance(x, dict)),
        key=lambda x: (
            str(x.get("metadata", {}).get("host", "")),
            str(x.get("metadata", {}).get("guest", "")),
            str(x.get("metadata", {}).get("mechanism", "")),
        ),
    ):
        meta = r.get("metadata")
        if not isinstance(meta, dict):
            continue
        host = str(meta.get("host", "")).strip().lower()
        guest = str(meta.get("guest", "")).strip().lower()
        mechanism = str(meta.get("mechanism", "")).strip().lower()
        benches = r.get("benchmarks")
        if not isinstance(benches, list):
            continue

        rows: list[tuple[str, list[float], float, float]] = []
        max_repeat = 0
        for b in benches:
            if not isinstance(b, dict):
                continue
            rep = b.get("repeat_analysis")
            if not isinstance(rep, dict):
                continue
            means = rep.get("repeat_means_ns")
            if not isinstance(means, list) or not means:
                continue
            repeat_means: list[float] = []
            for v in means:
                repeat_means.append(float(v))
            max_repeat = max(max_repeat, len(repeat_means))

            scenario = b.get("scenario")
            if not isinstance(scenario, str):
                raise ReportGenerationError(f"Repeat-analysis benchmark missing scenario in {host}->{guest}[{mechanism}]")
            data_size = b.get("data_size")
            scenario_key = scenario
            if data_size is not None:
                scenario_key = f"{scenario}_{data_size}"
            scenario_display = scenario_display_name(host, guest, scenario_key)

            mean_of_means = sum(repeat_means) / len(repeat_means)
            global_mean = rep.get("global_mean_ns")
            if global_mean is None:
                phases = b.get("phases", {})
                total = phases.get("total", {}) if isinstance(phases, dict) else {}
                global_mean = total.get("mean_ns")
            if global_mean is None:
                raise ReportGenerationError(f"Missing global mean in repeat analysis for {scenario_key}")

            rows.append((scenario_display, repeat_means, mean_of_means, float(global_mean)))

        if not rows:
            continue

        header = ["Scenario"] + [f"run_{i}_mean" for i in range(1, max_repeat + 1)] + [
            "mean_of_repeat_means",
            "global_pooled_mean",
        ]
        table_rows: list[list[str]] = []
        for scenario_display, repeat_means, mean_of_means, global_mean in rows:
            row = [scenario_display]
            for i in range(max_repeat):
                if i < len(repeat_means):
                    row.append(format_latency_ns(repeat_means[i]))
                else:
                    row.append("—")
            row.append(format_latency_ns(mean_of_means))
            row.append(format_latency_ns(global_mean))
            table_rows.append(row)

        block = []
        block.append(f"### {host} -> {guest} [{mechanism}]")
        block.append("")
        block.append(_render_markdown_table(header, table_rows))
        block.append("")
        blocks.append("\n".join(block))

    return blocks


def build_signature_matrix_rows() -> list[list[str]]:
    return [
        ["go->java", "array_sum_ragged_int32_2d_n<size>", "int32[][] -> int32", "string_echo_string8_utf8"],
        ["go->java", "packed_array_sum_int32_1d_n<size>", "int32_packed[] -> int32", "—"],
        ["python3->java", "array_sum_ragged_int32_2d_n<size>", "int32[][] -> int32", "string_echo_string8_utf8"],
        ["go->python3", "array_sum_ragged_int64_2d_n<size>", "int64[][] -> int64", "string_echo_string8_utf8"],
        ["go->python3", "packed_array_sum_int64_1d_n<size>", "int64_packed[] -> int64", "—"],
        ["java->python3", "array_sum_ragged_int64_2d_n<size>", "int64[][] -> int64", "string_echo_string8_utf8"],
        ["java->go", "array_echo_uint8_1d_n<size>", "uint8[] -> uint8[]", "string_echo_string8_utf8"],
        ["python3->go", "array_echo_uint8_1d_n<size>", "uint8[] -> uint8[]", "string_echo_string8_utf8"],
    ]


def format_table_for_report(block: TableBlock, table_index: int) -> str:
    header = [h for h in block.header]
    rows = [[c for c in r] for r in block.rows]

    # Rename "Native" to "Dedicated package baseline" in complexity tables
    if table_index in (7, 8, 9):
        for i, h in enumerate(header):
            if h.strip().lower() == "native":
                header[i] = "Dedicated package baseline"
        for r in rows:
            if r and r[0].strip().lower() == "native":
                r[0] = "dedicated package baseline"

    # Drop "Avg SLOC" column from Table 7 (Summary by Mechanism)
    if table_index == 7:
        avg_sloc_idx = None
        for i, h in enumerate(header):
            if h.strip() == "Avg SLOC":
                avg_sloc_idx = i
                break
        if avg_sloc_idx is not None:
            header = header[:avg_sloc_idx] + header[avg_sloc_idx + 1:]
            rows = [r[:avg_sloc_idx] + r[avg_sloc_idx + 1:] for r in rows]

    if header and header[0].strip().lower() == "scenario":
        host, guest = parse_pair_title(block.title)
        for r in rows:
            r[0] = scenario_display_name(host, guest, r[0])

    for r in rows:
        for i, cell in enumerate(r):
            r[i] = _convert_us_to_micro_sign(cell)

    return _render_markdown_table(header, rows)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    return slug.strip("_") or "table"


def parse_latency_to_ns(cell: str, context: str, allow_missing: bool = False) -> float | None:
    if allow_missing and cell.strip().upper() in ("MISSING", "FAIL"):
        return None
    m = LATENCY_RE.match(cell)
    if not m:
        raise ReportGenerationError(f"Expected latency value in '{context}', got '{cell}'")
    value = float(m.group(1))
    unit = m.group(2).lower()
    if unit == "ns":
        return value
    if unit in ("us", "µs", "μs"):
        return value * 1_000.0
    if unit == "ms":
        return value * 1_000_000.0
    if unit == "s":
        return value * 1_000_000_000.0
    raise ReportGenerationError(f"Unsupported latency unit '{unit}' in '{context}'")


def parse_leading_number(cell: str, context: str, allow_missing: bool = False) -> float:
    if allow_missing and cell.strip().upper() in ("MISSING", "FAIL"):
        return float("nan")
    m = LEADING_NUM_RE.match(cell)
    if not m:
        raise ReportGenerationError(f"Expected numeric-leading value in '{context}', got '{cell}'")
    return float(m.group(1))


def require_positive(values: list[float], context: str) -> None:
    finite = [v for v in values if not math.isnan(v)]
    if not finite:
        raise ReportGenerationError(f"No numeric values found for {context}")
    if any(v < 0 for v in finite):
        raise ReportGenerationError(f"Negative values not supported for {context}")


def parse_pair_title(title: str) -> tuple[str, str]:
    m = PAIR_TITLE_RE.match(title)
    if not m:
        raise ReportGenerationError(f"Cannot parse pair title '{title}'")
    return m.group(1).strip().lower(), m.group(2).strip().lower()


def normalize_mechanism_label(label: str) -> str:
    return label.strip().lower()


def build_average_lookup(consolidated: dict) -> dict[tuple[str, str], dict[str, float]]:
    entries = consolidated.get("mechanism_averages_by_pair")
    if not isinstance(entries, list):
        raise ReportGenerationError("consolidated.json missing 'mechanism_averages_by_pair'")

    lookup: dict[tuple[str, str], dict[str, float]] = {}
    for e in entries:
        if not isinstance(e, dict):
            raise ReportGenerationError("Invalid average entry type in consolidated.json")
        for key in ("host", "guest", "mechanism", "average_mean_ns"):
            if key not in e:
                raise ReportGenerationError(f"Average entry missing key '{key}': {e}")

        host = str(e["host"]).strip().lower()
        guest = str(e["guest"]).strip().lower()
        mechanism = normalize_mechanism_label(str(e["mechanism"]))
        try:
            avg = float(e["average_mean_ns"])
        except (TypeError, ValueError):
            raise ReportGenerationError(f"Invalid average_mean_ns in entry: {e}")

        lookup.setdefault((host, guest), {})[mechanism] = avg

    if not lookup:
        raise ReportGenerationError("No mechanism averages found in consolidated.json")
    return lookup


def plot_grouped_bars(
    categories: list[str],
    series_labels: list[str],
    series_values: list[list[float]],
    title: str,
    ylabel: str,
    output_path: Path,
    log_y: bool = False,
    avg_lines: dict[str, float] | None = None,
) -> None:
    if len(series_labels) != len(series_values):
        raise ReportGenerationError(f"Series label/value mismatch for '{title}'")
    if not categories:
        raise ReportGenerationError(f"No categories for '{title}'")

    for vals in series_values:
        if len(vals) != len(categories):
            raise ReportGenerationError(f"Series length mismatch for '{title}'")

    width = 0.8 / max(1, len(series_labels))
    x_positions = list(range(len(categories)))

    fig_width = max(10.0, min(20.0, len(categories) * 1.2))
    fig, ax = plt.subplots(figsize=(fig_width, 6.0))
    colors = list(plt.get_cmap("tab10").colors)

    for idx, (label, vals) in enumerate(zip(series_labels, series_values)):
        color = colors[idx % len(colors)]
        offset = (idx - (len(series_labels) - 1) / 2.0) * width
        xs = [x + offset for x in x_positions]
        ax.bar(xs, vals, width=width, label=label, color=color)
        if avg_lines is not None:
            if label not in avg_lines:
                raise ReportGenerationError(f"Missing average line for series '{label}' in '{title}'")
            avg = avg_lines[label]
            avg_plot = 1.0 if log_y and avg <= 0 else avg
            ax.axhline(avg_plot, color=color, linestyle="--", linewidth=1.5, alpha=0.9,
                       label=f"{label} avg")

    ax.set_ylabel(ylabel)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(categories, rotation=35, ha="right")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    if log_y:
        finite_vals = [v for vals in series_values for v in vals if not math.isnan(v)]
        if not finite_vals:
            raise ReportGenerationError(f"Log-scale chart has no numeric values in '{title}'")
        if any(v <= 0 for v in finite_vals):
            raise ReportGenerationError(f"Log-scale chart has non-positive values in '{title}'")
        ax.set_yscale("log")

    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def _extract_complexity_data(block: TableBlock) -> tuple[list[str], list[str], list[list[float]]]:
    """Extract mechanism labels, metric labels, and per-mechanism values from the complexity table.

    Returns (mechanism_labels, metric_labels, series_values) where
    series_values[i] is the list of metric values for mechanism i.
    """
    mechanism_labels = [
        ("dedicated package baseline" if r[0].strip().lower() == "native" else r[0])
        for r in block.rows
    ]
    col_labels = block.header[1:]

    wanted = ["Avg Benchmark SLOC", "Avg Languages", "Avg Max CC"]
    selected_col_indices = []
    for w in wanted:
        try:
            selected_col_indices.append(col_labels.index(w))
        except ValueError as e:
            raise ReportGenerationError(
                f"Missing required complexity column '{w}' for bar chart"
            ) from e

    metric_labels = [col_labels[i] for i in selected_col_indices]

    series_values: list[list[float]] = []
    for r_idx, row in enumerate(block.rows):
        vals: list[float] = []
        for in_idx in selected_col_indices:
            cell = row[1:][in_idx]
            v = parse_leading_number(cell, f"{block.title} row {r_idx + 1}")
            vals.append(v)
        series_values.append(vals)

    if not series_values:
        raise ReportGenerationError(f"Empty bar chart source in '{block.title}'")

    return mechanism_labels, metric_labels, series_values


def plot_complexity_bars(block: TableBlock, output_path: Path) -> None:
    """Generate complexity summary figures:

    1. Small multiples (3 subplots side-by-side) — the main figure.
    2. Three individual per-metric figures (07a/07b/07c).
    3. Percent-of-max normalized bar chart with raw annotations (07d).
    """
    mechanism_labels, metric_labels, series_values = _extract_complexity_data(block)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    y_labels = ["SLOC", "Languages", "Cyclomatic complexity"]

    # ---- (1) Small multiples: 3 subplots in one figure ----
    fig, axes = plt.subplots(1, 3, figsize=(14.0, 5.0))

    for col_idx, (ax, metric, ylabel) in enumerate(zip(axes, metric_labels, y_labels)):
        vals = [series_values[m_idx][col_idx] for m_idx in range(len(mechanism_labels))]
        bar_colors = [colors[i % len(colors)] for i in range(len(mechanism_labels))]
        bars = ax.bar(mechanism_labels, vals, color=bar_colors, width=0.6)

        # Annotate raw values
        for bar_obj, val in zip(bars, vals):
            ax.text(
                bar_obj.get_x() + bar_obj.get_width() / 2.0,
                bar_obj.get_height(),
                f"{val:.1f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold",
            )

        ax.set_title(metric, fontsize=11)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.25)
        ax.set_ylim(0, max(vals) * 1.18)
        ax.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)

    # ---- (2) Individual per-metric figures ----
    suffixes = ["a", "b", "c"]
    slug_names = ["avg_benchmark_sloc", "avg_languages", "avg_max_cc"]

    for col_idx, (suffix, slug, metric, ylabel) in enumerate(
        zip(suffixes, slug_names, metric_labels, y_labels)
    ):
        ind_path = output_path.parent / f"{output_path.stem}{suffix}_{slug}.png"
        vals = [series_values[m_idx][col_idx] for m_idx in range(len(mechanism_labels))]
        bar_colors = [colors[i % len(colors)] for i in range(len(mechanism_labels))]

        fig_ind, ax_ind = plt.subplots(figsize=(6.0, 5.0))
        bars = ax_ind.bar(mechanism_labels, vals, color=bar_colors, width=0.5)

        for bar_obj, val in zip(bars, vals):
            ax_ind.text(
                bar_obj.get_x() + bar_obj.get_width() / 2.0,
                bar_obj.get_height(),
                f"{val:.1f}",
                ha="center", va="bottom", fontsize=10, fontweight="bold",
            )

        ax_ind.set_ylabel(ylabel)
        ax_ind.grid(axis="y", alpha=0.25)
        ax_ind.set_ylim(0, max(vals) * 1.18)
        ax_ind.tick_params(axis="x", rotation=15)

        fig_ind.tight_layout()
        fig_ind.savefig(ind_path, dpi=170)
        plt.close(fig_ind)

    # ---- (3) Percent-of-max normalized bars with raw value annotations ----
    norm_path = output_path.parent / f"{output_path.stem}d_normalized.png"

    # Compute per-metric max for normalization
    num_metrics = len(metric_labels)
    col_max = [
        max(series_values[m_idx][c] for m_idx in range(len(mechanism_labels)))
        for c in range(num_metrics)
    ]

    fig_norm, ax_norm = plt.subplots(figsize=(10.0, 5.5))
    width = 0.8 / max(1, len(mechanism_labels))
    x_positions = list(range(num_metrics))

    for m_idx, (label, vals) in enumerate(zip(mechanism_labels, series_values)):
        color = colors[m_idx % len(colors)]
        offset = (m_idx - (len(mechanism_labels) - 1) / 2.0) * width
        xs = [x + offset for x in x_positions]

        # Normalize to percentage of column max
        norm_vals = [
            (v / col_max[c] * 100.0) if col_max[c] > 0 else 0.0
            for c, v in enumerate(vals)
        ]
        bars = ax_norm.bar(xs, norm_vals, width=width, label=label, color=color)

        # Annotate with raw values
        for bar_obj, raw_val in zip(bars, vals):
            ax_norm.text(
                bar_obj.get_x() + bar_obj.get_width() / 2.0,
                bar_obj.get_height() + 1.0,
                f"{raw_val:.1f}",
                ha="center", va="bottom", fontsize=8,
            )

    ax_norm.set_ylabel("% of maximum")
    ax_norm.set_xticks(x_positions)
    ax_norm.set_xticklabels(metric_labels)
    ax_norm.set_ylim(0, 115)
    ax_norm.legend()
    ax_norm.grid(axis="y", alpha=0.25)

    fig_norm.tight_layout()
    fig_norm.savefig(norm_path, dpi=170)
    plt.close(fig_norm)


def render_figure_for_table(
    block: TableBlock,
    index: int,
    averages_by_pair: dict[tuple[str, str], dict[str, float]],
) -> tuple[Path, str]:
    filename = f"{index:02d}_{slugify(block.title)}.png"
    output_path = FIGURES_DIR / filename

    if not block.header:
        raise ReportGenerationError(f"Table '{block.title}' has empty header")

    first_col = block.header[0].strip().lower()

    if first_col == "scenario":
        host, guest = parse_pair_title(block.title)
        pair_avg = averages_by_pair.get((host, guest))
        if pair_avg is None:
            raise ReportGenerationError(f"No mechanism averages found for pair '{block.title}'")

        categories = [scenario_display_name(host, guest, row[0]) for row in block.rows]
        series_labels = [normalize_mechanism_label(h.replace(" (mean)", "").strip()) for h in block.header[1:]]
        series_values: list[list[float]] = []
        has_zero = False
        avg_lines: dict[str, float] = {}
        for c_idx, label in enumerate(series_labels, start=1):
            vals: list[float] = []
            for r_idx, row in enumerate(block.rows):
                parsed = parse_latency_to_ns(
                    row[c_idx],
                    f"{block.title} row {r_idx + 1} '{label}'",
                    allow_missing=True,
                )
                vals.append(float("nan") if parsed is None else parsed)
            require_positive(vals, block.title)
            if any((not math.isnan(v)) and v == 0 for v in vals):
                has_zero = True
            series_values.append(vals)
            if label not in pair_avg:
                raise ReportGenerationError(
                    f"Average for mechanism '{label}' missing in consolidated averages for '{block.title}'"
                )
            avg_lines[label] = float(pair_avg[label])

        # Visualization-only floor for log-scale when values are reported as 0 ns.
        # This preserves relative shape without claiming sub-ns precision.
        plot_values = [
            [1.0 if v == 0 else v for v in vals]
            for vals in series_values
        ]

        plot_grouped_bars(
            categories=categories,
            series_labels=series_labels,
            series_values=plot_values,
            title=block.title,
            ylabel="Mean latency (ns, log scale)",
            output_path=output_path,
            log_y=True,
            avg_lines=avg_lines,
        )
        desc = "Grouped bar chart on logarithmic Y-axis (mean latency in ns) with dashed per-mechanism average lines."
        if has_zero:
            desc += " Cells reported as 0 ns are plotted at 1 ns for visualization only."
        return output_path, desc

    if first_col == "mechanism":
        plot_complexity_bars(block, output_path)
        return output_path, "Grouped bar chart comparing key complexity metrics by mechanism (raw values annotated)."

    if first_col == "pair":
        # Add dedicated package names to pair labels
        categories = []
        for row in block.rows:
            pair = row[0].strip()
            m = PAIR_TITLE_RE.match(pair)
            if m:
                host, guest = m.group(1).strip().lower(), m.group(2).strip().lower()
                pkg = DEDICATED_PACKAGE_NAMES.get((host, guest))
                if pkg:
                    categories.append(f"{pair}\n({pkg})")
                else:
                    categories.append(pair)
            else:
                categories.append(pair)

        series_labels = [
            "Dedicated package baseline" if h.strip().lower() == "native" else h.strip()
            for h in block.header[1:]
        ]
        series_values: list[list[float]] = []
        for c_idx, label in enumerate(series_labels, start=1):
            vals: list[float] = []
            for r_idx, row in enumerate(block.rows):
                vals.append(parse_leading_number(row[c_idx], f"{block.title} row {r_idx + 1} '{label}'"))
            require_positive(vals, block.title)
            series_values.append(vals)

        ylabel = "Count" if "Languages Required" in block.title else "SLOC / value"
        plot_grouped_bars(
            categories=categories,
            series_labels=series_labels,
            series_values=series_values,
            title=block.title,
            ylabel=ylabel,
            output_path=output_path,
            log_y=False,
        )
        return output_path, "Grouped bar chart by language pair."

    raise ReportGenerationError(f"Unsupported table format for '{block.title}'")


def _extract_comparison_mean_ns(comp: dict, mechanism_key: str, context: str) -> float:
    obj = comp.get(mechanism_key)
    if not isinstance(obj, dict):
        raise ReportGenerationError(f"Missing comparison mechanism '{mechanism_key}' in {context}")
    status = str(obj.get("status", "")).upper()
    if status != "PASS":
        raise ReportGenerationError(
            f"Comparison mechanism '{mechanism_key}' not PASS in {context} (status={status})"
        )
    mean_ns = obj.get("mean_ns")
    if mean_ns is None:
        raise ReportGenerationError(f"Missing mean_ns for mechanism '{mechanism_key}' in {context}")
    try:
        return float(mean_ns)
    except (TypeError, ValueError) as e:
        raise ReportGenerationError(
            f"Invalid mean_ns for mechanism '{mechanism_key}' in {context}: {mean_ns}"
        ) from e


def render_any_echo_figure(consolidated: dict) -> tuple[Path, str] | None:
    comparisons = consolidated.get("comparisons")
    if not isinstance(comparisons, list):
        raise ReportGenerationError("consolidated.json missing 'comparisons' for Any-Echo figure")

    entries: list[tuple[str, float, float, float]] = []
    for comp in comparisons:
        if not isinstance(comp, dict):
            continue
        scenario = str(comp.get("scenario", "")).strip().lower()
        if not scenario.startswith("any_echo_"):
            continue
        host = str(comp.get("host", "")).strip().lower()
        guest = str(comp.get("guest", "")).strip().lower()
        context = f"any_echo comparison {host}->{guest} ({scenario})"

        fixed = {"host", "guest", "scenario", "metaffi", "grpc"}
        native_keys = [k for k in comp.keys() if k not in fixed]
        if len(native_keys) != 1:
            raise ReportGenerationError(
                f"Expected exactly one dedicated-native mechanism key in {context}, got {native_keys}"
            )
        native_key = native_keys[0]

        metaffi_ns = _extract_comparison_mean_ns(comp, "metaffi", context)
        native_ns = _extract_comparison_mean_ns(comp, native_key, context)
        grpc_ns = _extract_comparison_mean_ns(comp, "grpc", context)
        entries.append((f"{host}->{guest}", metaffi_ns, native_ns, grpc_ns))

    if not entries:
        return None

    entries.sort(key=lambda x: x[0])

    # Add dedicated package names to X-axis labels
    categories = []
    for e in entries:
        pair = e[0]
        parts = pair.split("->")
        if len(parts) == 2:
            pkg = DEDICATED_PACKAGE_NAMES.get((parts[0].strip(), parts[1].strip()))
            categories.append(f"{pair}\n({pkg})" if pkg else pair)
        else:
            categories.append(pair)

    metaffi_vals = [e[1] for e in entries]
    native_vals = [e[2] for e in entries]
    grpc_vals = [e[3] for e in entries]
    require_positive(metaffi_vals + native_vals + grpc_vals, "Any-Echo comparison figure")

    output_path = FIGURES_DIR / "00_any_echo_overview.png"
    plot_grouped_bars(
        categories=categories,
        series_labels=["metaffi", "dedicated_native", "grpc"],
        series_values=[metaffi_vals, native_vals, grpc_vals],
        title="Any-Echo Dynamic Payload Benchmark",
        ylabel="Mean latency (ns, log scale)",
        output_path=output_path,
        log_y=True,
    )
    return output_path, (
        "Any-Echo focused grouped bar chart on logarithmic Y-axis "
        "(MetaFFI vs dedicated native package vs gRPC)."
    )


def extract_native_bindings_from_tables(tables: list[TableBlock]) -> list[tuple[str, str, str]]:
    """
    Extract per-pair native package labels from
    'Per-Pair Comparison (Benchmark-Only SLOC)' table.
    """
    target_title = "Per-Pair Comparison (Benchmark-Only SLOC)"
    target = next((t for t in tables if t.title.strip() == target_title), None)
    if target is None:
        raise ReportGenerationError(f"Missing table required for native binding extraction: '{target_title}'")

    normalized_header = [h.strip().lower() for h in target.header]
    if not normalized_header or normalized_header[0] != "pair":
        raise ReportGenerationError(f"Unexpected first column in '{target_title}': {target.header}")

    native_col_idx = -1
    for i, h in enumerate(normalized_header):
        if "native" in h or "dedicated package baseline" in h:
            native_col_idx = i
            break
    if native_col_idx <= 0:
        raise ReportGenerationError(f"Could not find native baseline column in '{target_title}'")

    description_by_binding = {
        "jni": "Java Native Interface bridge (includes language-specific native glue where needed).",
        "cpython": "Go <-> Python bridge via CPython C API.",
        "jep": "Java Embedded Python (JEP) package.",
        "ctypes": "Python ctypes FFI package.",
        "jpype": "Python JPype package (JVM bridge).",
    }

    extracted: list[tuple[str, str, str]] = []
    for row in target.rows:
        pair = row[0].strip()
        native_cell = row[native_col_idx].strip()

        m = re.search(r"\(([^)]+)\)", native_cell)
        if not m:
            raise ReportGenerationError(
                f"Native baseline cell for pair '{pair}' must include package label in parentheses, got '{native_cell}'"
            )
        binding = m.group(1).strip().lower()
        if binding not in description_by_binding:
            raise ReportGenerationError(
                f"Unknown native binding '{binding}' in '{target_title}' for pair '{pair}'"
            )
        extracted.append((pair, binding, description_by_binding[binding]))

    if not extracted:
        raise ReportGenerationError(f"No native baseline bindings extracted from '{target_title}'")
    return extracted


def _get_figure_commentary(table_title: str) -> str | None:
    """Return explanatory prose for a figure, placed after the figure image."""
    commentaries: dict[str, str] = {
        "Go -> Java": (
            "MetaFFI latency ranges from ~1.3 µs (void call) to ~104 µs (any_echo), "
            "while JNI stays below 1 µs for most lightweight scenarios and reaches ~14 µs at 10k-element arrays. "
            "gRPC consistently occupies the 140--305 µs band, dominated by protobuf serialization and HTTP/2 transport. "
            "The MetaFFI-to-JNI gap widens with data payload complexity (CDTS per-element metadata vs JNI bulk array access), "
            "but MetaFFI remains 10--30x faster than gRPC across all scenarios."
        ),
        "Go -> Python3": (
            "MetaFFI and CPython diverge most sharply on any_echo (223 µs vs 1.6 µs), "
            "where CDTS dynamic-type serialization is heaviest. "
            "For void calls, MetaFFI (485 ns) is within 5x of CPython (92 ns); "
            "the gap is largely GIL acquire/release overhead that CPython avoids by holding the GIL across iterations. "
            "gRPC latency (297--834 µs) is 1--2 orders of magnitude above both in-process mechanisms, "
            "confirming that even MetaFFI's CDTS overhead is far smaller than RPC transport cost."
        ),
        "Java -> Go": (
            "The void-call scenario shows MetaFFI matching the JNI+cgo baseline (~1.7 µs each), "
            "thanks to the Java host API's pre-compiled JNI fast path. "
            "Array echo scenarios show MetaFFI at 6--13 µs vs JNI at 3--7 µs, a modest 2x factor. "
            "The any_echo scenario is the outlier: MetaFFI (238 µs) exceeds even gRPC (190 µs) "
            "due to fully dynamic CDTS type dispatch on 100 mixed-type elements. "
            "gRPC otherwise sits at 140--338 µs, well above both in-process mechanisms."
        ),
        "Java -> Python3": (
            "MetaFFI outperforms JEP on 7 of 11 scenarios, including void call (325 ns vs 8.9 µs), "
            "primitives, strings, object methods, callbacks, and error propagation. "
            "JEP gains advantage only on large arrays (55 µs vs 213 µs at 10k) via NumPy-backed zero-copy transfers. "
            "gRPC is the slowest mechanism across all scenarios (335--928 µs), "
            "making MetaFFI the fastest option for most Java-to-Python3 interop patterns."
        ),
        "Python3 -> Go": (
            "MetaFFI and ctypes track closely for lightweight scenarios: void call (2.6 µs vs 1.9 µs), "
            "array echo at small sizes (5.8--6.0 µs vs 4.7--5.3 µs). "
            "The gap opens at 10k-element arrays (18.4 µs vs 5.5 µs) where ctypes benefits from buffer-protocol transfers. "
            "MetaFFI outperforms gRPC (215--1600 µs) by 20--160x, and notably MetaFFI's error propagation (3.8 µs) "
            "is faster than ctypes (4.6 µs) on that scenario."
        ),
        "Python3 -> Java": (
            "JPype dominates MetaFFI on most scenarios, with void call at 600 ns vs 2.9 µs "
            "and array sum at 10k elements at 5.1 µs vs 133 µs. "
            "MetaFFI's main advantage is error propagation (16.8 µs vs 29.7 µs for JPype). "
            "gRPC is consistently the slowest mechanism (211--1410 µs), "
            "placing MetaFFI in the middle ground between JPype's optimized JNI path and gRPC's RPC overhead."
        ),
        "Summary by Mechanism": (
            "MetaFFI requires the fewest languages per implementation (1.0 on average vs 2.0 for dedicated packages and 3.0 for gRPC), "
            "reflecting its uniform single-language API. "
            "Dedicated package baselines show the highest average benchmark SLOC (1532 lines) "
            "driven by the java->go JNI+cgo implementation at 6745 lines. "
            "MetaFFI has the lowest average max cyclomatic complexity (11.3) compared to native packages (18.2) and gRPC (20.8)."
        ),
        "Per-Pair Comparison (Benchmark-Only SLOC)": (
            "MetaFFI SLOC is comparable to or lower than dedicated packages for most pairs, "
            "with the exception of go->java (481 vs 641) and go->python3 (470 vs 588). "
            "The java->go pair shows the most extreme contrast: MetaFFI at 537 lines vs JNI+cgo at 6745 lines, "
            "reflecting the complexity of bidirectional JNI+cgo bridge code. "
            "gRPC SLOC is moderate (468--742) but requires 3 languages everywhere."
        ),
        "Languages Required per Pair": (
            "MetaFFI consistently requires only the host language (1 language per pair), "
            "while gRPC always requires 3 languages (host, guest, Protobuf schema). "
            "Dedicated packages vary: 1 language for same-ecosystem pairs (java->python3 JEP, python3->java JPype) "
            "but 2--3 languages when bridging across memory models (go->java JNI requires C+Go, python3->go ctypes requires C+Go+Python)."
        ),
        "Cross-Pair Performance Summary": (
            "Across all six language pairs, MetaFFI mean latency ranges from 26 µs (java->python3) to 60 µs (python3->java). "
            "Dedicated packages span from 4.5 µs (python3->java JPype) to 3.6k µs (java->go JNI+cgo, inflated by the 6745-SLOC bridge). "
            "gRPC is consistently the slowest (230--430 µs), confirming that in-process mechanisms "
            "provide substantially lower latency than RPC-based interop for all measured pairs."
        ),
    }
    return commentaries.get(table_title.strip())


def build_cross_pair_section(
    averages_by_pair: dict[tuple[str, str], dict[str, float]],
) -> tuple[str, Path]:
    """Build a cross-pair performance comparison table + grouped bar chart.

    Returns (markdown_section, figure_path).
    """
    # Collect data for all 6 pairs
    pair_order = [
        ("go", "java"), ("go", "python3"),
        ("java", "go"), ("java", "python3"),
        ("python3", "go"), ("python3", "java"),
    ]

    table_rows: list[list[str]] = []
    metaffi_vals: list[float] = []
    native_vals: list[float] = []
    grpc_vals: list[float] = []
    categories: list[str] = []

    for host, guest in pair_order:
        pair_avg = averages_by_pair.get((host, guest))
        if pair_avg is None:
            raise ReportGenerationError(f"Missing averages for pair {host}->{guest}")

        metaffi_ns = pair_avg.get("metaffi")
        grpc_ns = pair_avg.get("grpc")
        if metaffi_ns is None or grpc_ns is None:
            raise ReportGenerationError(f"Missing metaffi/grpc average for {host}->{guest}")

        # Find the native/dedicated package mechanism (not metaffi, not grpc)
        native_key = None
        native_ns = None
        for k, v in pair_avg.items():
            if k not in ("metaffi", "grpc"):
                native_key = k
                native_ns = v
                break
        if native_ns is None:
            raise ReportGenerationError(f"Missing native average for {host}->{guest}")

        pkg = DEDICATED_PACKAGE_NAMES.get((host, guest), native_key)
        pair_label = f"{host}->{guest}"

        table_rows.append([
            pair_label,
            format_latency_ns(metaffi_ns),
            f"{format_latency_ns(native_ns)} ({pkg})",
            format_latency_ns(grpc_ns),
        ])

        categories.append(f"{pair_label}\n({pkg})")
        metaffi_vals.append(metaffi_ns)
        native_vals.append(native_ns)
        grpc_vals.append(grpc_ns)

    # Build the table markdown
    table_header = ["Pair", "MetaFFI (mean)", "Dedicated package (mean)", "gRPC (mean)"]
    table_md = _render_markdown_table(table_header, table_rows)

    # Build the figure
    figure_path = FIGURES_DIR / "00_cross_pair_summary.png"
    plot_grouped_bars(
        categories=categories,
        series_labels=["MetaFFI", "Dedicated package", "gRPC"],
        series_values=[metaffi_vals, native_vals, grpc_vals],
        title="Cross-Pair Performance Summary",
        ylabel="Mean latency (ns, log scale)",
        output_path=figure_path,
        log_y=True,
    )

    # Assemble section
    lines: list[str] = []
    lines.append("## Cross-Pair Performance Summary")
    lines.append("")
    lines.append(table_md)
    lines.append("")
    rel_figure = figure_path.relative_to(RESULTS_DIR).as_posix()
    lines.append(f"<p align=\"center\"><b>Cross-Pair Performance Summary</b></p>")
    lines.append("")
    lines.append(f"![Cross-Pair Performance Summary]({rel_figure})")
    lines.append("")

    commentary = _get_figure_commentary("Cross-Pair Performance Summary")
    if commentary:
        lines.append(commentary)
        lines.append("")

    return "\n".join(lines), figure_path


def build_report_markdown(
    consolidated: dict,
    complexity: dict,
    tables: list[TableBlock],
    figure_map: list[tuple[Path, str]],
    averages_by_pair: dict[tuple[str, str], dict[str, float]],
    any_echo_figure: tuple[Path, str] | None = None,
) -> str:
    gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    summary = consolidated.get("summary", {})
    unique_protocols, protocol_entries = extract_benchmark_protocol(consolidated)

    lines: list[str] = []
    lines.append("# MetaFFI Cross-Language Evaluation Report")
    lines.append("")
    lines.append(f"Generated: {gen_time}")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report is generated from the benchmark/correctness consolidation and complexity analysis outputs.")
    lines.append("It provides table-by-table visualization support for thesis writing, without injecting final conclusions.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- `consolidated.json`: result files={summary.get('total_result_files', 'N/A')} / expected={summary.get('expected_triples', 'N/A')}")
    lines.append(
        f"- `consolidated.json`: benchmarks passed={summary.get('benchmarks', {}).get('passed', 'N/A')}, "
        f"failed={summary.get('benchmarks', {}).get('failed', 'N/A')}"
    )
    lines.append(f"- `complexity.json`: pair comparisons={len(complexity.get('pair_comparisons', []))}")
    lines.append(f"- `tables.md`: tables parsed={len(tables)}")
    lines.append("")
    lines.append("## Analysis Notes")
    lines.append("")
    lines.append("- Performance charts use the mean values reported in `tables.md` and are converted to nanoseconds for plotting.")
    lines.append("- Pair performance charts use logarithmic Y-scale due to multi-order magnitude spread across scenarios/mechanisms.")
    lines.append("- Complexity summary chart is a grouped bar chart comparing key metrics (Avg Benchmark SLOC, Avg Languages, Avg Max CC) by mechanism.")
    lines.append("- This report is fail-fast: any malformed source value aborts generation to avoid silent misreporting.")
    lines.append("- For performance figures, dashed horizontal lines are per-pair, per-mechanism averages loaded from `consolidated.json`.")
    lines.append("- gRPC results include protobuf schema-bound serialization/deserialization plus localhost RPC transport stack overhead (channel, HTTP/2 framing, socket I/O, server scheduling).")
    lines.append("- MetaFFI CDTS is schema-less at call-definition level (runtime carries type metadata per value), so no `.proto` schema authoring is required for cross-language calls.")
    lines.append("")
    lines.append("## Optimizations Implemented")
    lines.append("")
    lines.append("- `sdk/runtime_manager/jvm/jvm.cpp`, `sdk/runtime_manager/jvm/jvm.h`: keep JNI thread attachment by default (detach-on-release remains available via `METAFFI_JVM_DETACH_ON_ENV_RELEASE=true`).")
    lines.append("- `sdk/runtime_manager/go/module.cpp`, `lang-plugin-go/runtime/go_api.cpp`: disabled verbose Go plugin logging by default; enable only with `METAFFI_GO_PLUGIN_DEBUG_LOG=1`.")
    lines.append("- `lang-plugin-python3/runtime/call_xcall.cpp`: cached parsed `param_metaffi_types` metadata and added optional phase profiler (`METAFFI_PROFILE_PY_XCALL=1`).")
    lines.append("- `sdk/cdts_serializer/jvm/cdts_jvm_serializer.cpp`: primitive-array extraction uses `GetPrimitiveArrayCritical` to avoid extra copy paths.")
    lines.append("- `sdk/api/jvm/metaffi/api/accessor/Caller.java`: added per-phase caller profiler (`METAFFI_PROFILE_CALLER=1`) with periodic progress summary.")
    lines.append("- `sdk/api/jvm/metaffi/api/accessor/Caller.java`, `sdk/api/jvm/metaffi/api/accessor/MetaFFIAccessor.java`, `sdk/api/jvm/accessor/metaffi_api_accessor.cpp`: added int64 single-parameter fast path (`set_cdt_int64`) for lower serialization overhead in hot no-return calls.")
    lines.append("- `tests/run_all_tests.py`: config-driven rerun support with scenario-level merge updates and fail-fast config validation.")
    lines.append("- `sdk/runtime_manager/jvm/cdts_java_wrapper.cpp`, `sdk/api/jvm/accessor/metaffi_api_accessor.cpp`: fixed Go object handle double-free crash in `java->go [metaffi]`. When a Go object handle (with its `release` function pointer) was returned to Java via CDT, both Java's `MetaFFIHandle` and the CDT's `cdt::free()` would call the release callback, causing a double-free and intermittent JVM abort (`ShouldNotReachHere`). Fix: null out `release` pointers on foreign (non-JVM) handles after Java extracts them, and as a safety net in `free_cdts`. Applied symmetrically to both input and output handle paths.")
    lines.append("")
    lines.append("### Hot-path optimizations (void_call focus)")
    lines.append("")
    lines.append("The following optimizations target the `void_call_void_void` scenario (no parameters, no return values), reducing pure cross-language call overhead:")
    lines.append("")
    lines.append("#### JVM plugin (`lang-plugin-jvm/runtime/jvm_runtime.cpp`)")
    lines.append("")
    lines.append("- **Cached JNI reflection infrastructure**: All `FindClass` and `GetMethodID` calls for the reflection hot-path (`java/lang/Object`, `java/lang/reflect/Method`, `java/lang/reflect/Constructor`, `java/lang/reflect/Field`, `java/lang/Class`, `java/lang/reflect/Array`) are now resolved once at JVM load time into global references and reused on every call. Previously, each `invoke_method` call did `FindClass(\"java/lang/reflect/Method\")` + `GetMethodID(\"invoke\")` per invocation.")
    lines.append("- **Zero-arg fast path**: For calls with no arguments, `invoke_reflection_call` now calls `Method.invoke(instance, null)` directly instead of building an empty `Object[]` array. This eliminates per-call `FindClass(\"java/lang/Object\")` + `NewObjectArray(0)` + `DeleteLocalRef` overhead.")
    lines.append("- **Skip coerce_args for empty argument arrays**: `coerce_args_to_param_types` returns immediately when the argument array has zero elements, avoiding unnecessary `getParameterTypes()` reflection calls.")
    lines.append("- **Thread-local JNIEnv caching** (`sdk/runtime_manager/jvm/jvm.cpp`): Added `thread_local JNIEnv*` cache for the default no-detach mode. `get_environment()` returns the cached pointer on subsequent calls from the same thread, avoiding repeated `GetEnv`/`AttachCurrentThread` JNI calls.")
    lines.append("- **Signature-based xcall dispatch**: `load_entity` wires the appropriate xcall entry point based on the parameter/return-value signature at load time (`jvm_api_xcall_no_params_no_ret`, etc.), avoiding runtime branching on CDTS presence.")
    lines.append("")
    lines.append("#### Python3 guest plugin (`lang-plugin-python3/runtime/python_api.cpp`)")
    lines.append("")
    lines.append("- **Direct PyObject_CallObject for void(void)**: `pyxcall_no_params_no_ret` now calls `PyObject_CallObject(callable, NULL)` directly on the underlying `PyObject*` instead of going through `CallableEntity::call(vector)`. This eliminates: redundant GIL acquisition (GIL was acquired twice -- once in the xcall, once in `CallableEntity::call`), `std::mutex` lock, `dynamic_cast`, `std::vector` construction, `PyTuple_New(0)`, `organize_arguments`, and `PyCallable_Check` per call.")
    lines.append("")
    lines.append("#### Python3 host runtime (`lang-plugin-python3/runtime/call_xcall.cpp`)")
    lines.append("")
    lines.append("- **Skip param-type parsing for void path**: `call_xcall` now defers `get_or_parse_param_types` to the params/ret branch, avoiding any param-type cache lookup for `void_call` (params_count == 0 && retval_count == 0).")
    lines.append("")
    lines.append("#### Go host API (`sdk/api/go/MetaFFIModule.go`)")
    lines.append("")
    lines.append("- **Skip CDT allocation for void calls**: `LoadWithInfo` returns a `func() error` closure for the (0-params, 0-retvals) case that calls `XLLRXCallNoParamsNoRet` directly, bypassing `XLLRAllocCDTSBuffer` entirely.")
    lines.append("")
    lines.append("#### JNI baseline fairness (`tests/go/without_metaffi/call_java_jni/bridge.go`)")
    lines.append("")
    lines.append("- **Thread-local env parity**: Added matching thread-local `JNIEnv*` caching to MetaFFI JVM path; verified JNI baseline already benefits from the same optimization via `GetEnv` fast-path.")
    lines.append("- **Moved FindClass to initialization**: JNI baseline's `bench_string_echo`, `bench_array_sum`, and `bench_any_echo` previously called `FindClass` in the hot loop. These class references are now cached in `jni_load_classes()` as global refs.")
    lines.append("")
    lines.append("### Correctness fixes")
    lines.append("")
    lines.append("- `sdk/runtime_manager/jvm/jni_helpers.h`: Unwrap `InvocationTargetException`/`UndeclaredThrowableException` to report root cause.")
    lines.append("- `lang-plugin-jvm/runtime/jvm_runtime.cpp` (`resolve_method`): Fall back to name+param-count matching when exact type matching fails for opaque handles.")
    lines.append("- `lang-plugin-jvm/runtime/jvm_runtime.cpp` (`coerce_args_to_param_types`): Coerce `Object[]` arguments to the declared parameter type arrays using `java.lang.reflect.Array`.")
    lines.append("- `sdk/cdts_serializer/jvm/cdts_jvm_serializer.cpp` (`extract_multidim_array`): Correctly build JNI class descriptors for nested array types (e.g. `[[I` for `int[][]`).")
    lines.append("- `sdk/cdts_serializer/jvm/cdts_jvm_serializer.cpp` (`set_index`): Allow one-past-the-end index for null/any trailing values.")
    lines.append("")
    lines.append("### CDT large-array analysis (methodology note)")
    lines.append("")
    lines.append("Four scenarios where MetaFFI latency exceeds gRPC involve 10k-element arrays or dynamic (`any`) types. Analysis of the CDT serialization paths across all three language runtimes (Go `TraverseConstruct.go`, Java `cdts_jvm_serializer.cpp` / `cdts_java_wrapper.cpp`, Python3 `cdts_python3_serializer.cpp`) confirmed that all already use optimised bulk operations: Go issues a single CGO call per primitive array via `copy_cdts_to_uint8_buffer` / `fill_cdts_from_uint8_buffer`; Java uses `GetPrimitiveArrayCritical` with tight C++ loops; Python3 uses tight C++ loops over `PyList` items. The overhead is structural: CDT is schema-less and carries per-element type metadata (24 bytes per `cdt` element), whereas gRPC/protobuf uses packed scalar encoding with no per-element metadata. For 10k `uint8` elements, CDT allocates ~240 KB vs ~10 KB for protobuf. This is an inherent trade-off of CDT's runtime-typed design and cannot be eliminated without schema-aware fast paths.")
    lines.append("")
    lines.append("### Packed arrays (CDT optimization)")
    lines.append("")
    lines.append("Packed arrays (`metaffi_packed_type`) address the per-element CDT overhead for 1D homogeneous primitive arrays. Instead of allocating one CDT per element (24 bytes each), a packed array stores the data as a contiguous `type* + length` block under a single CDT. This eliminates per-element type metadata overhead and enables bulk `memcpy`-style transfers. The `array_sum` and `array_echo` benchmark scenarios now use packed array primitives by default across all language pairs.")
    lines.append("")
    lines.append("### Go API CDT lifecycle fixes (`sdk/api/go/`)")
    lines.append("")
    lines.append("- **OS-thread pinning for CDT cache coherency** (`MetaFFIModule.go`): Added `runtime.LockOSThread()` / `defer runtime.UnlockOSThread()` to all MetaFFI call closures that allocate/free CDTS buffers. The CDT cache uses thread-local storage in `xllr.dll`; without pinning, Go goroutine migration between OS threads caused `alloc_cdts_buffer` and `free_cdts_buffer` to operate on different TLS caches, producing negative cache indices and `std::abort()`. This fix is required for correctness of all Go-hosted cross-language calls that use the CDTS cache.")
    lines.append("- **Proper CDTS buffer freeing** (`MetaFFIModule.go`, `XLLRAccessor.go`): Replaced erroneous conditional `C.free()` with `XLLRClearAndFreeCDTSBuffer()` across all call paths. The new function nulls `free_required` on input parameter CDTs before calling `xllr_free_cdts_buffer`, preventing the CDT destructor from releasing Go-owned resources (handles, callables, strings) while still properly managing cache indices.")
    lines.append("- **Handle ownership semantics** (`TraverseConstruct.go`): Set `free_required = false` on `metaffi_handle_type` CDT elements when serializing Go handles as parameters, ensuring the CDT destructor does not release Go-owned object handles.")
    lines.append("")
    lines.append("## Benchmark Protocol")
    lines.append("")
    lines.append("For each benchmark scenario, the execution protocol is:")
    lines.append("1. Run warm-up iterations (excluded from reported statistics).")
    lines.append("2. Run measured iterations and collect per-iteration latency samples.")
    lines.append("3. Compute summary statistics from measured samples (after each test's built-in filtering/processing path).")
    lines.append("4. Persist timing metadata, including timer-overhead measurement, into the result file.")
    lines.append("")
    lines.append("- Warm-up reduces runtime transients (for example JVM JIT/warm caches) before sampling.")
    if len(unique_protocols) == 1:
        warmup, measured, repeat_count, batch_min, batch_max = next(iter(unique_protocols))
        lines.append(
            "- Protocol in this dataset is uniform across all result files: "
            f"`warmup={warmup}`, `measured={measured}`, `repeats={repeat_count}`, "
            f"`batch_min_elapsed_ns={batch_min}`, `batch_max_calls={batch_max}` per scenario."
        )
        lines.append("- Reported global benchmark means use pooled iterations across all repeats.")
    else:
        lines.append("- Protocol differs across result files; exact per-triple configuration:")
        for host, guest, mech, warmup, measured, repeat_count, batch_min, batch_max in protocol_entries:
            lines.append(
                f"- `{host}->{guest} [{mech}]`: `warmup={warmup}`, `measured={measured}`, "
                f"`repeats={repeat_count}`, `batch_min_elapsed_ns={batch_min}`, "
                f"`batch_max_calls={batch_max}`."
            )
        lines.append("- Reported global benchmark means use pooled iterations across all repeats.")
    lines.append("")
    lines.append("## Scenario Scope Strategy")
    lines.append("")
    lines.append("- This benchmark suite intentionally samples multiple data/interop patterns without exhausting every type x operation x pair combination.")
    lines.append("- Rationale: a fully crossed design would multiply the experiment matrix substantially beyond the current 18 triples and the baseline scenario set (plus targeted extensions).")
    lines.append("- Therefore, array scenarios are representative by pair and guest API constraints (including ragged-array sum and byte-array echo), and are explicitly labeled below.")
    lines.append("")
    lines.append("## Scenario Definitions")
    lines.append("")
    lines.append("- `void_call_void_void` (source key: `void_call`): true void(void) invocation -- no arguments, no return value. Measures pure cross-language call overhead.")
    lines.append("- `primitive_echo_int64_int64_to_float64` (source key: `primitive_echo`): primitive transfer and return.")
    lines.append("- `string_echo_string8_utf8` (source key: `string_echo`): string marshaling overhead using MetaFFI `string8` (UTF-8).")
    lines.append("- Native baseline note for `string_echo`: CPython path uses UTF-8 APIs; JNI path uses `GetStringUTFChars` / `NewStringUTF` (JNI modified UTF-8).")
    lines.append("- Ragged-array sum scenarios in tables are rendered as `array_sum_ragged_<type>_2d_n<size>`.")
    lines.append("- Byte-array echo scenarios in tables are rendered as `array_echo_uint8_1d_n<size>`.")
    lines.append("- Exact array payload types in this dataset by pair:")
    lines.append("- `go->java`: ragged `int32[][] -> int32` (rendered as `array_sum_ragged_int32_2d_n<size>`).")
    lines.append("- `python3->java`: ragged `int32[][] -> int32` (rendered as `array_sum_ragged_int32_2d_n<size>`).")
    lines.append("- `go->python3`: ragged `int64[][] -> int64` (rendered as `array_sum_ragged_int64_2d_n<size>`).")
    lines.append("- `java->python3`: ragged `int64[][] -> int64` (rendered as `array_sum_ragged_int64_2d_n<size>`).")
    lines.append("- `java->go`: `uint8[] -> uint8[]` roundtrip (rendered as `array_echo_uint8_1d_n<size>`).")
    lines.append("- `python3->go`: `uint8[] -> uint8[]` roundtrip (rendered as `array_echo_uint8_1d_n<size>`).")
    lines.append("- `object_method_ctor_plus_instance_call` (source key: `object_method`): object construction/handle passing and instance call.")
    lines.append("- `callback_callable_int_int_to_int` (source key: `callback`): callable transfer and reverse invocation across boundary.")
    lines.append("- `error_propagation_exception_path` (source key: `error_propagation`): exception/error signaling overhead.")
    lines.append("- `packed_array_sum_int32_1d_n<size>` / `packed_array_sum_int64_1d_n<size>` (source key: `packed_array_sum_<size>`): 1D packed array sum using contiguous memory CDT path (no per-element type metadata).")
    lines.append("- `any_echo_mixed_dynamic_n<size>` (source key: `any_echo_<size>`): dynamic `Any` payload roundtrip using mixed-type arrays (schema-less in MetaFFI/CDTS vs schema-declared dynamic container in protobuf).")
    lines.append("")
    lines.append("## Array Family Interpretation")
    lines.append("")
    lines.append("- Two array workload families are intentionally present: ragged-array sum (`array_sum_ragged_*`) and byte-array echo (`array_echo_uint8_*`).")
    lines.append("- These families serve the same high-level goal (array marshaling stress across sizes), but they are not semantically identical operations.")
    lines.append("- Comparative claims should be made within the same family across mechanisms for a given pair.")
    lines.append("- Cross-family absolute ranking (for example, comparing `array_sum_ragged_*` directly against `array_echo_uint8_*`) should be avoided in conclusions.")
    lines.append("")
    lines.append("## Threats To Validity")
    lines.append("")
    lines.append("- Timer-floor effect: values displayed as `0 ns` indicate latency below effective timing resolution for the single-call measurement method.")
    lines.append("- Native baseline heterogeneity: dedicated pair-specific packages (JNI/CPython/ctypes/JPype/JEP) are practical baselines, not a single uniform raw-native method.")
    lines.append("- gRPC architectural asymmetry: gRPC baseline measures networked RPC semantics (protobuf schema + client/server transport), while MetaFFI baseline measures in-process FFI interop semantics.")
    lines.append("- Therefore, gRPC vs MetaFFI should be interpreted as practical engineering alternatives for cross-language integration, not as strictly identical execution models.")
    lines.append("- Pair-specific API constraints: scenario signatures differ by guest module/API compatibility (for example ragged int32/int64 sum vs uint8 echo).")
    lines.append("- Runtime effects: JIT/runtime warm-up behavior (especially JVM-host cases) can influence steady-state timing and motivates explicit warm-up control.")
    lines.append("- Result interpretation should therefore remain scenario-signature aware and reproducibility-bounded to this exact tooling/version set.")
    lines.append("")
    lines.append("## Table 7 Metric Definitions")
    lines.append("")
    lines.append("- `Count`: number of implementations in that mechanism group (6 pair-directions per mechanism family).")
    lines.append("- `Avg SLOC`: average source-code lines (SLOC) across implementations in the group.")
    lines.append("- `Avg Benchmark SLOC`: average benchmark-only SLOC; MetaFFI correctness-only files are excluded.")
    lines.append("- `Avg Languages`: average number of programming languages per implementation.")
    lines.append("- `Avg Files`: average count of source files per implementation.")
    lines.append("- `Avg Max CC`: average of each implementation's maximum cyclomatic complexity.")
    lines.append("- `SLOC` vs `LOC`: SLOC counts only non-blank, non-comment lines (LOC includes comments/blanks).")
    lines.append("- Tooling:")
    lines.append("  - `cloc` for SLOC counting (non-blank, non-comment lines).")
    lines.append("  - `lizard` for cyclomatic complexity (`python -m lizard --csv ...`).")
    lines.append("  - Reference: https://github.com/terryyin/lizard")
    lines.append("")
    lines.append("## Baseline Interpretation (MetaFFI vs Native Packages)")
    lines.append("")
    native_bindings = extract_native_bindings_from_tables(tables)
    lines.append("- Native baselines are intentionally practical per pair. The concrete baselines in this dataset are:")
    for pair, binding, desc in native_bindings:
        lines.append(f"- `{pair}`: `{binding}` ({desc})")
    lines.append("- Therefore, comparisons should be interpreted as: **MetaFFI vs strongest practical direct bridge available at experiment time**.")
    lines.append("- This is not identical to a pure \"raw native glue\" comparison in every pair, because libraries like JEP/JPype abstract some low-level integration code.")
    lines.append("- The uniformity claim for MetaFFI remains orthogonal: one approach across all pairs/mechanisms vs heterogeneous package-specific approaches.")
    lines.append("- gRPC requires explicit protobuf schema/contracts (`.proto`) and generated stubs per language; MetaFFI uses IDL + runtime type metadata (CDTS) and does not require per-scenario protobuf contracts.")
    lines.append("- To address \"future better package\" arguments, keep conclusions version/time bounded and tied to reproducible baselines used in this experiment.")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Values shown as `0 ns` mean the measured latency is below effective timer+measurement resolution for the single-call method in this environment.")
    lines.append("- In performance figures, `0 ns` points are rendered at `1 ns` only so they can be shown on logarithmic axes; this is a visualization floor, not a claimed runtime value.")
    lines.append("- In Tables 7-9, \"native\" refers to **dedicated per-pair interoperability packages** (e.g., JEP/JPype/JNI/cgo/ctypes), not a uniform raw-native implementation style.")
    lines.append("")
    if any_echo_figure is not None:
        fig_path, fig_desc = any_echo_figure
        rel_any = fig_path.relative_to(RESULTS_DIR).as_posix()
        lines.append("## Any-Echo Focus Figure")
        lines.append("")
        lines.append(f"<p align=\"center\"><b>Any-Echo Dynamic Payload Benchmark</b></p>")
        lines.append("")
        lines.append(f"![Any-Echo Dynamic Payload Benchmark]({rel_any})")
        lines.append("")

    repeat_tables = build_repeat_analysis_tables(consolidated)
    if repeat_tables:
        lines.append("## Repeat-Mean Tables")
        lines.append("")
        lines.append("- Each table reports per-repeat means (`run_i_mean`), the arithmetic `mean_of_repeat_means`, and the published `global_pooled_mean`.")
        lines.append("- Figures in this report use only `global_pooled_mean` values.")
        lines.append("")
        lines.extend(repeat_tables)

    lines.append("## Appendix A: Scenario Signature Matrix")
    lines.append("")
    lines.append(_render_markdown_table(
        ["Pair", "Array Scenario Label", "Array Signature", "String Scenario Label"],
        build_signature_matrix_rows(),
    ))
    lines.append("")
    lines.append("## Tables And Figures")
    lines.append("")

    for i, (table, (figure_path, figure_desc)) in enumerate(zip(tables, figure_map), start=1):
        # Insert cross-pair comparison section before Table 7 (complexity tables)
        if i == 7:
            cross_pair_md, _ = build_cross_pair_section(averages_by_pair)
            lines.append(cross_pair_md)

        rel_figure = figure_path.relative_to(RESULTS_DIR).as_posix()
        lines.append(f"### Table {i}: {table.title}")
        lines.append("")
        lines.append(format_table_for_report(table, i))
        lines.append("")
        if i in (7, 8, 9):
            lines.append("Note: \"Native\" here means dedicated package baseline for that pair, not raw native glue code.")
            lines.append("")
        lines.append(f"<p align=\"center\"><b>{table.title}</b></p>")
        lines.append("")
        lines.append(f"![{table.title}]({rel_figure})")
        lines.append("")

        # Add figure commentary after the figure image
        fig_commentary = _get_figure_commentary(table.title)
        if fig_commentary:
            lines.append(fig_commentary)
            lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    if not TABLES_FILE.is_file():
        raise ReportGenerationError(f"Missing input table file: {TABLES_FILE}")

    consolidated = load_json(CONSOLIDATED_FILE)
    complexity = load_json(COMPLEXITY_FILE)
    averages_by_pair = build_average_lookup(consolidated)
    tables_text = TABLES_FILE.read_text(encoding="utf-8")
    tables = parse_tables(tables_text)

    if FIGURES_DIR.exists():
        shutil.rmtree(FIGURES_DIR)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    figure_map: list[tuple[Path, str]] = []
    for idx, table in enumerate(tables, start=1):
        figure_map.append(render_figure_for_table(table, idx, averages_by_pair))
    any_echo_figure = render_any_echo_figure(consolidated)

    report_md = build_report_markdown(
        consolidated,
        complexity,
        tables,
        figure_map,
        averages_by_pair=averages_by_pair,
        any_echo_figure=any_echo_figure,
    )
    REPORT_FILE.write_text(report_md, encoding="utf-8")

    print(f"Report written to {REPORT_FILE}")
    print(f"Figures written to {FIGURES_DIR}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ReportGenerationError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)
