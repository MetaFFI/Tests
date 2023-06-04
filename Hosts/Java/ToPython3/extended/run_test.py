import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Python3/extended/extended_test.py', 'extended_test.py')
	build_metaffi('extended_test.py', None, 'openjdk', None)
	build_metaffi('metaffi_objects.py', None, 'openjdk', None)
	build_metaffi('collections', 'py', 'openjdk', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	metaffi_home = os.getenv("METAFFI_HOME")
	exec_cmd('javac -cp ".{0}./..{0}collections_MetaFFIHost.jar{0}extended_test_MetaFFIHost.jar{0}metaffi_objects_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" Main_test.java'.format(os.pathsep, metaffi_home))
	exec_cmd('java -cp ".{0}./..{0}collections_MetaFFIHost.jar{0}extended_test_MetaFFIHost.jar{0}metaffi_objects_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" extended.Main_test'.format(os.pathsep, metaffi_home))
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('extended_test.py')
	os.remove('metaffi_objects.py')
	os.remove('extended_test_MetaFFIGuest.py')
	os.remove('collections_MetaFFIGuest.py')
	os.remove('metaffi_objects_MetaFFIGuest.py')
	os.remove('extended_test_MetaFFIHost.jar')
	os.remove('collections_MetaFFIHost.jar')
	os.remove('metaffi_objects_MetaFFIHost.jar')
	os.remove('Main_test.class')

	shutil.rmtree('__pycache__')
