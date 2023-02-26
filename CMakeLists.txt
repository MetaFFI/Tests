
#------------------------------- Tests project ------------------------------------------
project(tests VERSION 0.0.1)

add_ctest_and_catch2_packages()
get_app_path("python3" PY_EXEC)

macro(add_use_case_test NAME TEST_PATH)
	add_test(NAME "(Usecase Test) ${NAME}"
			COMMAND ${PY_EXEC} run_test.py ${TEST_PATH}
			WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})
endmacro()

# embedded from go
add_use_case_test("Embedding Go->Python3 Sanity" ./Embed/Go/ToPython3/Sanity)

# embedded from python3
add_use_case_test("Embedding Python3->Go Sanity" ./Embed/Python3/Sanity)
add_use_case_test("Embedding Python3->Go Deque" ./Embed/Python3/Deque)
add_use_case_test("Embedding Python3->Go Performance" ./Embed/Python3/CallPerformance)

# from go
add_use_case_test("Go->Python3 Sanity" ./Hosts/Go/ToPython3/sanity)
add_use_case_test("Go->Python3 Deque" ./Hosts/Go/ToPython3/libraries/deque)
add_use_case_test("Go->Python3 3rd Party - Python-String-Utils" ./Hosts/Go/ToPython3/libraries/python-string-utils)
add_use_case_test("Go->Java Sanity" ./Hosts/Go/ToJava/sanity)


# from python3
add_use_case_test("Python3->Go Sanity" ./Hosts/Python3/ToGo/sanity)
add_use_case_test("Python3->Go 3rd Party - MCache" ./Hosts/Python3/ToGo/libraries/go-mcache)
add_use_case_test("Python3->Go 3rd Party - GoUtils" ./Hosts/Python3/ToGo/libraries/goutils)
add_use_case_test("Python3->Java Sanity" ./Hosts/Python3/ToJava/sanity)


# from java
add_use_case_test("Java->Python Sanity" ./Hosts/Java/ToPython3/sanity)
add_use_case_test("Java->Go Sanity" ./Hosts/Java/ToGo/sanity)
add_use_case_test("Java->Python3 3rd Party - Python-String-Utils" ./Hosts/Java/ToPython3/libraries/python_string_utils)


# from kotlin

# from groovy

# from scala


# Provide all tests in to installer
file(ARCHIVE_CREATE OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/tests.zip
		PATHS ${CMAKE_CURRENT_SOURCE_DIR}
		FORMAT zip)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/tests.zip
		DESTINATION .)
