#include "test_env.h"

#include <utils/env_utils.h>

#include <filesystem>
#include <stdexcept>
#include <string>

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

std::string resolve_python3_module_path()
{
	std::string root = require_env("METAFFI_SOURCE_ROOT");
	std::filesystem::path path(root);
	path /= "sdk";
	path /= "test_modules";
	path /= "guest_modules";
	path /= "python3";
	path /= "module";

	std::string path_str = path.string();
	if (!std::filesystem::exists(path_str))
	{
		throw std::runtime_error(
			"Python3 guest module directory not found: " + path_str);
	}
	return path_str;
}

} // namespace

TestEnv::TestEnv()
	: runtime("python3")
	, module(runtime.runtime_plugin(), resolve_python3_module_path())
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
