cmake_minimum_required(VERSION 3.16.3)

project(tests VERSION 0.0.1)

include(CTest)
enable_testing()

# embedded from go
add_test(NAME embed_go_to_python3
		COMMAND python3 run_test.py ./Embed/Go/ToPython3/Sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

# embedded from python3
add_test(NAME embed_python3_to_go_deque
		COMMAND python3 run_test.py ./Embed/Python3/Deque
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME embed_python3_to_go_call_performance
		COMMAND python3 run_test.py ./Embed/Python3/CallPerformance
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME embed_python3_to_go_sanity
		COMMAND python3 run_test.py ./Embed/Python3/Sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

# from go
add_test(NAME go_to_python3_sanity
		COMMAND python3 run_test.py ./Hosts/Go/ToPython3/sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME go_to_python3_libraries_deque
		COMMAND python3 run_test.py ./Hosts/Go/ToPython3/libraries/deque
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME go_to_python3_libraries_python-string-utils
		COMMAND python3 run_test.py ./Hosts/Go/ToPython3/libraries/python-string-utils
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME go_to_java_sanity # TODO: Add test map in Java
		COMMAND python3 run_test.py ./Hosts/Go/ToJava/sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

# from python3
add_test(NAME python3_to_go_sanity
		COMMAND python3 run_test.py ./Hosts/Python3/ToGo/sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME python3_to_go_libraries_go-mcache
		COMMAND python3 run_test.py ./Hosts/Python3/ToGo/libraries/go-mcache
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME python3_to_go_libraries_goutils
		COMMAND python3 run_test.py ./Hosts/Python3/ToGo/libraries/goutils
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME python3_to_java_sanity
		COMMAND python3 run_test.py ./Hosts/Python3/ToJava/sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

# from java
add_test(NAME java_to_python3_sanity
		COMMAND python3 run_test.py ./Hosts/Java/ToPython3/sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME java_to_go_sanity
		COMMAND python3 run_test.py ./Hosts/Java/ToGo/sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME java_to_python3_libraries_python_string_utils
		COMMAND python3 run_test.py ./Hosts/Java/ToPython3/libraries/python_string_utils
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

# from kotlin

# from groovy

# from scala

file(ARCHIVE_CREATE OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/tests.zip
		PATHS ${CMAKE_CURRENT_SOURCE_DIR}
		FORMAT zip
		)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/tests.zip
		DESTINATION .)
