#include <doctest/doctest.h>

#include "test_env.h"

#include <cstdint>
#include <string>

// ==========================================================================
// Core functions
// ==========================================================================

TEST_CASE("cpp->go - hello_world")
{
	auto& env = test_env();
	auto f = env.module.load_entity("callable=HelloWorld", {}, {metaffi_string8_type});
	auto [msg] = f.call<std::string>();
	CHECK(msg == "Hello World, from Go");
}

TEST_CASE("cpp->go - returns_an_error")
{
	auto& env = test_env();
	auto f = env.module.load_entity("callable=ReturnsAnError", {}, {});
	CHECK_THROWS(f.call<>());
}

TEST_CASE("cpp->go - div_integers")
{
	auto& env = test_env();
	auto f = env.module.load_entity(
		"callable=DivIntegers",
		{metaffi_int64_type, metaffi_int64_type},
		{metaffi_float64_type});
	auto [v] = f.call<double>(int64_t(10), int64_t(2));
	CHECK(v == doctest::Approx(5.0));
}

// ==========================================================================
// State: counter
// ==========================================================================

TEST_CASE("cpp->go - counter")
{
	auto& env = test_env();

	auto set = env.module.load_entity(
		"callable=SetCounter",
		{metaffi_int64_type},
		{});

	auto get = env.module.load_entity(
		"callable=GetCounter",
		{},
		{metaffi_int64_type});

	auto inc = env.module.load_entity(
		"callable=IncCounter",
		{metaffi_int64_type},
		{metaffi_int64_type});

	// Reset counter to 0
	CHECK_NOTHROW(set.call<>(int64_t(0)));

	auto [v0] = get.call<int64_t>();
	CHECK(v0 == 0);

	// Increment by 5
	auto [v1] = inc.call<int64_t>(int64_t(5));
	CHECK(v1 == 5);

	// Verify
	auto [v2] = get.call<int64_t>();
	CHECK(v2 == 5);

	// Reset
	CHECK_NOTHROW(set.call<>(int64_t(0)));
}
