set(METAFFI_TESTS_ROOT "${CMAKE_CURRENT_LIST_DIR}")
set(METAFFI_TESTS_RUNNER "${METAFFI_TESTS_ROOT}/run_all_tests.py")
set(METAFFI_TESTS_CORRECTNESS_CONFIG "${METAFFI_TESTS_ROOT}/configs/only_correctness_config.yml")

if(NOT EXISTS "${METAFFI_TESTS_RUNNER}")
    message(FATAL_ERROR "tests runner not found: ${METAFFI_TESTS_RUNNER}")
endif()

if(NOT EXISTS "${METAFFI_TESTS_CORRECTNESS_CONFIG}")
    message(FATAL_ERROR "correctness config not found: ${METAFFI_TESTS_CORRECTNESS_CONFIG}")
endif()

find_program(METAFFI_TESTS_PYTHON_EXEC NAMES python3 python REQUIRED)
find_or_install_pip_package(PyYAML)
find_or_install_pip_package(pytest)

add_test(
    NAME metaffi_tests_correctness
    COMMAND "${METAFFI_TESTS_PYTHON_EXEC}" "${METAFFI_TESTS_RUNNER}" --config "${METAFFI_TESTS_CORRECTNESS_CONFIG}"
    WORKING_DIRECTORY "${METAFFI_TESTS_ROOT}"
)
set_tests_properties(metaffi_tests_correctness PROPERTIES
    LABELS "metaffi;correctness"
)

add_custom_target(metaffi_tests)
set(metaffi_tests metaffi_tests PARENT_SCOPE)
