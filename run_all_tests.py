#!/usr/bin/env python3
"""
Config-driven runner for MetaFFI cross-language benchmarks/correctness.

Fail-fast policy:
- --config is mandatory.
- Any missing/unknown config key, malformed value, command failure, or
  aggregation mismatch aborts immediately (unless config.execution.fail_fast=false).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


TESTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TESTS_ROOT.parent

HOSTS = ["go", "python3", "java"]
NATIVE_MECHANISMS = {
    ("go", "python3"): "cpython",
    ("go", "java"): "jni",
    ("python3", "go"): "ctypes",
    ("python3", "java"): "jpype",
    ("java", "go"): "jni",
    ("java", "python3"): "jep",
}

ALL_TRIPLES: list[tuple[str, str, str]] = []
for h in HOSTS:
    for g in HOSTS:
        if h == g:
            continue
        ALL_TRIPLES.append((h, g, "metaffi"))
        ALL_TRIPLES.append((h, g, NATIVE_MECHANISMS[(h, g)]))
        ALL_TRIPLES.append((h, g, "grpc"))

ALL_MECHANISMS = sorted({m for _, _, m in ALL_TRIPLES})


class ConfigError(Exception):
    pass


class RunnerError(Exception):
    pass


@dataclass
class Config:
    include_benchmarks: bool
    include_correctness: bool
    repeats: int
    warmup_iterations: int
    measured_iterations: int
    batch_min_elapsed_ns: int
    batch_max_calls: int
    heartbeat_seconds: int

    hosts: list[str]
    pairs: list[tuple[str, str]]
    mechanisms: list[str]

    rerun_existing: bool
    fail_fast: bool
    default_timeout_seconds: int
    java_metaffi_timeout_seconds: int

    canonical_results_dir: Path
    repeat_root_dir: Path
    write_repeat_files: bool
    run_complexity: bool
    run_consolidation: bool
    run_tables: bool
    run_report: bool


@dataclass
class StageOutcome:
    host: str
    guest: str
    mechanism: str
    stage: str
    repeat_index: int | None
    status: str
    elapsed_seconds: float
    command_display: str
    error_message: str | None = None


def sanitize_path_component(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")
    if not cleaned:
        raise ConfigError(f"Config filename stem '{name}' cannot be sanitized into a valid path component")
    return cleaned


def require_keys(obj: dict[str, Any], expected: set[str], ctx: str) -> None:
    missing = expected - set(obj.keys())
    unknown = set(obj.keys()) - expected
    if missing:
        raise ConfigError(f"{ctx}: missing required keys: {sorted(missing)}")
    if unknown:
        raise ConfigError(f"{ctx}: unknown keys (fail-fast): {sorted(unknown)}")


def parse_pair(pair: str) -> tuple[str, str]:
    parts = pair.split(":")
    if len(parts) != 2:
        raise ConfigError(f"Invalid pair '{pair}', expected host:guest")
    host, guest = parts[0].strip().lower(), parts[1].strip().lower()
    if host not in HOSTS or guest not in HOSTS or host == guest:
        raise ConfigError(f"Invalid pair '{pair}', allowed hosts={HOSTS} and host!=guest")
    return host, guest


def load_config(path: Path) -> Config:
    if not path.is_file():
        raise ConfigError(f"Config file does not exist: {path}")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError("Top-level YAML must be a mapping")

    require_keys(data, {"run", "selection", "execution", "outputs"}, "config")

    run = data["run"]
    selection = data["selection"]
    execution = data["execution"]
    outputs = data["outputs"]

    if not isinstance(run, dict):
        raise ConfigError("run must be a mapping")
    if not isinstance(selection, dict):
        raise ConfigError("selection must be a mapping")
    if not isinstance(execution, dict):
        raise ConfigError("execution must be a mapping")
    if not isinstance(outputs, dict):
        raise ConfigError("outputs must be a mapping")

    require_keys(
        run,
        {
            "include_benchmarks",
            "include_correctness",
            "repeats",
            "warmup_iterations",
            "measured_iterations",
            "batch_min_elapsed_ns",
            "batch_max_calls",
            "heartbeat_seconds",
        },
        "run",
    )
    require_keys(selection, {"hosts", "pairs", "mechanisms"}, "selection")
    require_keys(
        execution,
        {
            "rerun_existing",
            "fail_fast",
            "default_timeout_seconds",
            "java_metaffi_timeout_seconds",
        },
        "execution",
    )
    require_keys(
        outputs,
        {
            "canonical_results_dir",
            "repeat_root_dir",
            "write_repeat_files",
            "run_complexity",
            "run_consolidation",
            "run_tables",
            "run_report",
        },
        "outputs",
    )

    def as_bool(v: Any, key: str) -> bool:
        if not isinstance(v, bool):
            raise ConfigError(f"{key} must be boolean")
        return v

    def as_pos_int(v: Any, key: str, min_value: int = 1) -> int:
        if not isinstance(v, int):
            raise ConfigError(f"{key} must be integer")
        if v < min_value:
            raise ConfigError(f"{key} must be >= {min_value}")
        return v

    include_benchmarks = as_bool(run["include_benchmarks"], "run.include_benchmarks")
    include_correctness = as_bool(run["include_correctness"], "run.include_correctness")
    if not include_benchmarks and not include_correctness:
        raise ConfigError("At least one of run.include_benchmarks/run.include_correctness must be true")

    repeats = as_pos_int(run["repeats"], "run.repeats")
    warmup_iterations = as_pos_int(run["warmup_iterations"], "run.warmup_iterations", min_value=0)
    measured_iterations = as_pos_int(run["measured_iterations"], "run.measured_iterations")
    batch_min_elapsed_ns = as_pos_int(run["batch_min_elapsed_ns"], "run.batch_min_elapsed_ns")
    batch_max_calls = as_pos_int(run["batch_max_calls"], "run.batch_max_calls")
    heartbeat_seconds = as_pos_int(run["heartbeat_seconds"], "run.heartbeat_seconds")

    hosts = selection["hosts"]
    if not isinstance(hosts, list) or not hosts:
        raise ConfigError("selection.hosts must be a non-empty list")
    hosts_norm = []
    for h in hosts:
        if not isinstance(h, str):
            raise ConfigError("selection.hosts entries must be strings")
        hn = h.strip().lower()
        if hn not in HOSTS:
            raise ConfigError(f"selection.hosts contains unsupported host '{h}'")
        hosts_norm.append(hn)

    pairs = selection["pairs"]
    if not isinstance(pairs, list):
        raise ConfigError("selection.pairs must be a list")
    pairs_norm = [parse_pair(p) for p in pairs]

    mechanisms = selection["mechanisms"]
    if not isinstance(mechanisms, list) or not mechanisms:
        raise ConfigError("selection.mechanisms must be a non-empty list")
    mechs_norm = []
    for m in mechanisms:
        if not isinstance(m, str):
            raise ConfigError("selection.mechanisms entries must be strings")
        mn = m.strip().lower()
        if mn not in ALL_MECHANISMS:
            raise ConfigError(f"selection.mechanisms contains unsupported mechanism '{m}'")
        mechs_norm.append(mn)

    rerun_existing = as_bool(execution["rerun_existing"], "execution.rerun_existing")
    fail_fast = as_bool(execution["fail_fast"], "execution.fail_fast")
    default_timeout_seconds = as_pos_int(execution["default_timeout_seconds"], "execution.default_timeout_seconds")
    java_metaffi_timeout_seconds = as_pos_int(
        execution["java_metaffi_timeout_seconds"], "execution.java_metaffi_timeout_seconds"
    )

    canonical_results_dir = (REPO_ROOT / str(outputs["canonical_results_dir"]))
    repeat_root_dir = (REPO_ROOT / str(outputs["repeat_root_dir"]))
    write_repeat_files = as_bool(outputs["write_repeat_files"], "outputs.write_repeat_files")
    run_complexity = as_bool(outputs["run_complexity"], "outputs.run_complexity")
    run_consolidation = as_bool(outputs["run_consolidation"], "outputs.run_consolidation")
    run_tables = as_bool(outputs["run_tables"], "outputs.run_tables")
    run_report = as_bool(outputs["run_report"], "outputs.run_report")

    return Config(
        include_benchmarks=include_benchmarks,
        include_correctness=include_correctness,
        repeats=repeats,
        warmup_iterations=warmup_iterations,
        measured_iterations=measured_iterations,
        batch_min_elapsed_ns=batch_min_elapsed_ns,
        batch_max_calls=batch_max_calls,
        heartbeat_seconds=heartbeat_seconds,
        hosts=hosts_norm,
        pairs=pairs_norm,
        mechanisms=mechs_norm,
        rerun_existing=rerun_existing,
        fail_fast=fail_fast,
        default_timeout_seconds=default_timeout_seconds,
        java_metaffi_timeout_seconds=java_metaffi_timeout_seconds,
        canonical_results_dir=canonical_results_dir,
        repeat_root_dir=repeat_root_dir,
        write_repeat_files=write_repeat_files,
        run_complexity=run_complexity,
        run_consolidation=run_consolidation,
        run_tables=run_tables,
        run_report=run_report,
    )


def triple_label(triple: tuple[str, str, str]) -> str:
    h, g, m = triple
    return f"{h}->{g} [{m}]"


def result_filename(triple: tuple[str, str, str]) -> str:
    h, g, m = triple
    return f"{h}_to_{g}_{m}.json"


def triple_key(triple: tuple[str, str, str]) -> str:
    return f"{triple[0]}|{triple[1]}|{triple[2]}"


def config_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resume_state_path(repeat_root_dir: Path, config_stem: str) -> Path:
    return repeat_root_dir / "_state" / f"{config_stem}.json"


def empty_resume_state(config_sha: str, config_path: Path) -> dict[str, Any]:
    return {
        "version": 1,
        "config_sha256": config_sha,
        "config_path": str(config_path),
        "benchmarks": {},
        "correctness": {},
    }


def load_resume_state(state_file: Path, config_sha: str, config_path: Path) -> dict[str, Any]:
    if not state_file.is_file():
        return empty_resume_state(config_sha, config_path)

    try:
        raw = json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RunnerError(f"Malformed resume state JSON: {state_file}: {e}") from e

    if not isinstance(raw, dict):
        raise RunnerError(f"Malformed resume state (expected object): {state_file}")

    if raw.get("version") != 1:
        raise RunnerError(f"Unsupported resume state version in {state_file}: {raw.get('version')}")

    if raw.get("config_sha256") != config_sha:
        print("Resume state exists for same config name but different file content; starting fresh state.")
        return empty_resume_state(config_sha, config_path)

    if not isinstance(raw.get("benchmarks"), dict) or not isinstance(raw.get("correctness"), dict):
        raise RunnerError(f"Malformed resume state content in {state_file}")

    return raw


def save_resume_state(state_file: Path, state: dict[str, Any]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def filter_triples(cfg: Config) -> list[tuple[str, str, str]]:
    triples: list[tuple[str, str, str]] = []
    allowed_pairs = set(cfg.pairs)
    for h, g, m in ALL_TRIPLES:
        if h not in cfg.hosts:
            continue
        if allowed_pairs and (h, g) not in allowed_pairs:
            continue
        if m not in cfg.mechanisms:
            continue
        triples.append((h, g, m))

    if not triples:
        raise RunnerError("No triples selected by config")
    return triples


def test_directory(triple: tuple[str, str, str]) -> Path:
    host, guest, mechanism = triple
    if mechanism == "metaffi":
        return TESTS_ROOT / host / f"call_{guest}"
    if mechanism == "grpc":
        return TESTS_ROOT / host / "without_metaffi" / f"call_{guest}_grpc"
    return TESTS_ROOT / host / "without_metaffi" / f"call_{guest}_{mechanism}"


def _find_maven() -> str:
    for name in ("mvn", "mvn.cmd"):
        try:
            subprocess.run([name, "--version"], capture_output=True, timeout=10, check=False)
            return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    choco = Path(r"C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.12\bin\mvn.cmd")
    if choco.is_file():
        return str(choco)
    raise RunnerError("Maven not found (mvn/mvn.cmd)")


def _find_jep_home() -> str | None:
    env_val = os.environ.get("JEP_HOME")
    if env_val and Path(env_val).is_dir():
        return env_val

    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import importlib.util; s=importlib.util.find_spec('jep'); print(s.submodule_search_locations[0] if s and s.submodule_search_locations else '')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        candidate = proc.stdout.strip()
        if candidate and Path(candidate).is_dir():
            return candidate
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None

def build_stage_commands(
    triple: tuple[str, str, str],
    stage: str,
    cfg: Config,
    result_path: Path | None,
    scenario_selectors: list[str] | None,
) -> tuple[list[list[str]], Path, dict[str, str]]:
    host, guest, mechanism = triple
    cwd = test_directory(triple)
    if not cwd.is_dir():
        raise RunnerError(f"Test directory missing for {triple_label(triple)}: {cwd}")

    env: dict[str, str] = {
        "METAFFI_TEST_WARMUP": str(cfg.warmup_iterations),
        "METAFFI_TEST_ITERATIONS": str(cfg.measured_iterations),
        "METAFFI_TEST_BATCH_MIN_ELAPSED_NS": str(cfg.batch_min_elapsed_ns),
        "METAFFI_TEST_BATCH_MAX_CALLS": str(cfg.batch_max_calls),
        "METAFFI_TEST_MODE": "benchmarks" if stage == "benchmark" else "correctness",
    }
    if stage == "benchmark" and scenario_selectors:
        env["METAFFI_TEST_SCENARIOS"] = ",".join(scenario_selectors)
    if result_path is not None:
        env["METAFFI_TEST_RESULTS_FILE"] = str(result_path)

    if stage not in ("benchmark", "correctness"):
        raise RunnerError(f"Unknown stage: {stage}")

    if stage == "correctness":
        if mechanism != "metaffi":
            return [], cwd, env
        if host == "go":
            return [["go", "test", "-v", "-count=1", "-timeout=600s", "./..."]], cwd, env
        if host == "python3":
            test_file = cwd / "test_correctness.py"
            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
            if guest == "java":
                cmd.extend(["-p", "no:faulthandler"])
            cmd.append(str(test_file))
            return [cmd], cwd, env
        if host == "java":
            mvn = _find_maven()
            return [[mvn, "test", "-Dtest=TestCorrectness", "-pl", "."]], cwd, env
        raise RunnerError(f"Unsupported host: {host}")

    if host == "go":
        return [["go", "test", "-v", "-run", "TestBenchmarkAll", "-count=1", "-timeout=600s", "./..."]], cwd, env

    if host == "python3":
        if mechanism == "metaffi":
            test_file = cwd / "test_benchmark.py"
            cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
            if guest == "java":
                cmd.extend(["-p", "no:faulthandler"])
            cmd.extend([str(test_file), "-k", "test_all_benchmarks"])
            return [cmd], cwd, env
        return [[sys.executable, str(cwd / "benchmark.py")]], cwd, env

    if host == "java":
        mvn = _find_maven()
        # Avoid method-level selector flakiness on default-package tests in Surefire.
        test_class = "TestBenchmark" if mechanism == "metaffi" else "BenchmarkTest"

        if mechanism == "jni" and guest == "go":
            go_bridge_dir = cwd / "go_bridge"
            if not go_bridge_dir.is_dir():
                raise RunnerError(f"Missing Go JNI bridge directory: {go_bridge_dir}")
            build_script = go_bridge_dir / "build.ps1"
            if not build_script.is_file():
                raise RunnerError(f"Missing Go JNI bridge build script: {build_script}")
            return [
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(build_script)],
                [mvn, "test", f"-Dtest={test_class}", "-pl", "."],
            ], cwd, env

        if mechanism == "jep":
            jep_home = _find_jep_home()
            if jep_home:
                env["JEP_HOME"] = jep_home

        # gRPC Java modules generate protobuf stubs under target/.  Stale
        # .class files from a previous protobuf version cause NoSuchMethodError
        # at runtime.  We nuke the entire target/ dir via the OS shell before
        # running Maven (shutil.rmtree silently fails on Windows file locks).
        if mechanism == "grpc":
            return [[mvn, "compile", "test", f"-Dtest={test_class}", "-pl", "."]], cwd, env

        return [[mvn, "test", f"-Dtest={test_class}", "-pl", "."]], cwd, env

    raise RunnerError(f"Unsupported host: {host}")


def timeout_for(triple: tuple[str, str, str], cfg: Config) -> int:
    host, _, mechanism = triple
    if host == "java" and mechanism == "metaffi":
        return cfg.java_metaffi_timeout_seconds
    return cfg.default_timeout_seconds


def should_retry_transient_failure(
    triple: tuple[str, str, str],
    stage: str,
    tail: str,
) -> bool:
    host, guest, mechanism = triple
    if stage != "benchmark" or host != "java" or mechanism != "grpc":
        return False

    if "BenchmarkProto$ArraySumRequest" in tail and "access$7()" in tail and "NoSuchMethod" in tail:
        return True

    retry_markers = (
        "Unable to clean up temporary proto file directory",
        "Proto path element is not a directory",
        "Unable to create test class 'BenchmarkTest'",
    )
    return any(marker in tail for marker in retry_markers)


def format_command_display(commands: list[list[str]], cwd: Path, env: dict[str, str]) -> str:
    env_keys = [
        "METAFFI_TEST_RESULTS_FILE",
        "METAFFI_TEST_ITERATIONS",
        "METAFFI_TEST_WARMUP",
        "METAFFI_TEST_BATCH_MIN_ELAPSED_NS",
        "METAFFI_TEST_BATCH_MAX_CALLS",
        "METAFFI_TEST_SCENARIOS",
        "METAFFI_TEST_MODE",
        "JEP_HOME",
    ]
    env_parts = [f'$env:{k}="{env[k]}"' for k in env_keys if k in env]
    parts = env_parts + [f"cd {cwd}"] + [" ".join(cmd) for cmd in commands]
    return " ; ".join(parts)


def run_command_with_heartbeat(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    heartbeat_seconds: int,
    heartbeat_label: str,
) -> tuple[int, float, str, bool]:
    start = time.monotonic()
    next_heartbeat = start + heartbeat_seconds

    with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as tf:
        log_path = Path(tf.name)

    try:
        with open(log_path, "wb") as logf:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                env=env,
                stdout=logf,
                stderr=subprocess.STDOUT,
            )

            timed_out = False
            while True:
                rc = proc.poll()
                now = time.monotonic()
                if rc is not None:
                    break
                elapsed = now - start
                if elapsed > timeout_seconds:
                    proc.kill()
                    proc.wait()
                    timed_out = True
                    rc = -99999
                    break
                if now >= next_heartbeat:
                    print(f"        [alive] {heartbeat_label} | elapsed={elapsed:.1f}s")
                    next_heartbeat = now + heartbeat_seconds
                time.sleep(0.5)

        elapsed = time.monotonic() - start
        full_log = log_path.read_text(encoding="utf-8", errors="replace")
        lines = [ln for ln in full_log.splitlines() if ln.strip()]
        tail = "\n".join(lines[-40:]) if lines else ""
        return rc, elapsed, tail, timed_out
    finally:
        try:
            log_path.unlink(missing_ok=True)
        except OSError:
            pass


def run_stage(
    triple: tuple[str, str, str],
    stage: str,
    cfg: Config,
    repeat_index: int | None,
    result_path: Path | None,
    scenario_selectors: list[str] | None,
) -> StageOutcome:
    commands, cwd, stage_env = build_stage_commands(triple, stage, cfg, result_path, scenario_selectors)
    if not commands:
        return StageOutcome(
            host=triple[0],
            guest=triple[1],
            mechanism=triple[2],
            stage=stage,
            repeat_index=repeat_index,
            status="SKIP",
            elapsed_seconds=0.0,
            command_display="(no-op)",
        )

    env = os.environ.copy()
    env.update(stage_env)
    # Ensure METAFFI_TEST_SCENARIOS is not inherited from parent process
    # unless explicitly set by the runner (scenario_mode).
    if "METAFFI_TEST_SCENARIOS" not in stage_env:
        env.pop("METAFFI_TEST_SCENARIOS", None)

    command_display = format_command_display(commands, cwd, stage_env)
    timeout = timeout_for(triple, cfg)

    total_elapsed = 0.0
    multi_phase = len(commands) > 1
    for phase_i, cmd in enumerate(commands, start=1):
        label = f"{triple_label(triple)} stage={stage}"
        if repeat_index is not None:
            label += f" repeat={repeat_index}"
        if multi_phase:
            label += f" phase={phase_i}/{len(commands)}"
        attempt = 1
        while True:
            rc, elapsed, tail, timed_out = run_command_with_heartbeat(
                cmd=cmd,
                cwd=cwd,
                env=env,
                timeout_seconds=timeout,
                heartbeat_seconds=cfg.heartbeat_seconds,
                heartbeat_label=label if attempt == 1 else f"{label} retry={attempt}",
            )
            total_elapsed += elapsed

            if timed_out:
                return StageOutcome(
                    host=triple[0],
                    guest=triple[1],
                    mechanism=triple[2],
                    stage=stage,
                    repeat_index=repeat_index,
                    status="FAIL",
                    elapsed_seconds=total_elapsed,
                    command_display=command_display,
                    error_message=(
                        f"TIMEOUT after {timeout}s at command phase {phase_i}\n{tail}"
                        if multi_phase
                        else f"TIMEOUT after {timeout}s\n{tail}"
                    ),
                )

            if rc == 0:
                break

            if attempt == 1 and should_retry_transient_failure(triple, stage, tail):
                print(f"        RETRY transient failure: {label}")
                time.sleep(1.0)
                attempt += 1
                continue

            return StageOutcome(
                host=triple[0],
                guest=triple[1],
                mechanism=triple[2],
                stage=stage,
                repeat_index=repeat_index,
                status="FAIL",
                elapsed_seconds=total_elapsed,
                command_display=command_display,
                error_message=(
                    f"Exit code {rc} at command phase {phase_i}\n{tail}"
                    if multi_phase
                    else f"Exit code {rc}\n{tail}"
                ),
            )

    if stage == "benchmark" and result_path is not None and not result_path.is_file():
        return StageOutcome(
            host=triple[0],
            guest=triple[1],
            mechanism=triple[2],
            stage=stage,
            repeat_index=repeat_index,
            status="FAIL",
            elapsed_seconds=total_elapsed,
            command_display=command_display,
            error_message=f"No result file produced: {result_path}",
        )

    return StageOutcome(
        host=triple[0],
        guest=triple[1],
        mechanism=triple[2],
        stage=stage,
        repeat_index=repeat_index,
        status="PASS",
        elapsed_seconds=total_elapsed,
        command_display=command_display,
    )

def percentile_from_sorted(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    idx = min(int(len(values) * q), len(values) - 1)
    return float(values[idx])


def remove_outliers_iqr(values: list[float]) -> list[float]:
    if len(values) < 4:
        return values
    s = sorted(values)
    n = len(s)
    q1 = s[n // 4]
    q3 = s[(3 * n) // 4]
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    cleaned = [x for x in s if low <= x <= high]
    return cleaned if cleaned else s


def compute_stats(values: list[float]) -> dict[str, float | list[float]]:
    if not values:
        return {
            "mean_ns": 0.0,
            "median_ns": 0.0,
            "p95_ns": 0.0,
            "p99_ns": 0.0,
            "stddev_ns": 0.0,
            "ci95_ns": [0.0, 0.0],
        }

    s = sorted(values)
    n = len(s)
    mean = sum(s) / n
    if n % 2 == 1:
        median = s[n // 2]
    else:
        median = (s[n // 2 - 1] + s[n // 2]) / 2.0
    p95 = percentile_from_sorted(s, 0.95)
    p99 = percentile_from_sorted(s, 0.99)

    var = sum((x - mean) ** 2 for x in s) / n
    stddev = math.sqrt(var)
    se = stddev / math.sqrt(n)
    return {
        "mean_ns": mean,
        "median_ns": median,
        "p95_ns": p95,
        "p99_ns": p99,
        "stddev_ns": stddev,
        "ci95_ns": [mean - 1.96 * se, mean + 1.96 * se],
    }


def scenario_key(bench: dict[str, Any]) -> tuple[str, int | None]:
    scenario = bench.get("scenario")
    if not isinstance(scenario, str):
        raise RunnerError(f"Malformed benchmark scenario entry: {bench}")
    data_size = bench.get("data_size")
    if data_size is not None and not isinstance(data_size, int):
        raise RunnerError(f"Invalid data_size in benchmark '{scenario}': {data_size}")
    return scenario, data_size


def scenario_selector_to_key(selector: str) -> tuple[str, int | None]:
    sel = selector.strip()
    if not sel:
        raise RunnerError("Empty scenario selector is not allowed")

    # Allow exact scenario names (void_call, primitive_echo, ...)
    # and size-suffixed selectors (array_sum_10000, array_echo_10000).
    m = re.match(r"^(.+)_([0-9]+)$", sel)
    if not m:
        return sel, None

    scenario_name = m.group(1)
    try:
        data_size = int(m.group(2))
    except ValueError as e:
        raise RunnerError(f"Invalid scenario selector '{selector}'") from e
    return scenario_name, data_size


def scenario_key_to_selector(key: tuple[str, int | None]) -> str:
    scenario_name, data_size = key
    if data_size is None:
        return scenario_name
    return f"{scenario_name}_{data_size}"


def parse_scenario_selectors(raw_selectors: list[str] | None) -> list[tuple[str, int | None]]:
    if not raw_selectors:
        return []

    expanded: list[str] = []
    for raw in raw_selectors:
        if raw is None:
            continue
        parts = [p.strip() for p in str(raw).split(",")]
        expanded.extend([p for p in parts if p])

    seen: set[tuple[str, int | None]] = set()
    parsed: list[tuple[str, int | None]] = []
    for s in expanded:
        key = scenario_selector_to_key(s)
        if key not in seen:
            seen.add(key)
            parsed.append(key)
    return parsed


def merge_selected_benchmarks(
    canonical_file: Path,
    rerun_data: dict[str, Any],
    selected_keys: set[tuple[str, int | None]],
    run_id: str,
) -> None:
    if not canonical_file.is_file():
        raise RunnerError(
            f"Scenario-rerun requires existing canonical result file, missing: {canonical_file}"
        )

    try:
        current = json.loads(canonical_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RunnerError(f"Malformed canonical JSON in {canonical_file}: {e}") from e

    cur_bench = current.get("benchmarks")
    new_bench = rerun_data.get("benchmarks")
    if not isinstance(cur_bench, list):
        raise RunnerError(f"Canonical file has invalid benchmarks section: {canonical_file}")
    if not isinstance(new_bench, list):
        raise RunnerError("Scenario rerun aggregation produced invalid benchmarks section")

    current_by_key: dict[tuple[str, int | None], dict[str, Any]] = {}
    for b in cur_bench:
        current_by_key[scenario_key(b)] = b

    rerun_by_key: dict[tuple[str, int | None], dict[str, Any]] = {}
    for b in new_bench:
        rerun_by_key[scenario_key(b)] = b

    applicable_keys = {
        k for k in selected_keys if (k in current_by_key) or (k in rerun_by_key)
    }

    missing_in_rerun = [k for k in applicable_keys if k not in rerun_by_key]
    if missing_in_rerun:
        missing_s = ", ".join(sorted(scenario_key_to_selector(k) for k in missing_in_rerun))
        raise RunnerError(
            "Scenario-rerun output missing requested scenario(s): "
            f"{missing_s}. Ensure benchmark harness supports METAFFI_TEST_SCENARIOS."
        )

    merged: list[dict[str, Any]] = []
    replaced_or_kept: set[tuple[str, int | None]] = set()
    for b in cur_bench:
        k = scenario_key(b)
        if k in applicable_keys:
            merged.append(rerun_by_key[k])
            replaced_or_kept.add(k)
        else:
            merged.append(b)

    # Allow scenario-rerun mode to introduce new scenarios that are not yet present
    # in canonical files (e.g., newly added benchmark scenario keys).
    for k in sorted(applicable_keys, key=lambda x: (x[0], x[1] if x[1] is not None else -1)):
        if k in replaced_or_kept:
            continue
        merged.append(rerun_by_key[k])
    current["benchmarks"] = merged

    if not isinstance(current.get("metadata"), dict):
        current["metadata"] = {}
    if not isinstance(current["metadata"].get("config"), dict):
        current["metadata"]["config"] = {}

    current["metadata"]["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    current["metadata"]["config"]["last_partial_run_id"] = run_id
    current["metadata"]["config"]["last_partial_scenarios"] = sorted(
        scenario_key_to_selector(k) for k in applicable_keys
    )
    with open(canonical_file, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)


def build_aggregated_result(
    triple: tuple[str, str, str],
    repeat_files: list[Path],
    cfg: Config,
    run_id: str,
    config_stem: str,
) -> dict[str, Any]:
    if not repeat_files:
        raise RunnerError(f"No repeat files found for {triple_label(triple)}")

    loaded: list[dict[str, Any]] = []
    for p in repeat_files:
        if not p.is_file():
            raise RunnerError(f"Missing repeat file for {triple_label(triple)}: {p}")
        try:
            loaded.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            raise RunnerError(f"Malformed JSON in repeat file {p}: {e}") from e

    base = copy.deepcopy(loaded[0])
    if "benchmarks" not in base or not isinstance(base["benchmarks"], list):
        raise RunnerError(f"Repeat file missing benchmarks array: {repeat_files[0]}")

    by_run: list[dict[tuple[str, int | None], dict[str, Any]]] = []
    for i, data in enumerate(loaded, start=1):
        benches = data.get("benchmarks")
        if not isinstance(benches, list):
            raise RunnerError(f"Repeat #{i} has invalid benchmarks section")
        m: dict[tuple[str, int | None], dict[str, Any]] = {}
        for b in benches:
            key = scenario_key(b)
            if key in m:
                raise RunnerError(f"Duplicate scenario in repeat #{i} for {triple_label(triple)}: {key}")
            m[key] = b
        by_run.append(m)

    # Allow partial repeats: use intersection so we can aggregate when some runs
    # crashed late (e.g. any_echo handle-table overflow) and have fewer scenarios.
    keys_all = set(by_run[0].keys())
    for m in by_run[1:]:
        keys_all |= set(m.keys())
    keys_common = set(by_run[0].keys())
    for m in by_run[1:]:
        keys_common &= set(m.keys())
    if keys_common != keys_all and keys_all:
        missing = keys_all - keys_common
        print(
            f"  WARN  {triple_label(triple)}: scenario set differs across repeats; "
            f"aggregating {len(keys_common)} common, {len(missing)} missing in some runs"
        )

    aggregated_benchmarks: list[dict[str, Any]] = []
    for key in sorted(keys_all, key=lambda x: (x[0], x[1] if x[1] is not None else -1)):
        scenario_name, data_size = key
        repeat_means: list[float] = []
        pooled_per_call: list[float] = []
        errors: list[str] = []

        if key not in keys_common:
            missing_runs = [i for i, m in enumerate(by_run, start=1) if key not in m]
            aggregated_benchmarks.append(
                {
                    "scenario": scenario_name,
                    "data_size": data_size,
                    "status": "FAIL",
                    "error": f"missing in run(s) {missing_runs}",
                    "raw_iterations_ns": [],
                    "phases": {},
                    "repeat_analysis": {
                        "repeat_count": len(repeat_files),
                        "repeat_means_ns": [],
                        "global_mean_ns": None,
                        "aggregation_method": "pooled_iterations",
                    },
                }
            )
            continue

        for i, m in enumerate(by_run, start=1):
            b = m[key]
            status = b.get("status")
            if status != "PASS":
                errors.append(f"run_{i}: status={status}")
                continue

            phases = b.get("phases")
            if not isinstance(phases, dict) or "total" not in phases or not isinstance(phases["total"], dict):
                raise RunnerError(f"Missing phases.total in {triple_label(triple)} scenario {key} run_{i}")

            total_phase = phases["total"]
            if "mean_ns" not in total_phase:
                raise RunnerError(f"Missing phases.total.mean_ns in {triple_label(triple)} scenario {key} run_{i}")
            repeat_means.append(float(total_phase["mean_ns"]))

            raw = b.get("raw_iterations_ns")
            if not isinstance(raw, list):
                raise RunnerError(f"raw_iterations_ns must be a list in {triple_label(triple)} scenario {key} run_{i}")

            for v in raw:
                pooled_per_call.append(float(v))

        if errors:
            aggregated_benchmarks.append(
                {
                    "scenario": scenario_name,
                    "data_size": data_size,
                    "status": "FAIL",
                    "error": "; ".join(errors),
                    "raw_iterations_ns": [],
                    "phases": {},
                    "repeat_analysis": {
                        "repeat_count": len(repeat_files),
                        "repeat_means_ns": repeat_means,
                        "global_mean_ns": None,
                        "aggregation_method": "pooled_iterations",
                    },
                }
            )
            continue

        cleaned = remove_outliers_iqr(pooled_per_call)
        stats = compute_stats(cleaned)
        aggregated_benchmarks.append(
            {
                "scenario": scenario_name,
                "data_size": data_size,
                "status": "PASS",
                "raw_iterations_ns": pooled_per_call,
                "phases": {"total": stats},
                "repeat_analysis": {
                    "repeat_count": len(repeat_files),
                    "repeat_means_ns": repeat_means,
                    "global_mean_ns": stats["mean_ns"],
                    "pooled_sample_count": len(pooled_per_call),
                    "aggregation_method": "pooled_iterations",
                },
            }
        )

    base["benchmarks"] = aggregated_benchmarks

    if not isinstance(base.get("metadata"), dict):
        base["metadata"] = {}
    if not isinstance(base["metadata"].get("config"), dict):
        base["metadata"]["config"] = {}

    base["metadata"]["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    base["metadata"]["config"]["warmup_iterations"] = cfg.warmup_iterations
    base["metadata"]["config"]["measured_iterations"] = cfg.measured_iterations
    base["metadata"]["config"]["repeat_count"] = len(repeat_files)
    base["metadata"]["config"]["batch_min_elapsed_ns"] = cfg.batch_min_elapsed_ns
    base["metadata"]["config"]["batch_max_calls"] = cfg.batch_max_calls
    base["metadata"]["config"]["aggregation_method"] = "pooled_iterations"
    base["metadata"]["config"]["run_id"] = run_id
    base["metadata"]["config"]["run_config_name"] = config_stem
    return base


def aggregate_repeat_files(
    triple: tuple[str, str, str],
    repeat_files: list[Path],
    canonical_file: Path,
    cfg: Config,
    run_id: str,
    config_stem: str,
) -> None:
    base = build_aggregated_result(triple, repeat_files, cfg, run_id, config_stem)
    canonical_file.parent.mkdir(parents=True, exist_ok=True)
    with open(canonical_file, "w", encoding="utf-8") as f:
        json.dump(base, f, indent=2)


def print_outcome(prefix: str, outcome: StageOutcome) -> None:
    def safe_stdout(text: str) -> str:
        enc = sys.stdout.encoding or "utf-8"
        return text.encode(enc, errors="replace").decode(enc, errors="replace")

    label = f"{outcome.host}->{outcome.guest} [{outcome.mechanism}]"
    rep = f" repeat={outcome.repeat_index}" if outcome.repeat_index is not None else ""
    print(safe_stdout(f"  {prefix:<5} {label} stage={outcome.stage}{rep} ({outcome.elapsed_seconds:.1f}s)"))
    if outcome.error_message:
        lines = outcome.error_message.splitlines()
        first_line = lines[0]
        print(safe_stdout(f"        Error: {first_line}"))
        if len(lines) > 1:
            print(safe_stdout("        Output tail:"))
            for ln in lines[1:]:
                print(safe_stdout(f"          {ln}"))


def run_script(script: Path, cwd: Path) -> None:
    if not script.is_file():
        raise RunnerError(f"Required script not found: {script}")
    proc = subprocess.run([sys.executable, str(script)], cwd=str(cwd), check=False)
    if proc.returncode != 0:
        raise RunnerError(f"Script failed ({proc.returncode}): {script}")


def clear_config_artifacts(config_path: Path) -> None:
    cfg = load_config(config_path.resolve())
    triples = filter_triples(cfg)
    config_stem = sanitize_path_component(config_path.stem)

    state_file = resume_state_path(cfg.repeat_root_dir, config_stem)
    removed_state = 0
    if state_file.is_file():
        state_file.unlink()
        removed_state = 1

    removed_repeat_dirs = 0
    if cfg.repeat_root_dir.is_dir():
        for d in cfg.repeat_root_dir.glob(f"*__{config_stem}"):
            if d.is_dir():
                shutil.rmtree(d)
                removed_repeat_dirs += 1

    removed_canonical = 0
    for triple in triples:
        f = cfg.canonical_results_dir / result_filename(triple)
        if f.is_file():
            f.unlink()
            removed_canonical += 1

    print("Cleared config artifacts:")
    print(f"  Config: {config_path.resolve()}")
    print(f"  State files removed: {removed_state}")
    print(f"  Repeat session directories removed: {removed_repeat_dirs}")
    print(f"  Canonical result files removed: {removed_canonical}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MetaFFI tests using strict YAML config")
    parser.add_argument("--config", help="Path to YAML config file")
    parser.add_argument(
        "--clear-config",
        dest="clear_config",
        help="Path to YAML config file whose cached run state/results should be cleared",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help=(
            "Benchmark scenario selector(s) to rerun and merge into canonical results only for those "
            "scenarios. Examples: void_call, array_sum_10000, array_echo_10000. "
            "Can be repeated or comma-separated."
        ),
    )
    args = parser.parse_args()

    if args.clear_config:
        if args.config:
            raise ConfigError("Use either --config or --clear-config, not both")
        clear_config_artifacts(Path(args.clear_config))
        return 0

    if not args.config:
        raise ConfigError("--config is required unless --clear-config is used")

    config_path = Path(args.config).resolve()
    cfg = load_config(config_path)
    triples = filter_triples(cfg)
    selected_scenario_keys = parse_scenario_selectors(args.scenarios)
    selected_scenario_selectors = [scenario_key_to_selector(k) for k in selected_scenario_keys]
    selected_scenario_key_set = set(selected_scenario_keys)
    scenario_mode = len(selected_scenario_keys) > 0

    if scenario_mode and not cfg.include_benchmarks:
        raise ConfigError("--scenario requires run.include_benchmarks=true in config")
    if scenario_mode and cfg.include_correctness:
        raise ConfigError("--scenario cannot be combined with run.include_correctness=true")

    cfg.canonical_results_dir.mkdir(parents=True, exist_ok=True)
    config_stem = sanitize_path_component(config_path.stem)
    cfg_sha = config_sha256(config_path)
    state_file = resume_state_path(cfg.repeat_root_dir, config_stem)
    resume_state = load_resume_state(state_file, cfg_sha, config_path)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{run_stamp}__{config_stem}"
    repeat_session_dir = cfg.repeat_root_dir / run_id

    print("=== MetaFFI Config Runner ===")
    print(f"Config: {config_path}")
    print(f"Triples selected: {len(triples)}")
    print(f"Benchmarks: {cfg.include_benchmarks} | Correctness: {cfg.include_correctness}")
    print(f"Repeats: {cfg.repeats} | Warmup: {cfg.warmup_iterations} | Iterations: {cfg.measured_iterations}")
    print(f"Batching: min_elapsed_ns={cfg.batch_min_elapsed_ns}, max_calls={cfg.batch_max_calls}")
    print(f"Fail-fast: {cfg.fail_fast}")
    if scenario_mode:
        print(f"Scenario rerun mode: {', '.join(selected_scenario_selectors)}")
    print(f"Run ID: {run_id}")
    print(f"Resume state: {state_file}")
    print()

    outcomes: list[StageOutcome] = []
    start_all = time.monotonic()

    benchmark_targets: list[tuple[str, str, str]] = []
    if cfg.include_benchmarks:
        for triple in triples:
            if scenario_mode:
                benchmark_targets.append(triple)
                continue

            canonical_file = cfg.canonical_results_dir / result_filename(triple)
            if not cfg.rerun_existing and canonical_file.is_file():
                out = StageOutcome(
                    host=triple[0],
                    guest=triple[1],
                    mechanism=triple[2],
                    stage="benchmark",
                    repeat_index=None,
                    status="SKIP",
                    elapsed_seconds=0.0,
                    command_display="(existing canonical result)",
                )
                outcomes.append(out)
                print_outcome("SKIP", out)
            else:
                benchmark_targets.append(triple)

    if cfg.include_correctness:
        print("-- Correctness Stage --")
        for idx, triple in enumerate(triples, start=1):
            ckey = triple_key(triple)
            if resume_state["correctness"].get(ckey) is True:
                out = StageOutcome(
                    host=triple[0],
                    guest=triple[1],
                    mechanism=triple[2],
                    stage="correctness",
                    repeat_index=None,
                    status="SKIP",
                    elapsed_seconds=0.0,
                    command_display="(resume: already passed for this config)",
                )
                outcomes.append(out)
                print_outcome("SKIP", out)
                continue

            print(f"  RUN   [{idx}/{len(triples)}] {triple_label(triple)} stage=correctness")
            out = run_stage(
                triple,
                "correctness",
                cfg,
                repeat_index=None,
                result_path=None,
                scenario_selectors=None,
            )
            outcomes.append(out)
            print_outcome(out.status, out)
            if out.status == "PASS":
                resume_state["correctness"][ckey] = True
                save_resume_state(state_file, resume_state)
            if out.status == "FAIL" and cfg.fail_fast:
                raise RunnerError("Fail-fast: correctness stage failed")
        print()

    repeat_files_by_triple: dict[tuple[str, str, str], list[Path]] = {t: [] for t in benchmark_targets}
    resume_benchmarks = cfg.write_repeat_files and not scenario_mode
    if cfg.include_benchmarks and not resume_benchmarks and benchmark_targets:
        reason = (
            "outputs.write_repeat_files=false"
            if not cfg.write_repeat_files
            else "scenario rerun mode requires fresh benchmark execution"
        )
        print(f"NOTE: Benchmark resume skipping disabled because {reason}")

    if cfg.include_benchmarks:
        if cfg.write_repeat_files:
            repeat_session_dir.mkdir(parents=True, exist_ok=True)

        print("-- Benchmark Stage --")
        total_runs = len(benchmark_targets) * cfg.repeats
        run_counter = 0

        for rep in range(1, cfg.repeats + 1):
            print(f"  Repeat {rep}/{cfg.repeats}")
            run_dir = repeat_session_dir / f"run_{rep:02d}"
            if cfg.write_repeat_files:
                run_dir.mkdir(parents=True, exist_ok=True)

            for triple in benchmark_targets:
                run_counter += 1
                repeat_file = run_dir / result_filename(triple)
                bkey = triple_key(triple)
                rep_key = str(rep)

                if resume_benchmarks:
                    bstate = resume_state["benchmarks"].get(bkey)
                    if bstate is not None and not isinstance(bstate, dict):
                        raise RunnerError(f"Malformed resume benchmark entry for {triple_label(triple)}")

                    prev_path_s = bstate.get(rep_key) if isinstance(bstate, dict) else None
                    if isinstance(prev_path_s, str):
                        prev_path = Path(prev_path_s)
                        if prev_path.is_file():
                            out = StageOutcome(
                                host=triple[0],
                                guest=triple[1],
                                mechanism=triple[2],
                                stage="benchmark",
                                repeat_index=rep,
                                status="SKIP",
                                elapsed_seconds=0.0,
                                command_display="(resume: already passed for this config)",
                            )
                            outcomes.append(out)
                            repeat_files_by_triple[triple].append(prev_path)
                            print_outcome("SKIP", out)
                            continue
                        # stale path in state: force re-run this repeat
                        bstate.pop(rep_key, None)
                        save_resume_state(state_file, resume_state)

                print(f"    RUN   [{run_counter}/{total_runs}] {triple_label(triple)} stage=benchmark repeat={rep}")

                out = run_stage(
                    triple,
                    "benchmark",
                    cfg,
                    repeat_index=rep,
                    result_path=repeat_file,
                    scenario_selectors=selected_scenario_selectors if scenario_mode else None,
                )
                outcomes.append(out)
                print_outcome(out.status, out)

                if out.status == "PASS":
                    repeat_files_by_triple[triple].append(repeat_file)
                    if resume_benchmarks:
                        bstate = resume_state["benchmarks"].setdefault(bkey, {})
                        if not isinstance(bstate, dict):
                            raise RunnerError(f"Malformed resume benchmark entry for {triple_label(triple)}")
                        bstate[rep_key] = str(repeat_file.resolve())
                        save_resume_state(state_file, resume_state)
                elif repeat_file.is_file() and repeat_file.stat().st_size > 0:
                    # Process failed but incremental saving produced partial results.
                    # Include the file so aggregation can use whatever scenarios completed.
                    # Do NOT trigger fail-fast here: the tail crash (e.g. any_echo
                    # handle-table overflow) happened after all critical scenarios
                    # were already saved.  Aggregation will flag any missing data.
                    repeat_files_by_triple[triple].append(repeat_file)
                    print(f"        (partial results salvaged from {repeat_file.name})")
                elif cfg.fail_fast:
                    raise RunnerError("Fail-fast: benchmark stage failed")

            print()

        print("-- Aggregation Stage (pooled iterations across repeats) --")
        for i, triple in enumerate(benchmark_targets, start=1):
            files = repeat_files_by_triple[triple]
            if len(files) == 0:
                msg = f"No repeat files for {triple_label(triple)}"
                if cfg.fail_fast:
                    raise RunnerError(msg)
                print(f"  FAIL  {msg}")
                continue
            if len(files) < cfg.repeats:
                print(
                    f"  WARN  {triple_label(triple)}: {len(files)}/{cfg.repeats} repeats "
                    f"(using available data)"
                )

            canonical_file = cfg.canonical_results_dir / result_filename(triple)
            if scenario_mode:
                print(
                    "  AGGR  "
                    f"[{i}/{len(benchmark_targets)}] {triple_label(triple)} "
                    f"(update scenarios: {', '.join(selected_scenario_selectors)}) -> {canonical_file.name}"
                )
                rerun_data = build_aggregated_result(triple, files, cfg, run_id, config_stem)
                merge_selected_benchmarks(canonical_file, rerun_data, selected_scenario_key_set, run_id)
            else:
                print(f"  AGGR  [{i}/{len(benchmark_targets)}] {triple_label(triple)} -> {canonical_file.name}")
                aggregate_repeat_files(triple, files, canonical_file, cfg, run_id, config_stem)

    if cfg.run_complexity:
        print("\n-- Complexity Analysis --")
        run_script(TESTS_ROOT / "analyze_complexity.py", TESTS_ROOT)

    if cfg.run_consolidation:
        print("\n-- Consolidation/Tables/Report --")
        run_script(TESTS_ROOT / "consolidate_results.py", TESTS_ROOT)
    else:
        if cfg.run_tables:
            print("\n-- Tables --")
            run_script(TESTS_ROOT / "generate_tables.py", TESTS_ROOT)
        if cfg.run_report:
            print("\n-- Report --")
            run_script(TESTS_ROOT / "generate_report.py", TESTS_ROOT)

    elapsed_all = time.monotonic() - start_all
    passed = sum(1 for o in outcomes if o.status == "PASS")
    failed = sum(1 for o in outcomes if o.status == "FAIL")
    skipped = sum(1 for o in outcomes if o.status == "SKIP")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Outcomes: total={len(outcomes)} pass={passed} fail={failed} skip={skipped}")
    print(f"  Elapsed: {elapsed_all:.1f}s")
    if cfg.write_repeat_files:
        print(f"  Repeat files: {repeat_session_dir}")
    print(f"  Canonical results: {cfg.canonical_results_dir}")

    if failed > 0:
        print("\nFAILED OUTCOMES:")
        for o in outcomes:
            if o.status != "FAIL":
                continue
            label = f"{o.host}->{o.guest} [{o.mechanism}] stage={o.stage}"
            if o.repeat_index is not None:
                label += f" repeat={o.repeat_index}"
            print(f"  {label}")
            if o.error_message:
                print(f"    Error: {o.error_message.splitlines()[0]}")
            print(f"    Command: {o.command_display}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ConfigError, RunnerError) as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)
