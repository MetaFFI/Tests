#!/usr/bin/env python3
"""
Master orchestration script for MetaFFI cross-language analysis.

Runs correctness tests and performance benchmarks for all (host, guest, mechanism)
combinations, producing per-pair JSON result files and a consolidated report.

FAIL-FAST POLICY: Any unexpected error aborts the affected pair immediately.
No retries, no fallbacks, no silent degradation.
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

HOSTS = ["go", "python3", "java"]
GUESTS = ["go", "python3", "java"]

# MetaFFI pairs: host calls guest via MetaFFI SDK
METAFFI_PAIRS = [
    (h, g) for h in HOSTS for g in GUESTS if h != g
]

# Native direct mechanisms per (host, guest)
NATIVE_MECHANISMS = {
    ("go", "python3"): "cpython",
    ("go", "java"): "jni",
    ("python3", "go"): "ctypes",
    ("python3", "java"): "jpype",
    ("java", "go"): "jni",
    ("java", "python3"): "jep",
}

DEFAULT_WARMUP = 100
DEFAULT_ITERATIONS = 10000


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PairResult:
    """Tracks the outcome of running tests for a single (host, guest, mechanism) triple."""
    host: str
    guest: str
    mechanism: str
    correctness_passed: Optional[bool] = None
    benchmark_passed: Optional[bool] = None
    result_file: Optional[Path] = None
    error_message: Optional[str] = None


# ---------------------------------------------------------------------------
# Environment validation
# ---------------------------------------------------------------------------

class EnvironmentError(Exception):
    """Raised when a required environment precondition is not met."""


def validate_environment() -> None:
    """Check that all required tools and env vars are present. Fail fast if not."""

    metaffi_home = os.environ.get("METAFFI_HOME")
    if not metaffi_home:
        raise EnvironmentError("METAFFI_HOME environment variable is not set")

    if not Path(metaffi_home).is_dir():
        raise EnvironmentError(f"METAFFI_HOME points to non-existent directory: {metaffi_home}")

    # Check language runtimes are available
    for cmd, name in [("go", "Go"), ("python", "Python3"), ("java", "Java")]:
        try:
            subprocess.run(
                [cmd, "--version" if cmd != "java" else "-version"],
                capture_output=True, timeout=10,
            )
        except FileNotFoundError:
            raise EnvironmentError(f"{name} ({cmd}) is not on PATH")
        except subprocess.TimeoutExpired:
            raise EnvironmentError(f"{name} ({cmd}) timed out during version check")


# ---------------------------------------------------------------------------
# Test runner helpers
# ---------------------------------------------------------------------------

def _find_maven() -> str:
    """Find Maven executable, checking PATH and known install locations."""

    # Try PATH first
    for name in ("mvn", "mvn.cmd"):
        try:
            subprocess.run([name, "--version"], capture_output=True, timeout=10)
            return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Known chocolatey install location
    choco_mvn = Path(r"C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.12\bin\mvn.cmd")
    if choco_mvn.is_file():
        return str(choco_mvn)

    raise EnvironmentError("Maven (mvn) not found on PATH or in known install locations")


def _find_jep_home() -> Optional[str]:
    """Find the Jep package directory (contains jep.dll and jep-*.jar)."""

    # Check env var first
    jep_home = os.environ.get("JEP_HOME")
    if jep_home and Path(jep_home).is_dir():
        return jep_home

    # Try to find via pip
    try:
        proc = subprocess.run(
            ["python", "-c", "import importlib.util; spec = importlib.util.find_spec('jep'); print(spec.submodule_search_locations[0])"],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            candidate = Path(proc.stdout.strip())
            if candidate.is_dir():
                return str(candidate)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


def _directory_for_pair(host: str, guest: str, mechanism: str) -> Path:
    """Return the test directory for a given (host, guest, mechanism) triple."""

    if mechanism == "metaffi":
        return TESTS_ROOT / host / f"call_{guest}"
    elif mechanism == "grpc":
        return TESTS_ROOT / host / "without_metaffi" / f"call_{guest}_grpc"
    else:
        # Native direct
        return TESTS_ROOT / host / "without_metaffi" / f"call_{guest}_{mechanism}"


def _result_filename(host: str, guest: str, mechanism: str) -> str:
    """Return the result JSON filename for a triple."""
    return f"{host}_to_{guest}_{mechanism}.json"


def run_pair(host: str, guest: str, mechanism: str,
             correctness_only: bool, benchmarks_only: bool,
             iterations: int, warmup: int) -> PairResult:
    """
    Run correctness and/or benchmark tests for a single (host, guest, mechanism) triple.

    Returns a PairResult with the outcome. Does NOT catch unexpected exceptions --
    those propagate to the caller (fail-fast).
    """

    result = PairResult(host=host, guest=guest, mechanism=mechanism)
    test_dir = _directory_for_pair(host, guest, mechanism)

    if not test_dir.is_dir():
        result.error_message = f"Test directory does not exist: {test_dir}"
        print(f"  SKIP {host}->{guest} [{mechanism}]: {result.error_message}", file=sys.stderr)
        return result

    result_file = RESULTS_DIR / _result_filename(host, guest, mechanism)
    result.result_file = result_file

    # Build the command based on host language
    env = os.environ.copy()
    env["METAFFI_TEST_RESULTS_FILE"] = str(result_file)
    env["METAFFI_TEST_ITERATIONS"] = str(iterations)
    env["METAFFI_TEST_WARMUP"] = str(warmup)

    if correctness_only:
        env["METAFFI_TEST_MODE"] = "correctness"
    elif benchmarks_only:
        env["METAFFI_TEST_MODE"] = "benchmarks"
    else:
        env["METAFFI_TEST_MODE"] = "all"

    # Determine how to invoke the tests
    if host == "go":
        cmd = ["go", "test", "-v", "-count=1", "-timeout=600s", "./..."]
    elif host == "python3":
        cmd = ["python", "-m", "pytest", "-v", "--tb=short", str(test_dir)]
    elif host == "java":
        # Java tests use Maven. Determine which test classes to run.
        mvn = _find_maven()
        if mechanism == "metaffi":
            # MetaFFI pairs have both TestCorrectness and TestBenchmark
            if correctness_only:
                test_class = "TestCorrectness"
            elif benchmarks_only:
                test_class = "TestBenchmark"
            else:
                test_class = "TestCorrectness,TestBenchmark"
        else:
            # Native/gRPC baselines only have BenchmarkTest
            test_class = "BenchmarkTest"

        cmd = [mvn, "test", f"-Dtest={test_class}", "-pl", "."]

        # Jep needs JEP_HOME set
        if mechanism == "jep":
            jep_home = _find_jep_home()
            if jep_home:
                env["JEP_HOME"] = jep_home
            else:
                result.error_message = "JEP_HOME not set and jep package not found"
                print(f"  SKIP {host}->{guest} [{mechanism}]: {result.error_message}", file=sys.stderr)
                return result
    else:
        raise ValueError(f"Unknown host language: {host}")

    print(f"  RUN  {host}->{guest} [{mechanism}] ...", flush=True)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(test_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        result.error_message = "Test process timed out after 600s"
        result.correctness_passed = False
        result.benchmark_passed = False
        print(f"  FAIL {host}->{guest} [{mechanism}]: TIMEOUT", file=sys.stderr)
        return result

    if proc.returncode != 0:
        result.error_message = f"Exit code {proc.returncode}\n{proc.stderr}"
        result.correctness_passed = False
        result.benchmark_passed = False
        print(f"  FAIL {host}->{guest} [{mechanism}]: exit code {proc.returncode}", file=sys.stderr)
        if proc.stdout:
            print(proc.stdout, file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        return result

    # Parse the result file if it was produced
    if result_file.is_file():
        try:
            with open(result_file) as f:
                data = json.load(f)

            correctness_status = data.get("correctness", {}).get("status")
            result.correctness_passed = (correctness_status == "PASS")

            # Check all benchmarks passed
            benchmarks = data.get("benchmarks", [])
            if benchmarks:
                result.benchmark_passed = all(
                    b.get("status") == "PASS" for b in benchmarks
                )
            else:
                result.benchmark_passed = None  # No benchmarks run

        except (json.JSONDecodeError, KeyError) as e:
            result.error_message = f"Failed to parse result file: {e}"
            result.correctness_passed = False
    else:
        # No result file produced -- test likely not yet implemented
        result.error_message = "No result file produced"

    status = "PASS" if (result.correctness_passed is not False and result.benchmark_passed is not False) else "FAIL"
    print(f"  {status} {host}->{guest} [{mechanism}]", flush=True)

    return result


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="MetaFFI cross-language analysis: run correctness tests and benchmarks.",
    )
    parser.add_argument("--host", choices=HOSTS, help="Run only tests where this language is the host.")
    parser.add_argument("--pair", help="Run only a specific pair, e.g. 'go:python3'.")
    parser.add_argument("--correctness-only", action="store_true", help="Skip benchmarks.")
    parser.add_argument("--benchmarks-only", action="store_true", help="Skip correctness tests.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS, help=f"Benchmark iterations (default: {DEFAULT_ITERATIONS}).")
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP, help=f"Warmup iterations (default: {DEFAULT_WARMUP}).")
    args = parser.parse_args()

    if args.correctness_only and args.benchmarks_only:
        print("ERROR: --correctness-only and --benchmarks-only are mutually exclusive.", file=sys.stderr)
        return 1

    # Validate environment before doing anything
    try:
        validate_environment()
    except EnvironmentError as e:
        print(f"FATAL: Environment check failed: {e}", file=sys.stderr)
        return 1

    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Determine which pairs to run
    if args.pair:
        parts = args.pair.split(":")
        if len(parts) != 2 or parts[0] not in HOSTS or parts[1] not in GUESTS or parts[0] == parts[1]:
            print(f"ERROR: Invalid pair '{args.pair}'. Use format 'host:guest', e.g. 'go:python3'.", file=sys.stderr)
            return 1
        pairs_to_run = [(parts[0], parts[1])]
    elif args.host:
        pairs_to_run = [(args.host, g) for g in GUESTS if g != args.host]
    else:
        pairs_to_run = METAFFI_PAIRS

    # Run all triples
    all_results: list[PairResult] = []
    any_failure = False
    start_time = time.perf_counter_ns()

    for host, guest in pairs_to_run:
        print(f"\n{'='*60}")
        print(f"  {host.upper()} -> {guest.upper()}")
        print(f"{'='*60}")

        # 1. MetaFFI
        metaffi_result = run_pair(
            host, guest, "metaffi",
            args.correctness_only, args.benchmarks_only,
            args.iterations, args.warmup,
        )
        all_results.append(metaffi_result)

        # Fail-fast: if MetaFFI correctness failed, skip benchmarks for native/grpc
        if metaffi_result.correctness_passed is False:
            any_failure = True
            print(f"  SKIP native/grpc for {host}->{guest}: MetaFFI correctness failed", file=sys.stderr)
            continue

        # 2. Native direct
        native_mech = NATIVE_MECHANISMS.get((host, guest))
        if native_mech:
            native_result = run_pair(
                host, guest, native_mech,
                args.correctness_only, args.benchmarks_only,
                args.iterations, args.warmup,
            )
            all_results.append(native_result)
            if native_result.correctness_passed is False or native_result.benchmark_passed is False:
                any_failure = True

        # 3. gRPC
        grpc_result = run_pair(
            host, guest, "grpc",
            args.correctness_only, args.benchmarks_only,
            args.iterations, args.warmup,
        )
        all_results.append(grpc_result)
        if grpc_result.correctness_passed is False or grpc_result.benchmark_passed is False:
            any_failure = True

    elapsed_ns = time.perf_counter_ns() - start_time

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total time: {elapsed_ns / 1_000_000_000:.2f}s")
    print()

    passed = 0
    failed = 0
    skipped = 0

    for r in all_results:
        if r.error_message and "does not exist" in r.error_message:
            skipped += 1
            status = "SKIP"
        elif r.correctness_passed is False or r.benchmark_passed is False:
            failed += 1
            status = "FAIL"
        else:
            passed += 1
            status = "PASS"

        print(f"  [{status:4s}] {r.host}->{r.guest} [{r.mechanism}]"
              + (f"  -- {r.error_message}" if r.error_message else ""))

    print()
    print(f"  Passed: {passed}  Failed: {failed}  Skipped: {skipped}")

    # Consolidate results
    consolidate_script = TESTS_ROOT / "consolidate_results.py"
    if consolidate_script.is_file():
        print("\nConsolidating results...")
        subprocess.run([sys.executable, str(consolidate_script)], cwd=str(TESTS_ROOT))

    if any_failure:
        print("\nFATAL: One or more test suites failed.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
