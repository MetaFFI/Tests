cmake_minimum_required(VERSION 3.16.3)

project(tests VERSION 0.0.1)

include(CTest)
enable_testing()

add_test(NAME embed_go_to_python3
		COMMAND python3 run_test.py ./Embed/Go/ToPython3
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME embed_python_to_go_deque
		COMMAND python3 run_test.py ./Embed/Python3/Deque
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

add_test(NAME embed_python_to_go_sanity
		COMMAND python3 run_test.py ./Embed/Python3/Sanity
		WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})