"""Shared pytest fixtures for Python3 -> Java MetaFFI tests.

Provides session-scoped fixtures for the MetaFFI OpenJDK runtime and module,
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

# Java guest module JAR path
JAVA_GUEST_JAR_PATH = os.path.join(
    METAFFI_SOURCE_ROOT, "sdk", "test_modules", "guest_modules", "java",
    "test_bin", "guest_java.jar"
)

if not os.path.isfile(JAVA_GUEST_JAR_PATH):
    raise RuntimeError(
        f"Java guest JAR not found: {JAVA_GUEST_JAR_PATH}\n"
        "Build it first: cmake --build ... (see sdk/test_modules/guest_modules/java/CMakeLists.txt)"
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
def java_runtime():
    """Initialize the MetaFFI OpenJDK runtime plugin. Released at session end."""
    rt = metaffi.MetaFFIRuntime("jvm")

    start = time.perf_counter_ns()
    rt.load_runtime_plugin()
    init_timing["load_runtime_plugin_ns"] = time.perf_counter_ns() - start

    yield rt
    rt.release_runtime_plugin()


@pytest.fixture(scope="session")
def java_module(java_runtime):
    """Load the Java guest module via MetaFFI."""
    start = time.perf_counter_ns()
    mod = java_runtime.load_module(JAVA_GUEST_JAR_PATH)
    init_timing["load_module_ns"] = time.perf_counter_ns() - start

    yield mod
    mod = None
