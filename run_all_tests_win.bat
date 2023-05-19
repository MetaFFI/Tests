python3 run_test.py ./Hosts/Go/ToPython3/sanity
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Go/ToPython3/libraries/collections
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Go/ToPython3/libraries/python-string-utils
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Go/ToJava/sanity
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Python3/ToGo/sanity
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Python3/ToGo/libraries/go-mcache
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Python3/ToJava/sanity
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Java/ToPython3/sanity
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Java/ToGo/sanity
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Java/ToPython3/libraries/python_string_utils
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on

python3 run_test.py ./Hosts/Java/ToPython3/libraries/collections
@echo off
IF %ERRORLEVEL% NEQ 0 (
	echo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
@echo on