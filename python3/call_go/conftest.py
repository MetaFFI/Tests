"""Shared pytest fixtures for Python3 -> Go MetaFFI tests.

Provides session-scoped fixtures for the MetaFFI Go runtime and module,
used by both correctness and benchmark tests.
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

# Go runtime plugin requires the compiled DLL path (not the source directory)
GO_GUEST_MODULE_PATH = os.path.join(
    METAFFI_SOURCE_ROOT, "sdk", "test_modules", "guest_modules", "go",
    "test_bin", "guest_MetaFFIGuest.dll"
)

if not os.path.isfile(GO_GUEST_MODULE_PATH):
    raise RuntimeError(
        f"Go guest module DLL not found: {GO_GUEST_MODULE_PATH}\n"
        "Build it first: cmake --build ... (see sdk/test_modules/guest_modules/go/CMakeLists.txt)"
    )


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
def go_runtime():
    """Initialize the MetaFFI Go runtime plugin. Released at session end."""
    rt = metaffi.MetaFFIRuntime("go")

    start = time.perf_counter_ns()
    rt.load_runtime_plugin()
    init_timing["load_runtime_plugin_ns"] = time.perf_counter_ns() - start

    yield rt
    rt.release_runtime_plugin()


@pytest.fixture(scope="session")
def go_module(go_runtime):
    """Load the Go guest module via MetaFFI."""
    start = time.perf_counter_ns()
    mod = go_runtime.load_module(GO_GUEST_MODULE_PATH)
    init_timing["load_module_ns"] = time.perf_counter_ns() - start

    yield mod
