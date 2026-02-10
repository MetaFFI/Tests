#!/usr/bin/env python3
"""
Run all 18 MetaFFI cross-language tests and benchmarks.

For each (host, guest, mechanism) triple:
  - If a result file already exists and --all is not set: SKIP (print message)
  - Otherwise: run the test, print the command used, report PASS/FAIL/NEW

At the end, prints a summary of all tests and how to re-run any that failed.

Usage:
  python run_all_tests.py              # Run only missing tests
  python run_all_tests.py --all        # Re-run everything, overwrite results
  python run_all_tests.py --host go    # Only run Go-as-host tests
  python run_all_tests.py --pair go:python3  # Only run Go->Python3
  python run_all_tests.py --iterations 50000 --warmup 200
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TESTS_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = TESTS_ROOT / "results"

# All 18 (host, guest, mechanism) triples
ALL_TRIPLES: list[tuple[str, str, str]] = []

HOSTS = ["go", "python3", "java"]

# Native direct mechanism per (host, guest)
NATIVE_MECHANISMS = {
    ("go", "python3"): "cpython",
    ("go", "java"): "jni",
    ("python3", "go"): "ctypes",
    ("python3", "java"): "jpype",
    ("java", "go"): "jni",
    ("java", "python3"): "jep",
}

# Build the full list of 18 triples
for h in HOSTS:
    for g in HOSTS:
        if h == g:
            continue
        ALL_TRIPLES.append((h, g, "metaffi"))
        ALL_TRIPLES.append((h, g, NATIVE_MECHANISMS[(h, g)]))
        ALL_TRIPLES.append((h, g, "grpc"))

DEFAULT_WARMUP = 100
DEFAULT_ITERATIONS = 10000


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TestOutcome:
    """Result of a single test triple execution."""
    host: str
    guest: str
    mechanism: str
    status: str  # "PASS", "FAIL", "SKIP", "NEW"
    result_file: Optional[Path] = None
    command: Optional[str] = None
    error_message: Optional[str] = None
    elapsed_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_maven() -> str:
    """Find Maven executable."""
    for name in ("mvn", "mvn.cmd"):
        try:
            subprocess.run([name, "--version"], capture_output=True, timeout=10)
            return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    choco_mvn = Path(r"C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.12\bin\mvn.cmd")
    if choco_mvn.is_file():
        return str(choco_mvn)

    raise RuntimeError("Maven (mvn) not found on PATH or known install locations")


def _find_jep_home() -> Optional[str]:
    """Find Jep package directory."""
    jep_home = os.environ.get("JEP_HOME")
    if jep_home and Path(jep_home).is_dir():
        return jep_home

    try:
        proc = subprocess.run(
            ["python", "-c",
             "import importlib.util; spec = importlib.util.find_spec('jep'); print(spec.submodule_search_locations[0])"],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            candidate = Path(proc.stdout.strip())
            if candidate.is_dir():
                return str(candidate)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


def triple_label(host: str, guest: str, mechanism: str) -> str:
    return f"{host}->{guest} [{mechanism}]"


def result_filename(host: str, guest: str, mechanism: str) -> str:
    return f"{host}_to_{guest}_{mechanism}.json"


def test_directory(host: str, guest: str, mechanism: str) -> Path:
    if mechanism == "metaffi":
        return TESTS_ROOT / host / f"call_{guest}"
    elif mechanism == "grpc":
        return TESTS_ROOT / host / "without_metaffi" / f"call_{guest}_grpc"
    else:
        return TESTS_ROOT / host / "without_metaffi" / f"call_{guest}_{mechanism}"


def build_command(host: str, guest: str, mechanism: str, iterations: int, warmup: int) -> tuple[list[str], Path, dict]:
    """
    Build the command, working directory, and extra env vars for a test triple.
    Returns (cmd, cwd, extra_env).
    """
    test_dir = test_directory(host, guest, mechanism)
    result_file = RESULTS_DIR / result_filename(host, guest, mechanism)

    extra_env = {
        "METAFFI_TEST_RESULTS_FILE": str(result_file),
        "METAFFI_TEST_ITERATIONS": str(iterations),
        "METAFFI_TEST_WARMUP": str(warmup),
        "METAFFI_TEST_MODE": "all",
    }

    if host == "go":
        cmd = ["go", "test", "-v", "-count=1", "-timeout=600s", "./..."]

    elif host == "python3":
        if mechanism == "metaffi":
            # MetaFFI tests use pytest
            cmd = ["python", "-m", "pytest", "-v", "--tb=short", str(test_dir)]
        else:
            # Native/gRPC benchmarks are standalone scripts
            cmd = ["python", str(test_dir / "benchmark.py")]

    elif host == "java":
        mvn = _find_maven()
        if mechanism == "metaffi":
            test_class = "TestCorrectness,TestBenchmark"
        else:
            test_class = "BenchmarkTest"

        cmd = [mvn, "test", f"-Dtest={test_class}", "-pl", "."]

        # Jep needs JEP_HOME
        if mechanism == "jep":
            jep_home = _find_jep_home()
            if jep_home:
                extra_env["JEP_HOME"] = jep_home

    else:
        raise ValueError(f"Unknown host: {host}")

    return cmd, test_dir, extra_env


def format_command_for_display(cmd: list[str], cwd: Path, extra_env: dict) -> str:
    """Format a command as a human-readable string that can be copy-pasted."""
    env_parts = []
    for k in ("METAFFI_TEST_RESULTS_FILE", "METAFFI_TEST_ITERATIONS", "METAFFI_TEST_WARMUP"):
        if k in extra_env:
            env_parts.append(f'$env:{k}="{extra_env[k]}"')

    # Also include JEP_HOME if present
    if "JEP_HOME" in extra_env:
        env_parts.append(f'$env:JEP_HOME="{extra_env["JEP_HOME"]}"')

    cmd_str = " ".join(cmd)
    parts = []
    if env_parts:
        parts.extend(env_parts)
    parts.append(f"cd {cwd}")
    parts.append(cmd_str)

    return " ; ".join(parts)


def run_test(host: str, guest: str, mechanism: str,
             iterations: int, warmup: int) -> TestOutcome:
    """Run a single test triple and return the outcome."""

    label = triple_label(host, guest, mechanism)
    test_dir = test_directory(host, guest, mechanism)
    result_file = RESULTS_DIR / result_filename(host, guest, mechanism)

    outcome = TestOutcome(host=host, guest=guest, mechanism=mechanism,
                          result_file=result_file)

    # Check test directory exists
    if not test_dir.is_dir():
        outcome.status = "FAIL"
        outcome.error_message = f"Test directory does not exist: {test_dir}"
        return outcome

    # Build command
    try:
        cmd, cwd, extra_env = build_command(host, guest, mechanism, iterations, warmup)
    except RuntimeError as e:
        outcome.status = "FAIL"
        outcome.error_message = str(e)
        return outcome

    outcome.command = format_command_for_display(cmd, cwd, extra_env)

    # Merge env
    env = os.environ.copy()
    env.update(extra_env)

    # Run
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd), env=env,
            capture_output=True, text=True, timeout=600,
        )
    except subprocess.TimeoutExpired:
        outcome.elapsed_seconds = time.monotonic() - start
        outcome.status = "FAIL"
        outcome.error_message = "TIMEOUT after 600s"
        return outcome

    outcome.elapsed_seconds = time.monotonic() - start

    if proc.returncode != 0:
        outcome.status = "FAIL"
        # Capture the last 20 lines of stderr+stdout as error context
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        lines = combined.strip().splitlines()
        tail = "\n".join(lines[-20:]) if len(lines) > 20 else combined.strip()
        outcome.error_message = f"Exit code {proc.returncode}\n{tail}"
        return outcome

    # Verify result file was produced
    if result_file.is_file():
        try:
            with open(result_file) as f:
                data = json.load(f)

            # Check for benchmark failures
            failed_benchmarks = [
                b["scenario"] for b in data.get("benchmarks", [])
                if b.get("status") == "FAIL"
            ]
            correctness = data.get("correctness")
            correctness_failed = (correctness is not None and
                                  correctness.get("status") == "FAIL")

            if correctness_failed or failed_benchmarks:
                outcome.status = "FAIL"
                parts = []
                if correctness_failed:
                    parts.append("correctness FAIL")
                if failed_benchmarks:
                    parts.append(f"benchmarks FAIL: {', '.join(failed_benchmarks)}")
                outcome.error_message = "; ".join(parts)
            else:
                outcome.status = "PASS"

        except (json.JSONDecodeError, KeyError) as e:
            outcome.status = "FAIL"
            outcome.error_message = f"Corrupt result file: {e}"
    else:
        outcome.status = "FAIL"
        outcome.error_message = "No result file produced"

    return outcome


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all MetaFFI cross-language tests. Skips tests with existing results unless --all is set.",
    )
    parser.add_argument("--all", action="store_true",
                        help="Re-run ALL tests, overwriting existing results.")
    parser.add_argument("--host", choices=HOSTS,
                        help="Only run tests where this language is the host.")
    parser.add_argument("--pair",
                        help="Only run a specific pair, e.g. 'go:python3'.")
    parser.add_argument("--mechanism",
                        help="Only run a specific mechanism (metaffi, grpc, or native name).")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS,
                        help=f"Benchmark iterations (default: {DEFAULT_ITERATIONS}).")
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP,
                        help=f"Warmup iterations (default: {DEFAULT_WARMUP}).")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Filter triples
    triples = list(ALL_TRIPLES)
    if args.pair:
        parts = args.pair.split(":")
        if len(parts) != 2:
            print(f"ERROR: Invalid pair '{args.pair}'. Use 'host:guest' format.", file=sys.stderr)
            return 1
        triples = [(h, g, m) for h, g, m in triples if h == parts[0] and g == parts[1]]

    if args.host:
        triples = [(h, g, m) for h, g, m in triples if h == args.host]

    if args.mechanism:
        triples = [(h, g, m) for h, g, m in triples if m == args.mechanism]

    if not triples:
        print("ERROR: No matching test triples found for the given filters.", file=sys.stderr)
        return 1

    print(f"=== MetaFFI Test Runner ===")
    print(f"Total triples to consider: {len(triples)}")
    print(f"Mode: {'RERUN ALL' if args.all else 'SKIP EXISTING'}")
    print(f"Iterations: {args.iterations}, Warmup: {args.warmup}")
    print()

    outcomes: list[TestOutcome] = []
    start_time = time.monotonic()

    for host, guest, mechanism in triples:
        label = triple_label(host, guest, mechanism)
        result_file = RESULTS_DIR / result_filename(host, guest, mechanism)

        # Check if result already exists
        if not args.all and result_file.is_file():
            outcome = TestOutcome(
                host=host, guest=guest, mechanism=mechanism,
                status="SKIP", result_file=result_file,
            )
            outcomes.append(outcome)
            print(f"  SKIP  {label}  (result exists: {result_file.name})")
            continue

        # Build command for display even if we haven't run yet
        try:
            cmd, cwd, extra_env = build_command(host, guest, mechanism,
                                                 args.iterations, args.warmup)
            cmd_display = format_command_for_display(cmd, cwd, extra_env)
        except RuntimeError:
            cmd_display = "<could not build command>"

        print(f"  RUN   {label}")
        print(f"        Command: {cmd_display}")

        outcome = run_test(host, guest, mechanism, args.iterations, args.warmup)
        outcomes.append(outcome)

        if outcome.status == "PASS":
            print(f"  PASS  {label}  ({outcome.elapsed_seconds:.1f}s) -> {result_file.name}")
        else:
            print(f"  FAIL  {label}  ({outcome.elapsed_seconds:.1f}s)")
            if outcome.error_message:
                # Print first line of error indented
                first_line = outcome.error_message.split("\n")[0]
                print(f"        Error: {first_line}")

        print()

    total_time = time.monotonic() - start_time

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------

    passed = [o for o in outcomes if o.status == "PASS"]
    failed = [o for o in outcomes if o.status == "FAIL"]
    skipped = [o for o in outcomes if o.status == "SKIP"]

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total: {len(outcomes)}  |  Passed: {len(passed)}  |  Failed: {len(failed)}  |  Skipped: {len(skipped)}")
    print(f"  Elapsed: {total_time:.1f}s")
    print()

    # Report new results written
    if passed:
        print("NEW RESULTS WRITTEN:")
        for o in passed:
            print(f"  {triple_label(o.host, o.guest, o.mechanism)} -> {o.result_file.name}")
        print()

    # Report skipped (existing results)
    if skipped:
        print("SKIPPED (existing results):")
        for o in skipped:
            print(f"  {triple_label(o.host, o.guest, o.mechanism)} -> {o.result_file.name}")
        print()

    # Report failures with re-run commands
    if failed:
        print("FAILED TESTS:")
        for o in failed:
            print(f"  {triple_label(o.host, o.guest, o.mechanism)}")
            if o.error_message:
                first_line = o.error_message.split("\n")[0]
                print(f"    Error: {first_line}")
            if o.command:
                print(f"    Re-run: {o.command}")
            else:
                print(f"    (no command available - check test directory)")
            print()

    # Report MISSING result files (expected but not generated)
    all_expected = set()
    for h, g, m in ALL_TRIPLES:
        all_expected.add(result_filename(h, g, m))

    existing_results = {p.name for p in RESULTS_DIR.glob("*_to_*.json")}
    missing = sorted(all_expected - existing_results)

    if missing:
        print("MISSING RESULT FILES (no data for these triples):")
        for name in missing:
            print(f"  {name}")
        print()

    # Run consolidation
    consolidate_script = TESTS_ROOT / "consolidate_results.py"
    if consolidate_script.is_file() and (passed or args.all):
        print("Running consolidation...")
        subprocess.run([sys.executable, str(consolidate_script)], cwd=str(TESTS_ROOT))
        print()

    # Run table generation
    tables_script = TESTS_ROOT / "generate_tables.py"
    if tables_script.is_file() and (passed or args.all):
        print("Generating tables...")
        subprocess.run([sys.executable, str(tables_script)], cwd=str(TESTS_ROOT))
        print()

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
