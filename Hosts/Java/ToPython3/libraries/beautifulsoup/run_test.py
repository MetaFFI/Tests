import os
import platform
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	build_metaffi('bs4', 'py', 'openjdk', None)
	build_metaffi('requests', 'py', 'openjdk', None)
	build_metaffi('builtins', 'py', 'openjdk', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	metaffi_home = os.getenv("METAFFI_HOME")
	exec_cmd('javac -cp ".{0}./..{0}bs4_MetaFFIHost.jar{0}requests_MetaFFIHost.jar{0}builtins_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" Main_test.java'.format(os.pathsep, metaffi_home))
	exec_cmd('java -cp ".{0}./..{0}bs4_MetaFFIHost.jar{0}requests_MetaFFIHost.jar{0}builtins_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" beautifulsoup.Main_test'.format(os.pathsep, metaffi_home))

	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('bs4_MetaFFIGuest.py')
	os.remove('requests_MetaFFIGuest.py')
	os.remove('builtins_MetaFFIGuest.py')
	os.remove('metaffi_objects.py')
	os.remove('metaffi_objects_MetaFFIGuest.py')
	os.remove('bs4_MetaFFIHost.jar')
	os.remove('requests_MetaFFIHost.jar')
	os.remove('builtins_MetaFFIHost.jar')
	os.remove('Main_test.class')
	shutil.rmtree('__pycache__')
