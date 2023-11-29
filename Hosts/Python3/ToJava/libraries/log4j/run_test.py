import os
import shutil
from typing import Callable, Optional


# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str], Optional[str]], None], exec_cmd: Callable[[str], None]):
	shutil.copyfile(tests_root_path + '/Guests/Java/libraries/log4j/log4j-api-2.21.1.jar', 'log4j-api-2.21.1.jar')
	shutil.copyfile(tests_root_path + '/Guests/Java/libraries/log4j/log4j-core-2.21.1.jar', 'log4j-core-2.21.1.jar')
	shutil.copyfile(tests_root_path + '/Guests/Java/libraries/log4j/Log4jClass.java', 'Log4jClass.java')
	
	current_file = os.path.realpath(__file__)
	current_directory = os.path.dirname(current_file)
	
	build_metaffi('log4j-api-2.21.1.jar:org/apache/logging/log4j/LogManager;org/apache/logging/log4j/Logger',
				  None,
				  'python3',
				  None,
				  f"classPath={current_directory}/log4j-core-2.21.1.jar;{current_directory}/log4j-api-2.21.1.jar;{current_directory};{current_directory}/../")
	
	build_metaffi('Log4jClass.java',
	              None,
	              'python3',
	              None,
	              f"classPath={current_directory}/log4j-core-2.21.1.jar;{current_directory}/log4j-api-2.21.1.jar;{current_directory};{current_directory}/../")


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('python3 -m unittest Main_test.TestSanity')


def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('TestFuncs.java')
	os.remove('TestFuncs_MetaFFIGuest.jar')
	os.remove('TestFuncs_MetaFFIGuest' + dylib_ext)
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.py')
