# Dual-use: works as add_subdirectory() from the parent build, OR as a
# standalone project (cmake -S tests/cpp) for in-container compilation.

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    # ---- Standalone mode ----
    cmake_minimum_required(VERSION 3.21)
    project(metaffi_cpp_tests CXX)
    set(CMAKE_CXX_STANDARD 20)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)

    # Env var validation
    if(NOT DEFINED ENV{METAFFI_SOURCE_ROOT})
        message(FATAL_ERROR "METAFFI_SOURCE_ROOT env var is not set")
    endif()
    if(NOT DEFINED ENV{METAFFI_HOME})
        message(FATAL_ERROR "METAFFI_HOME env var is not set")
    endif()

    # Mirror sdk/CMakeLists.txt line 10
    set(metaffi_sdk_root "$ENV{METAFFI_SOURCE_ROOT}/sdk")
    set(sdk_include_dir  "$ENV{METAFFI_SOURCE_ROOT}/sdk")

    # ---- doctest ----
    find_package(doctest QUIET)
    if(NOT doctest_FOUND)
        find_path(DOCTEST_INCLUDE_DIR doctest/doctest.h
            PATHS /usr/include /usr/local/include
        )
        if(DOCTEST_INCLUDE_DIR)
            set(doctest_INCLUDE_DIRS "${DOCTEST_INCLUDE_DIR}")
            if(NOT TARGET doctest::doctest)
                add_library(doctest::doctest INTERFACE IMPORTED)
                set_target_properties(doctest::doctest PROPERTIES
                    INTERFACE_INCLUDE_DIRECTORIES "${DOCTEST_INCLUDE_DIR}")
            endif()
        else()
            message(FATAL_ERROR "doctest not found (tried find_package and find_path)")
        endif()
    else()
        # Normalise to doctest_INCLUDE_DIRS for sub-CMakeLists
        if(NOT doctest_INCLUDE_DIRS)
            get_target_property(doctest_INCLUDE_DIRS doctest::doctest
                INTERFACE_INCLUDE_DIRECTORIES)
        endif()
    endif()

    # ---- spdlog ----
    find_package(spdlog REQUIRED)

    # ---- Shim: find_or_install_package is a no-op (packages already found) ----
    macro(find_or_install_package PKG)
    endmacro()

    # ---- Shim: c_cpp_exe mirrors cmake/CPP.cmake but uses env vars ----
    # Must be a FUNCTION (not macro) so that path arguments with Windows
    # backslashes (e.g. C:\Users\...) are stored as variable values and never
    # re-parsed as CMake string literals (which would error on \U, \C, etc.).
    function(c_cpp_exe TARGET_NAME SOURCE INCLUDE LIBRARIES COPYPATH)
        # Normalise separators so Windows paths work in all CMake commands
        file(TO_CMAKE_PATH "${COPYPATH}" _copy_dest_raw)
        if(IS_ABSOLUTE "${_copy_dest_raw}")
            set(_copy_dest "${_copy_dest_raw}")
        else()
            file(TO_CMAKE_PATH "$ENV{METAFFI_HOME}" _metaffi_home)
            set(_copy_dest "${_metaffi_home}/${_copy_dest_raw}")
        endif()

        add_executable(${TARGET_NAME} ${SOURCE})

        if(UNIX)
            set_target_properties(${TARGET_NAME} PROPERTIES
                BUILD_WITH_INSTALL_RPATH  TRUE
                INSTALL_RPATH_USE_LINK_PATH FALSE
                INSTALL_RPATH             "$ORIGIN")
        endif()

        target_include_directories(${TARGET_NAME} PRIVATE ${INCLUDE})

        foreach(LIB ${LIBRARIES})
            target_link_libraries(${TARGET_NAME} PRIVATE ${LIB})
        endforeach()

        # C logging shim — use METAFFI_SOURCE_ROOT because CMAKE_SOURCE_DIR is tests/cpp
        file(TO_CMAKE_PATH "$ENV{METAFFI_SOURCE_ROOT}" _source_root)
        target_sources(${TARGET_NAME} PRIVATE
            "${_source_root}/sdk/utils/logger_c.cpp")

        # Prefer header-only spdlog (no DLL at runtime); fall back to compiled target
        if(TARGET spdlog::spdlog_header_only)
            target_link_libraries(${TARGET_NAME} PRIVATE spdlog::spdlog_header_only)
        else()
            target_link_libraries(${TARGET_NAME} PRIVATE spdlog::spdlog)
        endif()
        target_compile_definitions(${TARGET_NAME} PRIVATE SPDLOG_ACTIVE_LEVEL=0)

        add_custom_command(TARGET ${TARGET_NAME} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E echo
                "Going to copy $<TARGET_FILE:${TARGET_NAME}> to ${_copy_dest}:"
            COMMAND ${CMAKE_COMMAND} -E make_directory "${_copy_dest}"
            COMMAND ${CMAKE_COMMAND} -E copy
                $<TARGET_FILE:${TARGET_NAME}> "${_copy_dest}"
            COMMAND ${CMAKE_COMMAND} -E echo
                "Copied $<TARGET_FILE:${TARGET_NAME}> to ${_copy_dest}"
        )
    endfunction()

endif()  # end standalone mode

# ---- Subdirectories (unchanged) ----
add_subdirectory(call_go)
add_subdirectory(call_python3)
add_subdirectory(call_java)

# ---- Propagate target names to parent scope (only when used as subdirectory) ----
if(NOT CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    set(cpp_call_go_test      ${cpp_call_go_test}      PARENT_SCOPE)
    set(cpp_call_python3_test ${cpp_call_python3_test}  PARENT_SCOPE)
    set(cpp_call_java_test    ${cpp_call_java_test}     PARENT_SCOPE)
endif()
