"""Correctness tests: Python3 -> Java via MetaFFI

Tests ALL Java guest module entities accessible through MetaFFI.
Fail-fast: every assertion is exact (or epsilon-justified for floats).
"""

import pytest
import metaffi

T = metaffi.MetaFFITypes
ti = metaffi.metaffi_type_info

# ---------------------------------------------------------------------------
# Common xfail reasons for known MetaFFI SDK bugs
# ---------------------------------------------------------------------------

_XFAIL_NO_PARAMS_RET = pytest.mark.xfail(
    reason="MetaFFI JVM plugin bug: no-params-with-return xcall from Python "
           "host raises 'Index 0 out of bounds (size: 0)'",
    raises=RuntimeError, strict=True,
)

_XFAIL_CALLABLE_PARAM = pytest.mark.xfail(
    reason="MetaFFI JVM plugin bug: entity loading fails for methods that "
           "accept metaffi_callable_type parameters",
    raises=RuntimeError, strict=True,
)

_XFAIL_CALLABLE_RETURN = pytest.mark.xfail(
    reason="MetaFFI JVM plugin bug: callable return type not supported from "
           "Python host",
    raises=RuntimeError, strict=True,
)

_XFAIL_CHAR16 = pytest.mark.xfail(
    reason="MetaFFI JVM plugin bug: char16 type causes access violation "
           "reading 0xFFFFFFFFFFFFFFFF from Python host",
    raises=OSError, strict=True,
)

_XFAIL_3D_ARRAY_INVOKE = pytest.mark.xfail(
    reason="MetaFFI JVM plugin bug: 3D array param causes "
           "java.lang.reflect.InvocationTargetException",
    raises=RuntimeError, strict=True,
)


# ============================================================================
# Core functions (guest.CoreFunctions)
# ============================================================================

class TestCoreFunctions:

    @_XFAIL_NO_PARAMS_RET
    def test_hello_world(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=helloWorld",
            None, [ti(T.metaffi_string8_type)])
        result = fn()
        assert result == "Hello World, from Java"
        del fn

    def test_div_integers(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=divIntegers",
            [ti(T.metaffi_int64_type), ti(T.metaffi_int64_type)],
            [ti(T.metaffi_float64_type)])
        result = fn(10, 2)
        assert abs(result - 5.0) < 1e-10, f"divIntegers(10,2) = {result}, want 5.0"
        del fn

    def test_div_integers_fractional(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=divIntegers",
            [ti(T.metaffi_int64_type), ti(T.metaffi_int64_type)],
            [ti(T.metaffi_float64_type)])
        result = fn(7, 3)
        assert abs(result - 7.0 / 3.0) < 1e-10
        del fn

    def test_join_strings(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=joinStrings",
            [ti(T.metaffi_string8_array_type, dims=1)],
            [ti(T.metaffi_string8_type)])
        result = fn(["hello", "world"])
        assert result == "hello,world"
        del fn

    def test_join_strings_single(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=joinStrings",
            [ti(T.metaffi_string8_array_type, dims=1)],
            [ti(T.metaffi_string8_type)])
        result = fn(["only"])
        assert result == "only"
        del fn

    def test_wait_a_bit(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=waitABit",
            [ti(T.metaffi_int64_type)], None)
        fn(0)
        del fn

    @_XFAIL_NO_PARAMS_RET
    def test_return_null(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=returnNull",
            None, [ti(T.metaffi_handle_type)])
        result = fn()
        assert result is None
        del fn

    def test_returns_an_error(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=returnsAnError",
            None, None)
        with pytest.raises(RuntimeError, match="(?i)(error|exception)"):
            fn()
        del fn

    def test_return_any_int(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=returnAny",
            [ti(T.metaffi_int32_type)],
            [ti(T.metaffi_any_type)])
        result = fn(0)  # which=0 -> Integer(1)
        assert result == 1
        del fn

    def test_return_any_string(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=returnAny",
            [ti(T.metaffi_int32_type)],
            [ti(T.metaffi_any_type)])
        result = fn(1)  # which=1 -> "string"
        assert result == "string"
        del fn

    def test_return_any_nil(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=returnAny",
            [ti(T.metaffi_int32_type)],
            [ti(T.metaffi_any_type)])
        result = fn(999)  # default -> null
        assert result is None
        del fn

    @_XFAIL_NO_PARAMS_RET
    def test_return_multiple_return_values(self, java_module):
        """returnMultipleReturnValues() -> Object[] with mixed types."""
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=returnMultipleReturnValues",
            None, [ti(T.metaffi_any_array_type, dims=1)])
        result = fn()
        assert isinstance(result, (list, tuple))
        # Contents: [1, "string", 3.0, null, byte[]{1,2,3}, SomeClass]
        assert result[0] == 1
        assert result[1] == "string"
        assert abs(result[2] - 3.0) < 1e-10
        assert result[3] is None
        del fn


# ============================================================================
# Callbacks (guest.CoreFunctions + guest.Callbacks)
# ============================================================================

class TestCallbacks:

    @_XFAIL_CALLABLE_PARAM
    def test_call_callback_add(self, java_module):
        """Python callback passed to Java: add(1, 2) -> 3"""
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=callCallbackAdd",
            [ti(T.metaffi_callable_type)],
            [ti(T.metaffi_int32_type)])

        def adder(a: int, b: int) -> int:
            return a + b

        metaffi_adder = metaffi.make_metaffi_callable(adder)
        result = fn(metaffi_adder)
        assert result == 3, f"callCallbackAdd(adder): got {result}, want 3"
        del fn, metaffi_adder

    @_XFAIL_NO_PARAMS_RET
    def test_return_callback_add(self, java_module):
        """Java returns a callback, Python calls it."""
        fn = java_module.load_entity(
            "class=guest.CoreFunctions,callable=returnCallbackAdd",
            None, [ti(T.metaffi_callable_type)])
        callback = fn()
        assert callback is not None

        result = callback(3, 4)
        if isinstance(result, (list, tuple)):
            assert result[0] == 7, f"callback(3,4)[0] = {result[0]}, want 7"
        else:
            assert result == 7, f"callback(3,4) = {result}, want 7"
        del fn, callback

    @_XFAIL_CALLABLE_PARAM
    def test_call_transformer(self, java_module):
        """callTransformer(transformer, value) -> transformer.transform(value)"""
        fn = java_module.load_entity(
            "class=guest.Callbacks,callable=callTransformer",
            [ti(T.metaffi_callable_type), ti(T.metaffi_string8_type)],
            [ti(T.metaffi_string8_type)])

        def append_x(s: str) -> str:
            return s + "_x"

        metaffi_fn = metaffi.make_metaffi_callable(append_x)
        result = fn(metaffi_fn, "a")
        assert result == "a_x", f"callTransformer(append_x, 'a') = {result!r}"
        del fn, metaffi_fn

    @_XFAIL_CALLABLE_RETURN
    def test_return_transformer(self, java_module):
        """returnTransformer(suffix) returns callable that appends suffix."""
        fn = java_module.load_entity(
            "class=guest.Callbacks,callable=returnTransformer",
            [ti(T.metaffi_string8_type)],
            [ti(T.metaffi_callable_type)])
        transformer = fn("_y")
        assert transformer is not None

        result = transformer("b")
        if isinstance(result, (list, tuple)):
            assert result[0] == "b_y"
        else:
            assert result == "b_y"
        del fn, transformer


# ============================================================================
# Objects (guest.SomeClass, guest.TestMap)
# ============================================================================

class TestObjects:

    @_XFAIL_NO_PARAMS_RET
    def test_some_class_default_constructor(self, java_module):
        new_fn = java_module.load_entity(
            "class=guest.SomeClass,callable=<init>",
            None, [ti(T.metaffi_handle_type)])
        handle = new_fn()
        assert handle is not None

        print_fn = java_module.load_entity(
            "class=guest.SomeClass,callable=print,instance_required",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_string8_type)])
        result = print_fn(handle)
        assert result == "Hello from SomeClass some", f"print() = {result!r}"
        del new_fn, print_fn

    def test_some_class_named_constructor(self, java_module):
        new_fn = java_module.load_entity(
            "class=guest.SomeClass,callable=<init>",
            [ti(T.metaffi_string8_type)],
            [ti(T.metaffi_handle_type)])
        handle = new_fn("test_name")

        name_fn = java_module.load_entity(
            "class=guest.SomeClass,callable=getName,instance_required",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_string8_type)])
        name = name_fn(handle)
        assert name == "test_name", f"getName() = {name!r}"
        del new_fn, name_fn

    @_XFAIL_NO_PARAMS_RET
    def test_test_map_set_get_contains(self, java_module):
        new_map = java_module.load_entity(
            "class=guest.TestMap,callable=<init>",
            None, [ti(T.metaffi_handle_type)])
        set_fn = java_module.load_entity(
            "class=guest.TestMap,callable=set,instance_required",
            [ti(T.metaffi_handle_type), ti(T.metaffi_string8_type), ti(T.metaffi_any_type)],
            None)
        get_fn = java_module.load_entity(
            "class=guest.TestMap,callable=get,instance_required",
            [ti(T.metaffi_handle_type), ti(T.metaffi_string8_type)],
            [ti(T.metaffi_any_type)])
        contains_fn = java_module.load_entity(
            "class=guest.TestMap,callable=contains,instance_required",
            [ti(T.metaffi_handle_type), ti(T.metaffi_string8_type)],
            [ti(T.metaffi_bool_type)])

        handle = new_map()
        assert contains_fn(handle, "mykey") is False

        set_fn(handle, "mykey", "myvalue")
        assert contains_fn(handle, "mykey") is True

        val = get_fn(handle, "mykey")
        assert val == "myvalue", f"get('mykey') = {val!r}"
        del new_map, set_fn, get_fn, contains_fn

    @_XFAIL_NO_PARAMS_RET
    def test_test_map_name_field(self, java_module):
        new_map = java_module.load_entity(
            "class=guest.TestMap,callable=<init>",
            None, [ti(T.metaffi_handle_type)])
        name_getter = java_module.load_entity(
            "class=guest.TestMap,field=name,getter,instance_required",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_string8_type)])
        name_setter = java_module.load_entity(
            "class=guest.TestMap,field=name,setter,instance_required",
            [ti(T.metaffi_handle_type), ti(T.metaffi_string8_type)],
            None)

        handle = new_map()
        name = name_getter(handle)
        assert name == "name1", f"TestMap.name = {name!r}, want 'name1'"

        name_setter(handle, "updated")
        name = name_getter(handle)
        assert name == "updated", f"TestMap.name after set = {name!r}"
        del new_map, name_getter, name_setter


# ============================================================================
# Arrays (guest.ArrayFunctions)
# ============================================================================

class TestArrays:

    @_XFAIL_NO_PARAMS_RET
    def test_make_2d_array(self, java_module):
        fn = java_module.load_entity(
            "class=guest.ArrayFunctions,callable=make2dArray",
            None, [ti(T.metaffi_int32_array_type, dims=2)])
        result = fn()
        assert result == [[1, 2], [3, 4]], f"make2dArray() = {result}"
        del fn

    @_XFAIL_NO_PARAMS_RET
    def test_make_3d_array(self, java_module):
        fn = java_module.load_entity(
            "class=guest.ArrayFunctions,callable=make3dArray",
            None, [ti(T.metaffi_int32_array_type, dims=3)])
        result = fn()
        assert result == [[[1], [2]], [[3], [4]]], f"make3dArray() = {result}"
        del fn

    @_XFAIL_NO_PARAMS_RET
    def test_make_ragged_array(self, java_module):
        fn = java_module.load_entity(
            "class=guest.ArrayFunctions,callable=makeRaggedArray",
            None, [ti(T.metaffi_int32_array_type, dims=2)])
        result = fn()
        assert result == [[1, 2, 3], [4], [5, 6]], f"makeRaggedArray() = {result}"
        del fn

    def test_sum_ragged_array(self, java_module):
        fn = java_module.load_entity(
            "class=guest.ArrayFunctions,callable=sumRaggedArray",
            [ti(T.metaffi_int32_array_type, dims=2)],
            [ti(T.metaffi_int32_type)])
        result = fn([[1, 2, 3], [4], [5, 6]])
        assert result == 21, f"sumRaggedArray = {result}, want 21"
        del fn

    @_XFAIL_3D_ARRAY_INVOKE
    def test_sum_3d_array(self, java_module):
        fn = java_module.load_entity(
            "class=guest.ArrayFunctions,callable=sum3dArray",
            [ti(T.metaffi_int32_array_type, dims=3)],
            [ti(T.metaffi_int32_type)])
        result = fn([[[1], [2]], [[3], [4]]])
        assert result == 10, f"sum3dArray = {result}, want 10"
        del fn

    @_XFAIL_NO_PARAMS_RET
    def test_get_some_classes(self, java_module):
        fn = java_module.load_entity(
            "class=guest.ArrayFunctions,callable=getSomeClasses",
            None, [ti(T.metaffi_handle_array_type, dims=1)])
        handles = fn()
        assert len(handles) == 3
        for h in handles:
            assert h is not None
        del fn

    @_XFAIL_NO_PARAMS_RET
    def test_make_string_list(self, java_module):
        fn = java_module.load_entity(
            "class=guest.CollectionFunctions,callable=makeStringList",
            None, [ti(T.metaffi_handle_type)])
        result = fn()
        # Returns a Java List<String> as a handle
        assert result is not None
        del fn

    def test_echo_bytes(self, java_module):
        fn = java_module.load_entity(
            "class=guest.PrimitiveFunctions,callable=echoBytes",
            [ti(T.metaffi_int8_array_type, dims=1)],
            [ti(T.metaffi_int8_array_type, dims=1)])
        result = fn([1, 2, 3, 4, 5])
        assert list(result) == [1, 2, 3, 4, 5]
        del fn


# ============================================================================
# Primitives (guest.PrimitiveFunctions)
# ============================================================================

class TestPrimitives:

    @_XFAIL_CHAR16
    def test_to_upper(self, java_module):
        fn = java_module.load_entity(
            "class=guest.PrimitiveFunctions,callable=toUpper",
            [ti(T.metaffi_char16_type)],
            [ti(T.metaffi_char16_type)])
        result = fn('a')
        assert result == 'A' or result == ord('A'), f"toUpper('a') = {result!r}"
        del fn


# ============================================================================
# State (guest.StaticState)
# ============================================================================

class TestState:

    @_XFAIL_NO_PARAMS_RET
    def test_five_seconds_constant(self, java_module):
        getter = java_module.load_entity(
            "class=guest.StaticState,field=FIVE_SECONDS,getter",
            None, [ti(T.metaffi_int64_type)])
        val = getter()
        assert val == 5, f"FIVE_SECONDS = {val}, want 5"
        del getter

    @_XFAIL_NO_PARAMS_RET
    def test_counter_operations(self, java_module):
        get_fn = java_module.load_entity(
            "class=guest.StaticState,callable=getCounter",
            None, [ti(T.metaffi_int32_type)])
        set_fn = java_module.load_entity(
            "class=guest.StaticState,callable=setCounter",
            [ti(T.metaffi_int32_type)], None)
        inc_fn = java_module.load_entity(
            "class=guest.StaticState,callable=incCounter",
            [ti(T.metaffi_int32_type)],
            [ti(T.metaffi_int32_type)])

        set_fn(0)
        assert get_fn() == 0

        new_val = inc_fn(5)
        assert new_val == 5
        assert get_fn() == 5

        new_val = inc_fn(10)
        assert new_val == 15

        set_fn(0)
        assert get_fn() == 0
        del get_fn, set_fn, inc_fn


# ============================================================================
# Errors (guest.Errors)
# ============================================================================

class TestErrors:

    def test_throw_runtime(self, java_module):
        fn = java_module.load_entity(
            "class=guest.Errors,callable=throwRuntime",
            None, None)
        with pytest.raises(RuntimeError, match="(?i)(error|exception)"):
            fn()
        del fn

    def test_throw_checked_true(self, java_module):
        fn = java_module.load_entity(
            "class=guest.Errors,callable=throwChecked",
            [ti(T.metaffi_bool_type)], None)
        with pytest.raises(RuntimeError):
            fn(True)
        del fn

    def test_throw_checked_false(self, java_module):
        fn = java_module.load_entity(
            "class=guest.Errors,callable=throwChecked",
            [ti(T.metaffi_bool_type)], None)
        fn(False)  # Should not raise
        del fn

    def test_return_error_string(self, java_module):
        fn = java_module.load_entity(
            "class=guest.Errors,callable=returnErrorString",
            [ti(T.metaffi_bool_type)],
            [ti(T.metaffi_string8_type)])
        assert fn(True) == "ok"
        assert fn(False) == "error"
        del fn


# ============================================================================
# Nested types (guest.NestedTypes)
# ============================================================================

class TestNestedTypes:

    def test_make_inner(self, java_module):
        make_inner = java_module.load_entity(
            "class=guest.NestedTypes,callable=makeInner",
            [ti(T.metaffi_int32_type)],
            [ti(T.metaffi_handle_type)])
        get_value = java_module.load_entity(
            "class=guest.NestedTypes$Inner,callable=getValue,instance_required",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_int32_type)])

        inner = make_inner(42)
        val = get_value(inner)
        assert val == 42, f"Inner.getValue() = {val}, want 42"
        del make_inner, get_value


# ============================================================================
# Sub-module (guest.sub.SubModule)
# ============================================================================

class TestSubModule:

    def test_echo(self, java_module):
        fn = java_module.load_entity(
            "class=guest.sub.SubModule,callable=echo",
            [ti(T.metaffi_string8_type)],
            [ti(T.metaffi_string8_type)])
        result = fn("test_input")
        assert result == "test_input", f"echo('test_input') = {result!r}"
        del fn
