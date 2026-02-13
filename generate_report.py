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
        "void_call": "void_call_no_payload",
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

    arr_echo_size = _parse_sized_scenario(scenario, "array_echo")
    if arr_echo_size is not None:
        return f"array_echo_uint8_1d_n{arr_echo_size}"

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
        ["python3->java", "array_sum_ragged_int32_2d_n<size>", "int32[][] -> int32", "string_echo_string8_utf8"],
        ["go->python3", "array_sum_ragged_int64_2d_n<size>", "int64[][] -> int64", "string_echo_string8_utf8"],
        ["java->python3", "array_sum_ragged_int64_2d_n<size>", "int64[][] -> int64", "string_echo_string8_utf8"],
        ["java->go", "array_echo_uint8_1d_n<size>", "uint8[] -> uint8[]", "string_echo_string8_utf8"],
        ["python3->go", "array_echo_uint8_1d_n<size>", "uint8[] -> uint8[]", "string_echo_string8_utf8"],
    ]


def format_table_for_report(block: TableBlock, table_index: int) -> str:
    header = [h for h in block.header]
    rows = [[c for c in r] for r in block.rows]

    if table_index in (7, 8, 9):
        for i, h in enumerate(header):
            if h.strip().lower() == "native":
                header[i] = "Dedicated package baseline"
        for r in rows:
            if r and r[0].strip().lower() == "native":
                r[0] = "dedicated package baseline"

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


def parse_latency_to_ns(cell: str, context: str) -> float:
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


def parse_leading_number(cell: str, context: str) -> float:
    m = LEADING_NUM_RE.match(cell)
    if not m:
        raise ReportGenerationError(f"Expected numeric-leading value in '{context}', got '{cell}'")
    return float(m.group(1))


def require_positive(values: list[float], context: str) -> None:
    if not values:
        raise ReportGenerationError(f"No numeric values found for {context}")
    if any(v < 0 for v in values):
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

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(categories, rotation=35, ha="right")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    if log_y:
        if any(v <= 0 for vals in series_values for v in vals):
            raise ReportGenerationError(f"Log-scale chart has non-positive values in '{title}'")
        ax.set_yscale("log")

    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


def plot_complexity_heatmap(block: TableBlock, output_path: Path) -> None:
    row_labels = [("Dedicated package baseline" if r[0].strip().lower() == "native" else r[0]) for r in block.rows]
    col_labels = block.header[1:]
    selected_col_indices = list(range(len(col_labels)))
    # Keep full complexity table, but avoid over-emphasizing Avg Benchmark SLOC / Avg Files in the figure.
    if block.title.strip() == "Summary by Mechanism":
        wanted = ["Avg SLOC", "Avg Languages", "Avg Max CC"]
        selected_col_indices = []
        for w in wanted:
            try:
                selected_col_indices.append(col_labels.index(w))
            except ValueError as e:
                raise ReportGenerationError(
                    f"Missing required complexity column '{w}' for heatmap filtering"
                ) from e
        col_labels = [col_labels[i] for i in selected_col_indices]
    raw_matrix: list[list[float]] = []

    for r_idx, row in enumerate(block.rows):
        vals: list[float] = []
        for out_idx, in_idx in enumerate(selected_col_indices):
            cell = row[1:][in_idx]
            v = parse_leading_number(cell, f"{block.title} row {r_idx + 1} col {out_idx + 2}")
            vals.append(v)
        raw_matrix.append(vals)

    if not raw_matrix:
        raise ReportGenerationError(f"Empty heatmap source in '{block.title}'")

    # Column-wise min-max normalize for comparability across different units.
    normalized: list[list[float]] = []
    cols = len(raw_matrix[0])
    col_min = [min(raw_matrix[r][c] for r in range(len(raw_matrix))) for c in range(cols)]
    col_max = [max(raw_matrix[r][c] for r in range(len(raw_matrix))) for c in range(cols)]

    for r in range(len(raw_matrix)):
        norm_row: list[float] = []
        for c in range(cols):
            denom = col_max[c] - col_min[c]
            norm_row.append(0.0 if denom == 0 else (raw_matrix[r][c] - col_min[c]) / denom)
        normalized.append(norm_row)

    fig, ax = plt.subplots(figsize=(11.0, 4.8))
    heat = ax.imshow(normalized, cmap="YlOrBr", aspect="auto", vmin=0.0, vmax=1.0)
    ax.set_title(f"{block.title} (normalized per metric)")
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=35, ha="right")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels)
    cbar = fig.colorbar(heat, ax=ax)
    cbar.set_label("Relative value (0..1)")

    for r in range(len(raw_matrix)):
        for c in range(len(raw_matrix[0])):
            text_color = "white" if normalized[r][c] >= 0.58 else "black"
            ax.text(c, r, f"{raw_matrix[r][c]:.1f}", ha="center", va="center", fontsize=8, color=text_color)

    fig.tight_layout()
    fig.savefig(output_path, dpi=170)
    plt.close(fig)


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
                vals.append(parse_latency_to_ns(row[c_idx], f"{block.title} row {r_idx + 1} '{label}'"))
            require_positive(vals, block.title)
            if any(v == 0 for v in vals):
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
        plot_complexity_heatmap(block, output_path)
        return output_path, "Heatmap (column-wise normalized) with raw metric values annotated."

    if first_col == "pair":
        categories = [row[0] for row in block.rows]
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


def build_report_markdown(
    consolidated: dict,
    complexity: dict,
    tables: list[TableBlock],
    figure_map: list[tuple[Path, str]],
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
    lines.append("- Complexity summary chart is a normalized heatmap because metrics have different units/scales.")
    lines.append("- This report is fail-fast: any malformed source value aborts generation to avoid silent misreporting.")
    lines.append("- For performance figures, dashed horizontal lines are per-pair, per-mechanism averages loaded from `consolidated.json`.")
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
    lines.append("- Rationale: a fully crossed design would multiply the experiment matrix substantially beyond the current 18 triples and 10 benchmark scenarios per triple.")
    lines.append("- Therefore, array scenarios are representative by pair and guest API constraints (including ragged-array sum and byte-array echo), and are explicitly labeled below.")
    lines.append("")
    lines.append("## Scenario Definitions")
    lines.append("")
    lines.append("- `void_call_no_payload` (source key: `void_call`): minimal function invocation overhead with no data payload.")
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
    lines.append("- To address \"future better package\" arguments, keep conclusions version/time bounded and tied to reproducible baselines used in this experiment.")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Values shown as `0 ns` mean the measured latency is below effective timer+measurement resolution for the single-call method in this environment.")
    lines.append("- In performance figures, `0 ns` points are rendered at `1 ns` only so they can be shown on logarithmic axes; this is a visualization floor, not a claimed runtime value.")
    lines.append("- In Tables 7-9, \"native\" refers to **dedicated per-pair interoperability packages** (e.g., JEP/JPype/JNI/cgo/ctypes), not a uniform raw-native implementation style.")
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
        rel_figure = figure_path.relative_to(RESULTS_DIR).as_posix()
        lines.append(f"### Table {i}: {table.title}")
        lines.append("")
        lines.append(format_table_for_report(table, i))
        lines.append("")
        if i in (7, 8, 9):
            lines.append("Note: \"Native\" here means dedicated package baseline for that pair, not raw native glue code.")
            lines.append("")
        lines.append(f"Figure {i}: {figure_desc}")
        lines.append("")
        lines.append(f"![Figure {i} for {table.title}]({rel_figure})")
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

    report_md = build_report_markdown(consolidated, complexity, tables, figure_map)
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
