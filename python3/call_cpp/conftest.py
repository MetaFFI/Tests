"""Shared pytest fixtures for Python3 -> C++ MetaFFI tests.

Provides session-scoped fixtures for the MetaFFI C++ runtime and module,
used by correctness tests.
"""

import os
import sys
import time

# --- Ensure metaffi SDK is on the Python path ---
METAFFI_SOURCE_ROOT = os.environ.get("METAFFI_SOURCE_ROOT")
if not METAFFI_SOURCE_ROOT:
    raise RuntimeError(
        "METAFFI_SOURCE_ROOT environment variable not set. "
        "Set it to the MetaFFI repository root (e.g., c:\\src\\github.com\\MetaFFI)"
    )

_sdk_python_path = os.path.join(METAFFI_SOURCE_ROOT, "sdk", "api", "python3")
if _sdk_python_path not in sys.path:
    sys.path.insert(0, _sdk_python_path)

import pytest
import metaffi


def _guest_module_filename() -> str:
    if sys.platform.startswith("win"):
        return "cpp_guest_module.dll"
    if sys.platform == "darwin":
        return "cpp_guest_module.dylib"
    return "cpp_guest_module.so"


# C++ guest module path
CPP_GUEST_MODULE_PATH = os.path.join(
    METAFFI_SOURCE_ROOT, "sdk", "test_modules", "guest_modules", "cpp",
    "test_bin", _guest_module_filename()
)

if not os.path.isfile(CPP_GUEST_MODULE_PATH):
    raise RuntimeError(
        f"C++ guest module library not found: {CPP_GUEST_MODULE_PATH}\n"
        "Build it first: cmake --build ... --target cpp_guest_module"
    )
print(f"+++ call_cpp fixture: resolved CPP_GUEST_MODULE_PATH={CPP_GUEST_MODULE_PATH}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Timing storage (populated by fixtures, read by benchmarks)
# ---------------------------------------------------------------------------

init_timing = {
    "load_runtime_plugin_ns": 0,
    "load_module_ns": 0,
}


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def cpp_runtime():
    """Initialize the MetaFFI C++ runtime plugin. Released at session end."""
    print("+++ call_cpp fixture: cpp_runtime create start", file=sys.stderr, flush=True)
    rt = metaffi.MetaFFIRuntime("cpp")

    start = time.perf_counter_ns()
    rt.load_runtime_plugin()
    init_timing["load_runtime_plugin_ns"] = time.perf_counter_ns() - start

    yield rt
    rt.release_runtime_plugin()


@pytest.fixture(scope="session")
def cpp_module(cpp_runtime):
    """Load the C++ guest module via MetaFFI."""
    start = time.perf_counter_ns()
    mod = cpp_runtime.load_module(CPP_GUEST_MODULE_PATH)
    init_timing["load_module_ns"] = time.perf_counter_ns() - start

    yield mod
