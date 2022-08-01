cmake_minimum_required(VERSION 3.16.3)

project(tests VERSION 0.0.1)

include(CTest)
enable_testing()

add_test(NAME embed_go_to_python3
		COMMAND python3 run_test.py ./Embed/Go/ToPython3/Sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME embed_python3_to_go_deque
		COMMAND python3 run_test.py ./Embed/Python3/Deque
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME embed_python3_to_go_call_performance
		COMMAND python3 run_test.py ./Embed/Python3/CallPerformance
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME embed_python3_to_go_sanity
		COMMAND python3 run_test.py ./Embed/Python3/Sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME go_to_python3_sanity
		COMMAND python3 run_test.py ./Hosts/Go/ToPython3/sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME go_to_python3_libraries_deque
		COMMAND python3 run_test.py ./Hosts/Go/ToPython3/libraries/deque
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

#TODO: To fix - place C implementations in a different file (cdt_capi_loader.go)
#add_test(NAME go_to_python3_libraries_python-string-utils
#		COMMAND python3 run_test.py ./Hosts/Go/ToPython3/libraries/python-string-utils
#		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})