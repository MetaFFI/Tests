import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Python3/extended/extended_test.py', 'extended_test.py')
	build_metaffi('extended_test.py', None, 'go', None)
	build_metaffi('metaffi_objects.py', None, 'go', None)
	build_metaffi('collections', 'py', 'go', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go test -v')
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('extended_test.py')
	os.remove('metaffi_objects.py')
	os.remove('extended_test_MetaFFIGuest.py')
	os.remove('collections_MetaFFIGuest.py')
	os.remove('metaffi_objects_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	shutil.rmtree('collections')
	shutil.rmtree('extended_test')
	shutil.rmtree('metaffi_objects')
