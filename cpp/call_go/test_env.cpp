#include "test_env.h"

#include <utils/env_utils.h>

#include <filesystem>
#include <stdexcept>
#include <string>

#ifndef GO_GUEST_LIB_NAME
#	define GO_GUEST_LIB_NAME "guest_MetaFFIGuest.dll"
#endif

namespace
{

std::string require_env(const char* name)
{
	std::string value = get_env_var(name);
	if (value.empty())
	{
		throw std::runtime_error(std::string("Environment variable not set: ") + name);
	}
	return value;
}

std::string resolve_go_module_path()
{
	std::string root = require_env("METAFFI_SOURCE_ROOT");
	std::filesystem::path path(root);
	path /= "sdk";
	path /= "test_modules";
	path /= "guest_modules";
	path /= "go";
	path /= "test_bin";
	path /= GO_GUEST_LIB_NAME;

	std::string path_str = path.string();
	if (!std::filesystem::exists(path_str))
	{
		throw std::runtime_error(
			"Go guest module not found: " + path_str +
			". Build go_guest_module target first.");
	}
	return path_str;
}

} // namespace

TestEnv::TestEnv()
	: runtime("go")
	, module(runtime.runtime_plugin(), resolve_go_module_path())
{
	runtime.load_runtime_plugin();
}

TestEnv::~TestEnv()
{
	runtime.release_runtime_plugin();
}

TestEnv& test_env()
{
	static TestEnv env;
	return env;
}
