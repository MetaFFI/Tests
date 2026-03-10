"""Correctness tests: Python3 -> C via MetaFFI

Tests C guest module entities accessible through MetaFFI.
Fail-fast: every assertion is exact (or epsilon-justified for floats).
"""

import pytest
import metaffi

T = metaffi.MetaFFITypes
ti = metaffi.metaffi_type_info


# ============================================================================
# Core functions (C guest)
# ============================================================================

class TestCoreFunctions:

    def test_no_op(self, c_module):
        fn = c_module.load_entity("callable=xcall_c_no_op", None, None)
        fn()
        del fn

    def test_hello_world(self, c_module):
        fn = c_module.load_entity("callable=xcall_c_hello_world", None,
            [ti(T.metaffi_string8_type)])
        result = fn()
        assert result == "Hello World from C"
        del fn

    def test_returns_an_error(self, c_module):
        """C guest returns int32 (-1) instead of throwing."""
        fn = c_module.load_entity("callable=xcall_c_returns_an_error", None,
            [ti(T.metaffi_int32_type)])
        result = fn()
        assert result == -1, f"returns_an_error: got {result}, want -1"
        del fn

    def test_div_integers(self, c_module):
        fn = c_module.load_entity("callable=xcall_c_div_integers",
            [ti(T.metaffi_int64_type), ti(T.metaffi_int64_type)],
            [ti(T.metaffi_float64_type)])
        result = fn(10, 2)
        assert abs(result - 5.0) < 1e-10, f"div_integers(10,2) = {result}, want 5.0"
        del fn


# ============================================================================
# State: counter
# ============================================================================

class TestState:

    def test_counter_operations(self, c_module):
        """set_counter, get_counter, inc_counter round-trip."""
        get_fn = c_module.load_entity("callable=xcall_c_get_counter", None,
            [ti(T.metaffi_int64_type)])
        set_fn = c_module.load_entity("callable=xcall_c_set_counter",
            [ti(T.metaffi_int64_type)], None)
        inc_fn = c_module.load_entity("callable=xcall_c_inc_counter",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_int64_type)])

        # Reset counter to 0
        set_fn(0)
        assert get_fn() == 0

        # Increment by 5
        new_val = inc_fn(5)
        assert new_val == 5, f"inc_counter(5) = {new_val}, want 5"
        assert get_fn() == 5

        # Reset
        set_fn(0)
        assert get_fn() == 0

        del get_fn, set_fn, inc_fn
