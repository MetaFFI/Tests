"""Correctness tests: Python3 -> Go via MetaFFI

Tests ALL Go guest module entities accessible through MetaFFI.
Fail-fast: every assertion is exact (or epsilon-justified for floats).
Any failure aborts immediately with a detailed error.
"""

import pytest
import metaffi

T = metaffi.MetaFFITypes
ti = metaffi.metaffi_type_info


# ============================================================================
# Core functions (core.go)
# ============================================================================

class TestCoreFunctions:

    def test_hello_world(self, go_module):
        fn = go_module.load_entity("callable=HelloWorld", None,
            [ti(T.metaffi_string8_type)])
        result = fn()
        assert result == "Hello World, from Go"
        del fn

    def test_div_integers(self, go_module):
        fn = go_module.load_entity("callable=DivIntegers",
            [ti(T.metaffi_int64_type), ti(T.metaffi_int64_type)],
            [ti(T.metaffi_float64_type)])
        result = fn(10, 2)
        assert abs(result - 5.0) < 1e-10, f"DivIntegers(10,2) = {result}, want 5.0"
        del fn

    def test_div_integers_fractional(self, go_module):
        fn = go_module.load_entity("callable=DivIntegers",
            [ti(T.metaffi_int64_type), ti(T.metaffi_int64_type)],
            [ti(T.metaffi_float64_type)])
        result = fn(7, 3)
        assert abs(result - 7.0/3.0) < 1e-10, f"DivIntegers(7,3) = {result}, want {7.0/3.0}"
        del fn

    def test_join_strings(self, go_module):
        fn = go_module.load_entity("callable=JoinStrings",
            [ti(T.metaffi_string8_array_type, dims=1)],
            [ti(T.metaffi_string8_type)])
        result = fn(["hello", "world"])
        assert result == "hello,world"
        del fn

    def test_join_strings_single(self, go_module):
        fn = go_module.load_entity("callable=JoinStrings",
            [ti(T.metaffi_string8_array_type, dims=1)],
            [ti(T.metaffi_string8_type)])
        result = fn(["only"])
        assert result == "only"
        del fn

    def test_wait_a_bit(self, go_module):
        fn = go_module.load_entity("callable=WaitABit",
            [ti(T.metaffi_int64_type)], None)
        fn(0)  # 0ms wait - just tests the call succeeds
        del fn

    def test_return_null(self, go_module):
        fn = go_module.load_entity("callable=ReturnNull", None,
            [ti(T.metaffi_any_type)])
        result = fn()
        assert result is None
        del fn

    def test_returns_an_error(self, go_module):
        """Go function returns error -> MetaFFI raises RuntimeError in Python."""
        fn = go_module.load_entity("callable=ReturnsAnError", None, None)
        with pytest.raises(RuntimeError, match="Error"):
            fn()
        del fn

    def test_return_any_int(self, go_module):
        fn = go_module.load_entity("callable=ReturnAny",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_any_type)])
        result = fn(0)  # which=0 -> int64(1)
        assert result == 1
        del fn

    def test_return_any_string(self, go_module):
        fn = go_module.load_entity("callable=ReturnAny",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_any_type)])
        result = fn(1)  # which=1 -> "string"
        assert result == "string"
        del fn

    def test_return_any_float(self, go_module):
        fn = go_module.load_entity("callable=ReturnAny",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_any_type)])
        result = fn(2)  # which=2 -> 3.0
        assert abs(result - 3.0) < 1e-10
        del fn

    def test_return_any_string_list(self, go_module):
        fn = go_module.load_entity("callable=ReturnAny",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_any_type)])
        result = fn(3)  # which=3 -> []string{"list", "of", "strings"}
        assert result == ["list", "of", "strings"]
        del fn

    def test_return_any_nil(self, go_module):
        fn = go_module.load_entity("callable=ReturnAny",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_any_type)])
        result = fn(99)  # default -> nil
        assert result is None
        del fn

    def test_return_multiple_return_values(self, go_module):
        """ReturnMultipleReturnValues() -> (int64, string, float64, any, []byte, *SomeClass)"""
        fn = go_module.load_entity("callable=ReturnMultipleReturnValues", None, [
            ti(T.metaffi_int64_type),
            ti(T.metaffi_string8_type),
            ti(T.metaffi_float64_type),
            ti(T.metaffi_any_type),
            ti(T.metaffi_uint8_array_type, dims=1),
            ti(T.metaffi_handle_type),
        ])
        result = fn()
        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 6, f"Expected 6 return values, got {len(result)}"

        assert result[0] == 1, f"result[0] = {result[0]}, want 1"
        assert result[1] == "string", f"result[1] = {result[1]!r}, want 'string'"
        assert abs(result[2] - 3.0) < 1e-10, f"result[2] = {result[2]}, want 3.0"
        assert result[3] is None, f"result[3] = {result[3]}, want None"
        assert list(result[4]) == [1, 2, 3], f"result[4] = {result[4]}, want [1,2,3]"
        # result[5] is a SomeClass handle - just verify it's not None
        assert result[5] is not None, "result[5] (SomeClass handle) is None"
        del fn


# ============================================================================
# Callbacks (core.go + callbacks.go)
# ============================================================================

class TestCallbacks:

    def test_call_callback_add(self, go_module):
        """Python callback passed to Go: add(1, 2) -> 3"""
        fn = go_module.load_entity("callable=CallCallbackAdd",
            [ti(T.metaffi_callable_type)],
            [ti(T.metaffi_int64_type)])

        def adder(a: int, b: int) -> int:
            return a + b

        metaffi_adder = metaffi.make_metaffi_callable(adder)
        result = fn(metaffi_adder)
        assert result == 3, f"CallCallbackAdd(adder): got {result}, want 3"
        del fn, metaffi_adder

    def test_return_callback_add(self, go_module):
        """Go returns a callback, Python calls it."""
        fn = go_module.load_entity("callable=ReturnCallbackAdd", None,
            [ti(T.metaffi_callable_type)])
        callback = fn()
        assert callback is not None, "ReturnCallbackAdd returned None"

        # Call the returned Go function: add(10, 20) -> 30
        result = callback(10, 20)
        # Returned callable may return list/tuple
        if isinstance(result, (list, tuple)):
            assert result[0] == 30, f"callback(10, 20)[0] = {result[0]}, want 30"
        else:
            assert result == 30, f"callback(10, 20) = {result}, want 30"
        del fn, callback

    @pytest.mark.xfail(reason="Go named type StringTransformer != func(string)string; "
                        "MetaFFI IDL exports as handle(StringTransformer), not callable")
    def test_call_transformer(self, go_module):
        """CallTransformer(transformer, value) -> transformer(value)"""
        fn = go_module.load_entity("callable=CallTransformer",
            [ti(T.metaffi_callable_type), ti(T.metaffi_string8_type)],
            [ti(T.metaffi_string8_type)])

        def upper(s: str) -> str:
            return s.upper()

        metaffi_upper = metaffi.make_metaffi_callable(upper)
        result = fn(metaffi_upper, "hello")
        assert result == "HELLO", f"CallTransformer(upper, 'hello') = {result!r}, want 'HELLO'"
        del fn, metaffi_upper

    @pytest.mark.xfail(reason="ReturnTransformer returns handle(StringTransformer), "
                        "not a callable; Go named function types not invocable from Python")
    def test_return_transformer(self, go_module):
        """ReturnTransformer(suffix) returns a callable that appends suffix."""
        fn = go_module.load_entity("callable=ReturnTransformer",
            [ti(T.metaffi_string8_type)],
            [ti(T.metaffi_callable_type)])
        transformer = fn("_suffix")
        assert transformer is not None

        result = transformer("hello")
        if isinstance(result, (list, tuple)):
            assert result[0] == "hello_suffix"
        else:
            assert result == "hello_suffix"
        del fn, transformer

    def test_call_function(self, go_module):
        """CallFunction(function, value) -> function(value)"""
        fn = go_module.load_entity("callable=CallFunction",
            [ti(T.metaffi_callable_type), ti(T.metaffi_string8_type)],
            [ti(T.metaffi_int64_type)])

        def strlen(s: str) -> int:
            return len(s)

        metaffi_strlen = metaffi.make_metaffi_callable(strlen)
        result = fn(metaffi_strlen, "hello")
        assert result == 5, f"CallFunction(strlen, 'hello') = {result}, want 5"
        del fn, metaffi_strlen


# ============================================================================
# Objects (objects.go)
# ============================================================================

class TestObjects:

    def test_new_test_map(self, go_module):
        """NewTestMap() returns a valid handle."""
        fn = go_module.load_entity("callable=NewTestMap", None,
            [ti(T.metaffi_handle_type)])
        handle = fn()
        assert handle is not None, "NewTestMap() returned None"
        del fn

    def test_test_map_set_get_contains(self, go_module):
        """TestMap: Set/Get/Contains round-trip."""
        new_map = go_module.load_entity("callable=NewTestMap", None,
            [ti(T.metaffi_handle_type)])
        set_fn = go_module.load_entity("callable=TestMap.Set",
            [ti(T.metaffi_handle_type), ti(T.metaffi_string8_type), ti(T.metaffi_any_type)],
            None)
        get_fn = go_module.load_entity("callable=TestMap.Get",
            [ti(T.metaffi_handle_type), ti(T.metaffi_string8_type)],
            [ti(T.metaffi_any_type)])
        contains_fn = go_module.load_entity("callable=TestMap.Contains",
            [ti(T.metaffi_handle_type), ti(T.metaffi_string8_type)],
            [ti(T.metaffi_bool_type)])

        handle = new_map()

        # Initially: key should not exist
        assert contains_fn(handle, "mykey") is False

        # Set key
        set_fn(handle, "mykey", "myvalue")

        # Now key exists
        assert contains_fn(handle, "mykey") is True

        # Get returns the value
        val = get_fn(handle, "mykey")
        assert val == "myvalue", f"TestMap.Get('mykey') = {val!r}, want 'myvalue'"

        del new_map, set_fn, get_fn, contains_fn

    def test_test_map_name_field(self, go_module):
        """TestMap.Name field getter and setter (exported as GetName/SetName methods)."""
        new_map = go_module.load_entity("callable=NewTestMap", None,
            [ti(T.metaffi_handle_type)])
        name_getter = go_module.load_entity("callable=TestMap.GetName",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_string8_type)])
        name_setter = go_module.load_entity("callable=TestMap.SetName",
            [ti(T.metaffi_handle_type), ti(T.metaffi_string8_type)],
            None)

        handle = new_map()

        # Default name is "name1"
        name = name_getter(handle)
        assert name == "name1", f"TestMap.Name = {name!r}, want 'name1'"

        # Set a new name
        name_setter(handle, "updated_name")
        name = name_getter(handle)
        assert name == "updated_name", f"TestMap.Name after set = {name!r}, want 'updated_name'"

        del new_map, name_getter, name_setter

    def test_some_class_print(self, go_module):
        """SomeClass.Print() via handle obtained from GetSomeClasses."""
        get_classes = go_module.load_entity("callable=GetSomeClasses", None,
            [ti(T.metaffi_handle_array_type, dims=1)])
        print_fn = go_module.load_entity("callable=SomeClass.Print",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_string8_type)])

        handles = get_classes()
        assert len(handles) == 3, f"GetSomeClasses returned {len(handles)} items, want 3"

        # First class has Name="a"
        result = print_fn(handles[0])
        assert result == "Hello from SomeClass a", f"Print() = {result!r}"

        del get_classes, print_fn

    def test_some_class_name_field(self, go_module):
        """SomeClass.Name field getter (exported as GetName method)."""
        get_classes = go_module.load_entity("callable=GetSomeClasses", None,
            [ti(T.metaffi_handle_array_type, dims=1)])
        name_getter = go_module.load_entity("callable=SomeClass.GetName",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_string8_type)])

        handles = get_classes()

        assert name_getter(handles[0]) == "a"
        assert name_getter(handles[1]) == "b"
        assert name_getter(handles[2]) == "c"

        del get_classes, name_getter

    @pytest.mark.xfail(reason="Outer.GetInner returns *Inner (pointer) but "
                        "Inner.GetValue expects Inner (value); MetaFFI pointer/value mismatch")
    def test_new_outer_nested_fields(self, go_module):
        """NewOuter(42) -> Outer.GetInner -> Inner.GetValue == 42"""
        new_outer = go_module.load_entity("callable=NewOuter",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_handle_type)])
        inner_getter = go_module.load_entity("callable=Outer.GetInner",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_handle_type)])
        value_getter = go_module.load_entity("callable=Inner.GetValue",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_int64_type)])

        outer = new_outer(42)
        inner = inner_getter(outer)
        val = value_getter(inner)
        assert val == 42, f"Inner.Value = {val}, want 42"

        del new_outer, inner_getter, value_getter


# ============================================================================
# Arrays (arrays.go)
# ============================================================================

class TestArrays:

    @pytest.mark.xfail(reason="Go [][]int returned as handles; Go int != int64 "
                        "prevents MetaFFI from converting multi-dim int arrays")
    def test_make_2d_array(self, go_module):
        fn = go_module.load_entity("callable=Make2DArray", None,
            [ti(T.metaffi_int64_array_type, dims=2)])
        result = fn()
        assert result == [[1, 2], [3, 4]], f"Make2DArray() = {result}"
        del fn

    @pytest.mark.xfail(reason="Go [][][]int returned as handles; Go int != int64")
    def test_make_3d_array(self, go_module):
        fn = go_module.load_entity("callable=Make3DArray", None,
            [ti(T.metaffi_int64_array_type, dims=3)])
        result = fn()
        assert result == [[[1], [2]], [[3], [4]]], f"Make3DArray() = {result}"
        del fn

    @pytest.mark.xfail(reason="Go [][]int returned as handles; Go int != int64")
    def test_make_ragged_array(self, go_module):
        fn = go_module.load_entity("callable=MakeRaggedArray", None,
            [ti(T.metaffi_int64_array_type, dims=2)])
        result = fn()
        assert result == [[1, 2, 3], [4], [5, 6]], f"MakeRaggedArray() = {result}"
        del fn

    @pytest.mark.xfail(reason="Go [][]int input: MetaFFI passes [][]int64, "
                        "Go type assertion fails (int64 != int)")
    def test_sum_ragged_array(self, go_module):
        fn = go_module.load_entity("callable=SumRaggedArray",
            [ti(T.metaffi_int64_array_type, dims=2)],
            [ti(T.metaffi_int64_type)])
        result = fn([[1, 2, 3], [4], [5, 6]])
        assert result == 21, f"SumRaggedArray([[1,2,3],[4],[5,6]]) = {result}, want 21"
        del fn

    @pytest.mark.xfail(reason="Go [][][]int input: MetaFFI passes [][][]int64, "
                        "Go type assertion fails (int64 != int)")
    def test_sum_3d_array(self, go_module):
        fn = go_module.load_entity("callable=Sum3DArray",
            [ti(T.metaffi_int64_array_type, dims=3)],
            [ti(T.metaffi_int64_type)])
        result = fn([[[1], [2]], [[3], [4]]])
        assert result == 10, f"Sum3DArray([[[1],[2]],[[3],[4]]]) = {result}, want 10"
        del fn

    @pytest.mark.xfail(reason="2D byte array ([][]uint8) return conversion: "
                        "MetaFFI Python bridge cdt_array_to_pybytes fails on 2D")
    def test_get_three_buffers(self, go_module):
        fn = go_module.load_entity("callable=GetThreeBuffers", None,
            [ti(T.metaffi_uint8_array_type, dims=2)])
        result = fn()
        assert len(result) == 3
        assert list(result[0]) == [1, 2, 3, 4]
        assert list(result[1]) == [5, 6, 7]
        assert list(result[2]) == [8, 9]
        del fn

    def test_echo_bytes(self, go_module):
        fn = go_module.load_entity("callable=EchoBytes",
            [ti(T.metaffi_uint8_array_type, dims=1)],
            [ti(T.metaffi_uint8_array_type, dims=1)])
        result = fn([10, 20, 30])
        assert list(result) == [10, 20, 30]
        del fn

    def test_get_some_classes(self, go_module):
        fn = go_module.load_entity("callable=GetSomeClasses", None,
            [ti(T.metaffi_handle_array_type, dims=1)])
        handles = fn()
        assert len(handles) == 3, f"GetSomeClasses() returned {len(handles)} items, want 3"
        for h in handles:
            assert h is not None, "SomeClass handle is None"
        del fn

    def test_make_string_list(self, go_module):
        fn = go_module.load_entity("callable=MakeStringList", None,
            [ti(T.metaffi_string8_array_type, dims=1)])
        result = fn()
        assert result == ["a", "b", "c"], f"MakeStringList() = {result}"
        del fn


# ============================================================================
# Primitives (primitives.go)
# ============================================================================

class TestPrimitives:

    def test_to_upper_rune(self, go_module):
        """ToUpperRune('a') -> 'A' (rune = int32)"""
        fn = go_module.load_entity("callable=ToUpperRune",
            [ti(T.metaffi_int32_type)],
            [ti(T.metaffi_int32_type)])
        result = fn(ord('a'))
        assert result == ord('A'), f"ToUpperRune('a') = {chr(result)!r}, want 'A'"
        del fn

    def test_to_upper_rune_nonletter(self, go_module):
        """ToUpperRune('5') -> '5' (no change)"""
        fn = go_module.load_entity("callable=ToUpperRune",
            [ti(T.metaffi_int32_type)],
            [ti(T.metaffi_int32_type)])
        result = fn(ord('5'))
        assert result == ord('5')
        del fn


# ============================================================================
# State (state.go)
# ============================================================================

class TestState:

    def test_counter_operations(self, go_module):
        """GetCounter, SetCounter, IncCounter round-trip."""
        get_fn = go_module.load_entity("callable=GetCounter", None,
            [ti(T.metaffi_int64_type)])
        set_fn = go_module.load_entity("callable=SetCounter",
            [ti(T.metaffi_int64_type)], None)
        inc_fn = go_module.load_entity("callable=IncCounter",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_int64_type)])

        # Reset counter to 0
        set_fn(0)
        assert get_fn() == 0

        # Increment by 5
        new_val = inc_fn(5)
        assert new_val == 5, f"IncCounter(5) = {new_val}, want 5"
        assert get_fn() == 5

        # Increment by 10
        new_val = inc_fn(10)
        assert new_val == 15, f"IncCounter(10) = {new_val}, want 15"

        # Reset
        set_fn(0)
        assert get_fn() == 0

        del get_fn, set_fn, inc_fn

    def test_five_seconds_global(self, go_module):
        """FiveSeconds global variable (exported as GetFiveSeconds/SetFiveSeconds)."""
        getter = go_module.load_entity("callable=GetFiveSeconds", None,
            [ti(T.metaffi_int64_type)])
        setter = go_module.load_entity("callable=SetFiveSeconds",
            [ti(T.metaffi_int64_type)], None)

        # Default value is 5
        val = getter()
        assert val == 5, f"FiveSeconds = {val}, want 5"

        # Set to a different value
        setter(42)
        assert getter() == 42

        # Restore original
        setter(5)
        assert getter() == 5

        del getter, setter


# ============================================================================
# Errors (errors.go)
# ============================================================================

class TestErrors:

    def test_return_error_tuple_ok(self, go_module):
        """ReturnErrorTuple(true) -> (true, nil)"""
        fn = go_module.load_entity("callable=ReturnErrorTuple",
            [ti(T.metaffi_bool_type)],
            [ti(T.metaffi_bool_type)])
        result = fn(True)
        assert result is True, f"ReturnErrorTuple(true) = {result}, want True"
        del fn

    def test_return_error_tuple_fail(self, go_module):
        """ReturnErrorTuple(false) -> (false, error) -> raises RuntimeError"""
        fn = go_module.load_entity("callable=ReturnErrorTuple",
            [ti(T.metaffi_bool_type)],
            [ti(T.metaffi_bool_type)])
        with pytest.raises(RuntimeError, match="error"):
            fn(False)
        del fn

    def test_panics(self, go_module):
        """Panics() -> Go panic -> RuntimeError in Python"""
        fn = go_module.load_entity("callable=Panics", None, None)
        with pytest.raises(RuntimeError, match="panic"):
            fn()
        del fn


# ============================================================================
# Enums (enum.go)
# ============================================================================

class TestEnums:

    def test_get_color_and_name(self, go_module):
        """GetColor(idx) returns Color handle, ColorName(handle) returns string."""
        get_color = go_module.load_entity("callable=GetColor",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_handle_type)])
        color_name = go_module.load_entity("callable=ColorName",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_string8_type)])

        red = get_color(0)
        assert color_name(red) == "RED"

        green = get_color(1)
        assert color_name(green) == "GREEN"

        blue = get_color(2)
        assert color_name(blue) == "BLUE"

        del get_color, color_name


# ============================================================================
# Generics (generics.go)
# ============================================================================

class TestGenerics:

    @pytest.mark.xfail(reason="Generic method Box.Get not exported in Go guest IDL; "
                        "only NewIntBox/NewStringBox constructors are available")
    def test_new_int_box(self, go_module):
        """NewIntBox(42) -> Box[int] handle, then Get() -> 42"""
        new_box = go_module.load_entity("callable=NewIntBox",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_handle_type)])
        get_fn = go_module.load_entity("callable=Box.Get",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_any_type)])

        box = new_box(42)
        val = get_fn(box)
        assert val == 42, f"Box.Get() = {val}, want 42"
        del new_box, get_fn

    @pytest.mark.xfail(reason="Generic method Box.Get not exported in Go guest IDL")
    def test_new_string_box(self, go_module):
        """NewStringBox("hello") -> Box[string] handle, then Get() -> "hello" """
        new_box = go_module.load_entity("callable=NewStringBox",
            [ti(T.metaffi_string8_type)],
            [ti(T.metaffi_handle_type)])
        get_fn = go_module.load_entity("callable=Box.Get",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_any_type)])

        box = new_box("hello")
        val = get_fn(box)
        assert val == "hello", f"Box.Get() = {val!r}, want 'hello'"
        del new_box, get_fn

    @pytest.mark.xfail(reason="Generic methods Box.Get/Box.Set not exported in Go guest IDL")
    def test_box_set(self, go_module):
        """Box.Set(handle, newValue) updates the box."""
        new_box = go_module.load_entity("callable=NewIntBox",
            [ti(T.metaffi_int64_type)],
            [ti(T.metaffi_handle_type)])
        get_fn = go_module.load_entity("callable=Box.Get",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_any_type)])
        set_fn = go_module.load_entity("callable=Box.Set",
            [ti(T.metaffi_handle_type), ti(T.metaffi_any_type)],
            None)

        box = new_box(10)
        assert get_fn(box) == 10

        set_fn(box, 99)
        assert get_fn(box) == 99

        del new_box, get_fn, set_fn


# ============================================================================
# Varargs (varargs.go)
# ============================================================================

class TestVarargs:

    @pytest.mark.xfail(reason="Go varargs (Sum(...int)) exported as single int64 param "
                        "in IDL; array-to-variadic conversion not supported")
    def test_sum(self, go_module):
        """Sum(values ...int) -> int. Varargs passed as array."""
        fn = go_module.load_entity("callable=Sum",
            [ti(T.metaffi_int64_array_type, dims=1)],
            [ti(T.metaffi_int64_type)])
        assert fn([1, 2, 3, 4, 5]) == 15
        assert fn([]) == 0
        assert fn([100]) == 100
        del fn

    @pytest.mark.xfail(reason="Go varargs (Join(string, ...string)) exported as "
                        "single-value params in IDL; variadic expansion not supported")
    def test_join(self, go_module):
        """Join(prefix, values ...string) -> string. Mixed params + varargs."""
        fn = go_module.load_entity("callable=Join",
            [ti(T.metaffi_string8_type), ti(T.metaffi_string8_array_type, dims=1)],
            [ti(T.metaffi_string8_type)])
        result = fn("prefix", ["a", "b", "c"])
        assert result == "prefix:a:b:c", f"Join('prefix', ['a','b','c']) = {result!r}"
        del fn


# ============================================================================
# Async (channels.go)
# ============================================================================

class TestAsync:

    def test_add_async(self, go_module):
        """AddAsync(a, b) -> a + b computed asynchronously."""
        fn = go_module.load_entity("callable=AddAsync",
            [ti(T.metaffi_int64_type), ti(T.metaffi_int64_type)],
            [ti(T.metaffi_int64_type)])
        result = fn(17, 25)
        assert result == 42, f"AddAsync(17, 25) = {result}, want 42"
        del fn
