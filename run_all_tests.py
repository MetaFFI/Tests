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
import json
import math
import os
import re
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
        test_class = "TestBenchmark#testAllBenchmarks" if mechanism == "metaffi" else "BenchmarkTest#testAllBenchmarks"

        if mechanism == "jep":
            jep_home = _find_jep_home()
            if jep_home:
                env["JEP_HOME"] = jep_home

        return [[mvn, "test", f"-Dtest={test_class}", "-pl", "."]], cwd, env

    raise RunnerError(f"Unsupported host: {host}")


def timeout_for(triple: tuple[str, str, str], cfg: Config) -> int:
    host, _, mechanism = triple
    if host == "java" and mechanism == "metaffi":
        return cfg.java_metaffi_timeout_seconds
    return cfg.default_timeout_seconds


def format_command_display(commands: list[list[str]], cwd: Path, env: dict[str, str]) -> str:
    env_keys = [
        "METAFFI_TEST_RESULTS_FILE",
        "METAFFI_TEST_ITERATIONS",
        "METAFFI_TEST_WARMUP",
        "METAFFI_TEST_BATCH_MIN_ELAPSED_NS",
        "METAFFI_TEST_BATCH_MAX_CALLS",
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
) -> StageOutcome:
    commands, cwd, stage_env = build_stage_commands(triple, stage, cfg, result_path)
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

    command_display = format_command_display(commands, cwd, stage_env)
    timeout = timeout_for(triple, cfg)

    total_elapsed = 0.0
    for phase_i, cmd in enumerate(commands, start=1):
        label = f"{triple_label(triple)} stage={stage}"
        if repeat_index is not None:
            label += f" repeat={repeat_index}"
        label += f" phase={phase_i}/{len(commands)}"

        rc, elapsed, tail, timed_out = run_command_with_heartbeat(
            cmd=cmd,
            cwd=cwd,
            env=env,
            timeout_seconds=timeout,
            heartbeat_seconds=cfg.heartbeat_seconds,
            heartbeat_label=label,
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
                error_message=f"TIMEOUT after {timeout}s at command phase {phase_i}\n{tail}",
            )

        if rc != 0:
            return StageOutcome(
                host=triple[0],
                guest=triple[1],
                mechanism=triple[2],
                stage=stage,
                repeat_index=repeat_index,
                status="FAIL",
                elapsed_seconds=total_elapsed,
                command_display=command_display,
                error_message=f"Exit code {rc} at command phase {phase_i}\n{tail}",
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


def aggregate_repeat_files(
    triple: tuple[str, str, str],
    repeat_files: list[Path],
    canonical_file: Path,
    cfg: Config,
    run_id: str,
    config_stem: str,
) -> None:
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

    keys0 = set(by_run[0].keys())
    for i, m in enumerate(by_run[1:], start=2):
        if set(m.keys()) != keys0:
            raise RunnerError(
                f"Scenario mismatch across repeats for {triple_label(triple)} between run#1 and run#{i}"
            )

    aggregated_benchmarks: list[dict[str, Any]] = []
    for key in sorted(keys0, key=lambda x: (x[0], x[1] if x[1] is not None else -1)):
        scenario_name, data_size = key
        repeat_means: list[float] = []
        pooled_per_call: list[float] = []
        errors: list[str] = []

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

    canonical_file.parent.mkdir(parents=True, exist_ok=True)
    canonical_file.write_text(json.dumps(base, indent=2), encoding="utf-8")


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MetaFFI tests using strict YAML config")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    args = parser.parse_args()

    cfg = load_config(Path(args.config).resolve())
    triples = filter_triples(cfg)

    cfg.canonical_results_dir.mkdir(parents=True, exist_ok=True)
    config_stem = sanitize_path_component(Path(args.config).stem)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{run_stamp}__{config_stem}"
    repeat_session_dir = cfg.repeat_root_dir / run_id

    print("=== MetaFFI Config Runner ===")
    print(f"Config: {Path(args.config).resolve()}")
    print(f"Triples selected: {len(triples)}")
    print(f"Benchmarks: {cfg.include_benchmarks} | Correctness: {cfg.include_correctness}")
    print(f"Repeats: {cfg.repeats} | Warmup: {cfg.warmup_iterations} | Iterations: {cfg.measured_iterations}")
    print(f"Batching: min_elapsed_ns={cfg.batch_min_elapsed_ns}, max_calls={cfg.batch_max_calls}")
    print(f"Fail-fast: {cfg.fail_fast}")
    print(f"Run ID: {run_id}")
    print()

    outcomes: list[StageOutcome] = []
    start_all = time.monotonic()

    benchmark_targets: list[tuple[str, str, str]] = []
    if cfg.include_benchmarks:
        for triple in triples:
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
            print(f"  RUN   [{idx}/{len(triples)}] {triple_label(triple)} stage=correctness")
            out = run_stage(triple, "correctness", cfg, repeat_index=None, result_path=None)
            outcomes.append(out)
            print_outcome(out.status, out)
            if out.status == "FAIL" and cfg.fail_fast:
                raise RunnerError("Fail-fast: correctness stage failed")
        print()

    repeat_files_by_triple: dict[tuple[str, str, str], list[Path]] = {t: [] for t in benchmark_targets}

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
                print(f"    RUN   [{run_counter}/{total_runs}] {triple_label(triple)} stage=benchmark repeat={rep}")
                repeat_file = run_dir / result_filename(triple)

                out = run_stage(triple, "benchmark", cfg, repeat_index=rep, result_path=repeat_file)
                outcomes.append(out)
                print_outcome(out.status, out)

                if out.status == "PASS":
                    repeat_files_by_triple[triple].append(repeat_file)
                elif cfg.fail_fast:
                    raise RunnerError("Fail-fast: benchmark stage failed")

            print()

        print("-- Aggregation Stage (pooled iterations across repeats) --")
        for i, triple in enumerate(benchmark_targets, start=1):
            files = repeat_files_by_triple[triple]
            if len(files) != cfg.repeats:
                msg = (
                    f"Expected {cfg.repeats} repeat files for {triple_label(triple)}, "
                    f"found {len(files)}"
                )
                if cfg.fail_fast:
                    raise RunnerError(msg)
                print(f"  FAIL  {msg}")
                continue

            canonical_file = cfg.canonical_results_dir / result_filename(triple)
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
