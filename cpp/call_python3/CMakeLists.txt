# C++ host test: C++ -> Python3 guest via MetaFFI

find_or_install_package(Boost COMPONENTS filesystem)
find_or_install_package(doctest)

set(test_src
	${CMAKE_CURRENT_LIST_DIR}/../../cpp_test_main.cpp
	${CMAKE_CURRENT_LIST_DIR}/test_env.cpp
	${CMAKE_CURRENT_LIST_DIR}/test_correctness.cpp
)

set(test_includes
	${sdk_include_dir}
	${metaffi_sdk_root}/api/cpp/include
	${CMAKE_CURRENT_LIST_DIR}
	${doctest_INCLUDE_DIRS}
	${Boost_INCLUDE_DIRS}
)

c_cpp_exe(cpp_call_python3_test
	"${test_src}"
	"${test_includes}"
	"doctest::doctest;Boost::filesystem;metaffi.api.cpp"
	"$ENV{METAFFI_HOME}"
)

target_compile_definitions(cpp_call_python3_test PRIVATE
	DOCTEST_CONFIG_NO_WINDOWS_SEH
)

add_test(NAME cpp_call_python3_test
	COMMAND $ENV{METAFFI_HOME}/cpp_call_python3_test${CMAKE_EXECUTABLE_SUFFIX})

if(WIN32)
	set(_test_path "$ENV{METAFFI_HOME}/python3;$ENV{METAFFI_HOME}/cpp;$ENV{PATH}")
	string(REPLACE ";" "\\;" _test_path "${_test_path}")
	set_tests_properties(cpp_call_python3_test PROPERTIES
		ENVIRONMENT "PATH=${_test_path}")
elseif(APPLE)
	set_tests_properties(cpp_call_python3_test PROPERTIES
		ENVIRONMENT "DYLD_LIBRARY_PATH=$ENV{METAFFI_HOME}/python3:$ENV{METAFFI_HOME}/cpp:$ENV{DYLD_LIBRARY_PATH}")
else()
	set_tests_properties(cpp_call_python3_test PROPERTIES
		ENVIRONMENT "LD_LIBRARY_PATH=$ENV{METAFFI_HOME}/python3:$ENV{METAFFI_HOME}/cpp:$ENV{LD_LIBRARY_PATH}")
endif()
