#pragma once

#include <metaffi/api/metaffi_api.h>

struct TestEnv
{
	metaffi::api::MetaFFIRuntime runtime;
	metaffi::api::MetaFFIModule  module;

	TestEnv();
	~TestEnv();
};

TestEnv& test_env();
