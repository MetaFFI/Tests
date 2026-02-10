#!/usr/bin/env python3
"""
Code complexity analysis for MetaFFI cross-language testing framework.

Measures SLOC, cyclomatic complexity, file count, and language count for all
18 implementations (6 MetaFFI + 6 native + 6 gRPC), producing a structured
JSON report for thesis comparison tables.

Tools used:
  - cloc: SLOC counting (non-blank, non-comment lines)
  - lizard: Cyclomatic complexity (Go, Python, Java, C)
  - gocyclo: Go-specific cyclomatic complexity (supplementary)
  - radon: Python-specific cyclomatic complexity (supplementary)

Output: tests/results/complexity.json
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


TESTS_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = TESTS_ROOT / "results"

# Language extensions for classification
LANG_MAP = {
    ".go": "Go",
    ".py": "Python",
    ".java": "Java",
    ".c": "C",
    ".h": "C",
    ".proto": "Protobuf",
}

BUILD_FILES = {"go.mod", "go.sum", "go.work", "pom.xml", "requirements.txt",
               "build.ps1", "build.sh", "generate.sh", "generate.bat", "Makefile"}

# Files that are generated (not hand-written) — identified by path patterns
GENERATED_PATTERNS = [
    "/pb/",                  # Go gRPC generated stubs
    "_pb2.py",              # Python gRPC generated stubs
    "_pb2_grpc.py",         # Python gRPC generated stubs
    "/target/",             # Maven generated sources
    "_cgo_export.h",        # cgo generated header
    "/go_jni_bridge.h",     # cgo generated header from -buildmode=c-shared
]


# ---------------------------------------------------------------------------
# Implementation definitions
# ---------------------------------------------------------------------------

@dataclass
class Implementation:
    """Defines one of the 18 test implementations."""
    host: str
    guest: str
    mechanism: str
    label: str
    base_dir: Path
    # Source files: only hand-written code
    source_files: list[Path] = field(default_factory=list)
    # Build config files
    build_files: list[Path] = field(default_factory=list)
    # Proto definition files (hand-written, but separate category)
    proto_files: list[Path] = field(default_factory=list)
    # Generated files (gRPC stubs etc.)
    generated_files: list[Path] = field(default_factory=list)


def _classify_source_role(path: Path) -> str:
    """
    Classify a source file as 'benchmark', 'correctness', or 'shared'.
    Used to separate MetaFFI correctness tests from benchmark code.
    """
    name = path.name.lower()

    # Correctness test files
    if "correctness" in name:
        return "correctness"

    # Benchmark files
    if "benchmark" in name:
        return "benchmark"

    # Bridge/interop files
    if "bridge" in name or "jni_impl" in name:
        return "benchmark"

    # Server files (gRPC)
    if "server" in name:
        return "benchmark"

    # Conftest / setup files are shared
    if "conftest" in name:
        return "shared"

    # Java native declarations
    if "GoBridge" in path.name:
        return "benchmark"

    return "shared"


def _is_generated(path: Path) -> bool:
    """Check if a file path matches a generated-code pattern."""
    path_str = str(path).replace("\\", "/")
    return any(pat in path_str for pat in GENERATED_PATTERNS)


def _is_build_file(path: Path) -> bool:
    """Check if a file is a build configuration file."""
    return path.name in BUILD_FILES


def _classify_files(base_dir: Path) -> tuple[list[Path], list[Path], list[Path], list[Path]]:
    """
    Walk a directory and classify files into source, build, proto, generated.
    Returns (source_files, build_files, proto_files, generated_files).
    """
    source = []
    build = []
    proto = []
    generated = []

    if not base_dir.exists():
        return source, build, proto, generated

    for root, dirs, files in os.walk(base_dir):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {
            ".git", "__pycache__", "node_modules", ".idea",
            "classes", "test-classes", "surefire-reports",
            "maven-status", "maven-archiver",
        }]

        for fname in files:
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()

            # Skip binary/compiled files
            if ext in {".dll", ".so", ".dylib", ".exe", ".class", ".jar",
                       ".o", ".a", ".pyc", ".pyo"}:
                continue

            if _is_build_file(fpath):
                build.append(fpath)
            elif _is_generated(fpath):
                generated.append(fpath)
            elif ext == ".proto":
                proto.append(fpath)
            elif ext in LANG_MAP:
                source.append(fpath)

    return source, build, proto, generated


def define_implementations() -> list[Implementation]:
    """Define all 18 implementations with their file classifications."""

    impls = []

    # Helper to create and classify an implementation
    def add(host: str, guest: str, mechanism: str, label: str, base_dir: Path,
            extra_dirs: list[Path] = None):
        """Create implementation, auto-classify files from base_dir + extra_dirs."""
        impl = Implementation(
            host=host, guest=guest, mechanism=mechanism, label=label,
            base_dir=base_dir,
        )

        all_dirs = [base_dir] + (extra_dirs or [])
        for d in all_dirs:
            src, bld, prt, gen = _classify_files(d)
            impl.source_files.extend(src)
            impl.build_files.extend(bld)
            impl.proto_files.extend(prt)
            impl.generated_files.extend(gen)

        impls.append(impl)
        return impl

    t = TESTS_ROOT

    # --- MetaFFI pairs (6) ---
    add("go", "python3", "metaffi", "Go->Python3 MetaFFI",
        t / "go" / "call_python3")

    add("go", "java", "metaffi", "Go->Java MetaFFI",
        t / "go" / "call_java")

    add("python3", "go", "metaffi", "Python3->Go MetaFFI",
        t / "python3" / "call_go")

    add("python3", "java", "metaffi", "Python3->Java MetaFFI",
        t / "python3" / "call_java")

    add("java", "go", "metaffi", "Java->Go MetaFFI",
        t / "java" / "call_go")

    add("java", "python3", "metaffi", "Java->Python3 MetaFFI",
        t / "java" / "call_python3")

    # --- Native direct pairs (6) ---
    add("go", "python3", "cpython", "Go->Python3 cgo+CPython",
        t / "go" / "without_metaffi" / "call_python3_cpython")

    add("go", "java", "jni", "Go->Java cgo+JNI",
        t / "go" / "without_metaffi" / "call_java_jni")

    add("python3", "go", "ctypes", "Python3->Go ctypes",
        t / "python3" / "without_metaffi" / "call_go_ctypes",
        extra_dirs=[t / "python3" / "without_metaffi" / "call_go_ctypes" / "go_bridge"])

    add("python3", "java", "jpype", "Python3->Java JPype",
        t / "python3" / "without_metaffi" / "call_java_jpype")

    add("java", "go", "jni", "Java->Go JNI+cgo",
        t / "java" / "without_metaffi" / "call_go_jni",
        extra_dirs=[t / "java" / "without_metaffi" / "call_go_jni" / "go_bridge"])

    add("java", "python3", "jep", "Java->Python3 Jep",
        t / "java" / "without_metaffi" / "call_python3_jep")

    # --- gRPC pairs (6) ---
    # gRPC includes client (host) + server (guest) + proto.
    # Some implementations share servers from other pairs:
    #   - Python3->Java gRPC reuses Java server from Go->Java gRPC
    #   - Java->Go gRPC reuses Go server from Python3->Go gRPC
    #   - Java->Python3 gRPC reuses Python server from Go->Python3 gRPC
    # For fair comparison, include shared server code in extra_dirs.

    # These 3 have their own servers
    add("go", "python3", "grpc", "Go->Python3 gRPC",
        t / "go" / "without_metaffi" / "call_python3_grpc")

    add("go", "java", "grpc", "Go->Java gRPC",
        t / "go" / "without_metaffi" / "call_java_grpc")

    add("python3", "go", "grpc", "Python3->Go gRPC",
        t / "python3" / "without_metaffi" / "call_go_grpc")

    # These 3 share servers from the above — include shared server dir
    add("python3", "java", "grpc", "Python3->Java gRPC",
        t / "python3" / "without_metaffi" / "call_java_grpc",
        extra_dirs=[t / "go" / "without_metaffi" / "call_java_grpc" / "server"])

    add("java", "go", "grpc", "Java->Go gRPC",
        t / "java" / "without_metaffi" / "call_go_grpc",
        extra_dirs=[t / "python3" / "without_metaffi" / "call_go_grpc" / "server"])

    add("java", "python3", "grpc", "Java->Python3 gRPC",
        t / "java" / "without_metaffi" / "call_python3_grpc",
        extra_dirs=[t / "go" / "without_metaffi" / "call_python3_grpc" / "server"])

    return impls


# ---------------------------------------------------------------------------
# SLOC counting via cloc
# ---------------------------------------------------------------------------

def count_sloc_cloc(files: list[Path]) -> dict:
    """
    Count SLOC for a list of files using cloc.
    Returns dict with per-language breakdown and total.
    """
    if not files:
        return {"total": 0, "by_language": {}}

    # Write file list to temp file for cloc --list-file
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in files:
            f.write(str(p) + "\n")
        list_file = f.name

    try:
        proc = subprocess.run(
            ["cloc", "--json", f"--list-file={list_file}"],
            capture_output=True, text=True, timeout=60,
        )

        if proc.returncode != 0:
            print(f"  cloc warning: {proc.stderr.strip()}", file=sys.stderr)
            return {"total": 0, "by_language": {}}

        data = json.loads(proc.stdout)

        by_language = {}
        total_code = 0

        for lang, info in data.items():
            if lang in ("header", "SUM"):
                continue
            if isinstance(info, dict) and "code" in info:
                by_language[lang] = {
                    "code": info["code"],
                    "comment": info["comment"],
                    "blank": info["blank"],
                    "files": info["nFiles"],
                }
                total_code += info["code"]

        return {"total": total_code, "by_language": by_language}

    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  cloc error: {e}", file=sys.stderr)
        return {"total": 0, "by_language": {}}
    finally:
        os.unlink(list_file)


# ---------------------------------------------------------------------------
# Cyclomatic complexity via lizard
# ---------------------------------------------------------------------------

def measure_complexity_lizard(files: list[Path]) -> dict:
    """
    Measure cyclomatic complexity using lizard.
    Returns per-function data and aggregate stats.
    """
    if not files:
        return {"functions": [], "max_cc": 0, "avg_cc": 0.0, "total_functions": 0}

    # Filter to files lizard can process
    supported_exts = {".go", ".py", ".java", ".c", ".h", ".cpp", ".js"}
    analyzable = [f for f in files if f.suffix.lower() in supported_exts]

    if not analyzable:
        return {"functions": [], "max_cc": 0, "avg_cc": 0.0, "total_functions": 0}

    file_args = [str(f) for f in analyzable]

    try:
        proc = subprocess.run(
            ["python", "-m", "lizard", "--csv"] + file_args,
            capture_output=True, text=True, timeout=60,
        )

        functions = []
        for line in proc.stdout.strip().split("\n"):
            if not line or line.startswith("NLOC"):
                continue
            parts = line.split(",")
            if len(parts) >= 6:
                try:
                    functions.append({
                        "nloc": int(parts[0]),
                        "ccn": int(parts[1]),
                        "token_count": int(parts[2]),
                        "params": int(parts[3]),
                        "length": int(parts[4]),
                        "name": parts[5].strip('"'),
                    })
                except (ValueError, IndexError):
                    continue

        if not functions:
            return {"functions": [], "max_cc": 0, "avg_cc": 0.0, "total_functions": 0}

        cc_values = [f["ccn"] for f in functions]
        max_cc = max(cc_values)
        avg_cc = sum(cc_values) / len(cc_values)

        return {
            "functions": functions,
            "max_cc": max_cc,
            "avg_cc": round(avg_cc, 2),
            "total_functions": len(functions),
        }

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  lizard error: {e}", file=sys.stderr)
        return {"functions": [], "max_cc": 0, "avg_cc": 0.0, "total_functions": 0}


# ---------------------------------------------------------------------------
# Language and file counting
# ---------------------------------------------------------------------------

def count_languages(files: list[Path]) -> list[str]:
    """Return sorted list of distinct programming languages in the file set."""
    langs = set()
    for f in files:
        ext = f.suffix.lower()
        lang = LANG_MAP.get(ext)
        if lang:
            langs.add(lang)
    return sorted(langs)


# ---------------------------------------------------------------------------
# API surface estimation
# ---------------------------------------------------------------------------

def estimate_api_surface(impl: Implementation) -> dict:
    """
    Estimate the API surface (distinct API calls/concepts) for an implementation.
    Counts distinct import statements and unique API function/method calls.
    """
    imports = set()
    api_calls = set()

    for fpath in impl.source_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line in content.split("\n"):
            stripped = line.strip()

            # Count imports
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.add(stripped)
            elif stripped.startswith("import(") or stripped.startswith("import ("):
                imports.add(stripped)

            # Count MetaFFI API calls
            for api in ["NewMetaFFIRuntime", "LoadRuntimePlugin", "LoadModule",
                        "MetaFFIRuntime", "metaffi_runtime", "MetaFFIModule",
                        "metaffi_module", "load_runtime_plugin", "load_module",
                        "loadRuntimePlugin", "loadModule"]:
                if api in stripped:
                    api_calls.add(api)

            # Count native interop API calls
            for api in ["Py_Initialize", "PyRun_", "PyObject_", "PyUnicode_",
                        "PyLong_", "PyFloat_", "PyList_", "PyTuple_",
                        "JNI_CreateJavaVM", "FindClass", "GetMethodID",
                        "CallObjectMethod", "NewObject", "GetStaticMethodID",
                        "ctypes.cdll", "ctypes.c_", "ctypes.POINTER",
                        "jpype.startJVM", "jpype.JClass", "jpype.JArray",
                        "SharedInterpreter", "interp.exec", "interp.getValue",
                        "grpc.insecure_channel", "grpc.server",
                        "ManagedChannelBuilder", "ServerBuilder",
                        "grpc.Dial", "grpc.NewServer"]:
                if api in stripped:
                    api_calls.add(api)

    return {
        "distinct_imports": len(imports),
        "distinct_api_calls": len(api_calls),
        "api_calls_list": sorted(api_calls),
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

@dataclass
class ImplementationReport:
    """Complete analysis report for one implementation."""
    host: str
    guest: str
    mechanism: str
    label: str

    # File counts
    source_file_count: int = 0
    build_file_count: int = 0
    proto_file_count: int = 0
    generated_file_count: int = 0

    # Language diversity
    languages: list[str] = field(default_factory=list)
    language_count: int = 0

    # SLOC
    source_sloc: dict = field(default_factory=dict)
    benchmark_only_sloc: dict = field(default_factory=dict)  # benchmark + shared files only
    build_sloc: dict = field(default_factory=dict)
    proto_sloc: dict = field(default_factory=dict)
    generated_sloc: dict = field(default_factory=dict)

    # Complexity
    complexity: dict = field(default_factory=dict)

    # API surface
    api_surface: dict = field(default_factory=dict)

    # File listing
    source_files: list[str] = field(default_factory=list)
    build_files: list[str] = field(default_factory=list)
    proto_files: list[str] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)


def analyze_implementation(impl: Implementation) -> ImplementationReport:
    """Run all analyses on a single implementation."""

    report = ImplementationReport(
        host=impl.host,
        guest=impl.guest,
        mechanism=impl.mechanism,
        label=impl.label,
    )

    # File counts
    report.source_file_count = len(impl.source_files)
    report.build_file_count = len(impl.build_files)
    report.proto_file_count = len(impl.proto_files)
    report.generated_file_count = len(impl.generated_files)

    # File listings (relative to tests root)
    report.source_files = [str(f.relative_to(TESTS_ROOT)) for f in impl.source_files]
    report.build_files = [str(f.relative_to(TESTS_ROOT)) for f in impl.build_files]
    report.proto_files = [str(f.relative_to(TESTS_ROOT)) for f in impl.proto_files]
    report.generated_files = [str(f.relative_to(TESTS_ROOT)) for f in impl.generated_files]

    # Languages
    report.languages = count_languages(impl.source_files + impl.proto_files)
    report.language_count = len(report.languages)

    # SLOC
    print(f"  Counting SLOC...", flush=True)
    report.source_sloc = count_sloc_cloc(impl.source_files)
    report.build_sloc = count_sloc_cloc(impl.build_files)
    report.proto_sloc = count_sloc_cloc(impl.proto_files)
    report.generated_sloc = count_sloc_cloc(impl.generated_files)

    # Benchmark-only SLOC (excludes correctness test files, for fair cross-mechanism comparison)
    benchmark_files = [
        f for f in impl.source_files
        if _classify_source_role(f) in ("benchmark", "shared")
    ]
    report.benchmark_only_sloc = count_sloc_cloc(benchmark_files)

    # Complexity
    print(f"  Measuring complexity...", flush=True)
    report.complexity = measure_complexity_lizard(impl.source_files)

    # Don't include per-function details in the JSON (too verbose)
    # Keep only aggregate stats
    report.complexity = {
        "max_cc": report.complexity["max_cc"],
        "avg_cc": report.complexity["avg_cc"],
        "total_functions": report.complexity["total_functions"],
        "top_5_complex": sorted(
            report.complexity["functions"],
            key=lambda f: f["ccn"],
            reverse=True,
        )[:5] if report.complexity["functions"] else [],
    }

    # API surface
    report.api_surface = estimate_api_surface(impl)

    return report


def build_comparison_tables(reports: list[ImplementationReport]) -> dict:
    """Build cross-mechanism comparison tables grouped by (host, guest) pair."""

    # Group by (host, guest)
    pairs: dict[tuple[str, str], dict[str, ImplementationReport]] = {}
    for r in reports:
        key = (r.host, r.guest)
        if key not in pairs:
            pairs[key] = {}
        pairs[key][r.mechanism] = r

    tables = []

    for (host, guest), mechanisms in sorted(pairs.items()):
        row = {
            "host": host,
            "guest": guest,
            "mechanisms": {},
        }

        for mech_name, report in sorted(mechanisms.items()):
            row["mechanisms"][mech_name] = {
                "source_sloc": report.source_sloc.get("total", 0),
                "benchmark_only_sloc": report.benchmark_only_sloc.get("total", 0),
                "build_sloc": report.build_sloc.get("total", 0),
                "proto_sloc": report.proto_sloc.get("total", 0),
                "generated_sloc": report.generated_sloc.get("total", 0),
                "total_hand_written_sloc": (
                    report.source_sloc.get("total", 0) +
                    report.build_sloc.get("total", 0) +
                    report.proto_sloc.get("total", 0)
                ),
                "benchmark_hand_written_sloc": (
                    report.benchmark_only_sloc.get("total", 0) +
                    report.build_sloc.get("total", 0) +
                    report.proto_sloc.get("total", 0)
                ),
                "source_file_count": report.source_file_count,
                "language_count": report.language_count,
                "languages": report.languages,
                "max_cyclomatic_complexity": report.complexity.get("max_cc", 0),
                "avg_cyclomatic_complexity": report.complexity.get("avg_cc", 0.0),
            }

        tables.append(row)

    return {"pair_comparisons": tables}


def build_aggregate_summary(reports: list[ImplementationReport]) -> dict:
    """Build aggregate summary across all mechanisms."""

    by_mechanism: dict[str, list[ImplementationReport]] = {}
    for r in reports:
        mech = r.mechanism
        # Normalize native mechanisms to "native"
        if mech in ("cpython", "jni", "ctypes", "jpype", "jep"):
            mech = "native"
        if mech not in by_mechanism:
            by_mechanism[mech] = []
        by_mechanism[mech].append(r)

    summary = {}
    for mech, group in sorted(by_mechanism.items()):
        slocs = [r.source_sloc.get("total", 0) for r in group]
        bench_slocs = [r.benchmark_only_sloc.get("total", 0) for r in group]
        lang_counts = [r.language_count for r in group]
        file_counts = [r.source_file_count for r in group]
        max_ccs = [r.complexity.get("max_cc", 0) for r in group]

        summary[mech] = {
            "count": len(group),
            "avg_source_sloc": round(sum(slocs) / len(slocs), 1) if slocs else 0,
            "avg_benchmark_sloc": round(sum(bench_slocs) / len(bench_slocs), 1) if bench_slocs else 0,
            "min_source_sloc": min(slocs) if slocs else 0,
            "max_source_sloc": max(slocs) if slocs else 0,
            "avg_language_count": round(sum(lang_counts) / len(lang_counts), 1) if lang_counts else 0,
            "avg_file_count": round(sum(file_counts) / len(file_counts), 1) if file_counts else 0,
            "avg_max_cc": round(sum(max_ccs) / len(max_ccs), 1) if max_ccs else 0,
        }

    return summary


def main() -> int:
    print("MetaFFI Code Complexity Analysis")
    print("=" * 60)

    # Define all implementations
    impls = define_implementations()
    print(f"Found {len(impls)} implementations to analyze.\n")

    # Analyze each
    reports: list[ImplementationReport] = []
    for impl in impls:
        print(f"\n--- {impl.label} ---")
        print(f"  Base: {impl.base_dir}")
        print(f"  Source files: {len(impl.source_files)}")

        if not impl.source_files:
            print(f"  SKIP: No source files found")
            continue

        report = analyze_implementation(impl)
        reports.append(report)

        print(f"  Source SLOC: {report.source_sloc.get('total', 0)}")
        print(f"  Languages: {', '.join(report.languages)}")
        print(f"  Max CC: {report.complexity.get('max_cc', 0)}")

    # Build comparison tables
    print(f"\n{'=' * 60}")
    print("Building comparison tables...")
    comparisons = build_comparison_tables(reports)
    aggregate = build_aggregate_summary(reports)

    # Assemble final report
    output = {
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "total_implementations": len(reports),
        "aggregate_by_mechanism": aggregate,
        "pair_comparisons": comparisons["pair_comparisons"],
        "implementations": [asdict(r) for r in reports],
    }

    # Write output
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / "complexity.json"

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults written to {output_file}")

    # Print summary table
    print(f"\n{'=' * 60}")
    print("SUMMARY BY MECHANISM")
    print(f"{'=' * 60}")
    print(f"{'Mechanism':<12} {'Count':>5} {'Avg SLOC':>10} {'Avg Langs':>10} {'Avg Files':>10} {'Avg Max CC':>11}")
    print("-" * 60)
    for mech, stats in sorted(aggregate.items()):
        print(f"{mech:<12} {stats['count']:>5} {stats['avg_source_sloc']:>10.1f} "
              f"{stats['avg_language_count']:>10.1f} {stats['avg_file_count']:>10.1f} "
              f"{stats['avg_max_cc']:>11.1f}")

    # Print per-pair comparison (all SLOC)
    print(f"\n{'=' * 60}")
    print("PER-PAIR COMPARISON (Total Source SLOC)")
    print(f"{'=' * 60}")
    print(f"{'Pair':<25} {'MetaFFI':>10} {'Native':>10} {'gRPC':>10}")
    print("-" * 60)

    for comp in comparisons["pair_comparisons"]:
        pair_label = f"{comp['host']}->{comp['guest']}"
        mechs = comp["mechanisms"]

        metaffi_sloc = mechs.get("metaffi", {}).get("source_sloc", "-")
        grpc_sloc = mechs.get("grpc", {}).get("source_sloc", "-")

        native_sloc = "-"
        for mech_name, mech_data in mechs.items():
            if mech_name not in ("metaffi", "grpc"):
                native_sloc = mech_data.get("source_sloc", "-")
                break

        print(f"{pair_label:<25} {str(metaffi_sloc):>10} {str(native_sloc):>10} {str(grpc_sloc):>10}")

    # Print per-pair comparison (benchmark-only SLOC — fair comparison)
    print(f"\n{'=' * 60}")
    print("PER-PAIR COMPARISON (Benchmark-Only SLOC)")
    print("  (Excludes MetaFFI correctness tests for fair comparison)")
    print(f"{'=' * 60}")
    print(f"{'Pair':<25} {'MetaFFI':>10} {'Native':>10} {'gRPC':>10}")
    print("-" * 60)

    for comp in comparisons["pair_comparisons"]:
        pair_label = f"{comp['host']}->{comp['guest']}"
        mechs = comp["mechanisms"]

        metaffi_sloc = mechs.get("metaffi", {}).get("benchmark_only_sloc", "-")
        grpc_sloc = mechs.get("grpc", {}).get("benchmark_only_sloc", "-")

        native_sloc = "-"
        for mech_name, mech_data in mechs.items():
            if mech_name not in ("metaffi", "grpc"):
                native_sloc = mech_data.get("benchmark_only_sloc", "-")
                break

        print(f"{pair_label:<25} {str(metaffi_sloc):>10} {str(native_sloc):>10} {str(grpc_sloc):>10}")

    # Print language count comparison
    print(f"\n{'=' * 60}")
    print("PER-PAIR COMPARISON (Languages Required)")
    print(f"{'=' * 60}")
    print(f"{'Pair':<25} {'MetaFFI':>10} {'Native':>10} {'gRPC':>10}")
    print("-" * 60)

    for comp in comparisons["pair_comparisons"]:
        pair_label = f"{comp['host']}->{comp['guest']}"
        mechs = comp["mechanisms"]

        metaffi_langs = mechs.get("metaffi", {}).get("language_count", "-")
        grpc_langs = mechs.get("grpc", {}).get("language_count", "-")

        native_langs = "-"
        for mech_name, mech_data in mechs.items():
            if mech_name not in ("metaffi", "grpc"):
                native_langs = mech_data.get("language_count", "-")
                break

        print(f"{pair_label:<25} {str(metaffi_langs):>10} {str(native_langs):>10} {str(grpc_langs):>10}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
