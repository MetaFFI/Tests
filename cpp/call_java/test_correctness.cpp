#include <doctest/doctest.h>

#include "test_env.h"

#include <cstdint>
#include <string>

// ==========================================================================
// Core functions (guest.CoreFunctions)
// ==========================================================================

TEST_CASE("cpp->java - hello_world")
{
	auto& env = test_env();
	auto f = env.module.load_entity(
		"class=guest.CoreFunctions,callable=helloWorld",
		{}, {metaffi_string8_type});
	auto [msg] = f.call<std::string>();
	CHECK(msg == "Hello World, from Java");
}

TEST_CASE("cpp->java - returns_an_error")
{
	auto& env = test_env();
	auto f = env.module.load_entity(
		"class=guest.CoreFunctions,callable=returnsAnError",
		{}, {});
	CHECK_THROWS(f.call<>());
}

TEST_CASE("cpp->java - div_integers")
{
	auto& env = test_env();
	auto f = env.module.load_entity(
		"class=guest.CoreFunctions,callable=divIntegers",
		{metaffi_int64_type, metaffi_int64_type},
		{metaffi_float64_type});
	auto [v] = f.call<double>(int64_t(10), int64_t(2));
	CHECK(v == doctest::Approx(5.0));
}

// ==========================================================================
// State: counter (guest.StaticState)
// ==========================================================================

TEST_CASE("cpp->java - counter")
{
	auto& env = test_env();

	// Java StaticState counter methods use int (not long)
	auto set = env.module.load_entity(
		"class=guest.StaticState,callable=setCounter",
		{metaffi_int32_type},
		{});

	auto get = env.module.load_entity(
		"class=guest.StaticState,callable=getCounter",
		{},
		{metaffi_int32_type});

	auto inc = env.module.load_entity(
		"class=guest.StaticState,callable=incCounter",
		{metaffi_int32_type},
		{metaffi_int32_type});

	// Reset counter to 0
	CHECK_NOTHROW(set.call<>(int32_t(0)));

	auto [v0] = get.call<int32_t>();
	CHECK(v0 == 0);

	// Increment by 5
	auto [v1] = inc.call<int32_t>(int32_t(5));
	CHECK(v1 == 5);

	// Verify
	auto [v2] = get.call<int32_t>();
	CHECK(v2 == 5);

	// Reset
	CHECK_NOTHROW(set.call<>(int32_t(0)));
}
