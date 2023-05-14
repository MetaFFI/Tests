import os
import shutil
from typing import Callable, Optional
import sysconfig
import platform

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	build_metaffi('string_utils', 'py', 'openjdk', None)

def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	metaffi_home = os.getenv("METAFFI_HOME")
	exec_cmd('javac -cp ".{0}./..{0}string_utils_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" Main_test.java'.format(os.pathsep, metaffi_home))
	exec_cmd('java -cp ".{0}./..{0}string_utils_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" python_string_utils.Main_test'.format(os.pathsep, metaffi_home))
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('Main_test.class')
	os.remove('string_utils.java')
	os.remove('string_utils_MetaFFIGuest.py')
	os.remove('string_utils_MetaFFIHost.jar')
	shutil.rmtree('__pycache__')


