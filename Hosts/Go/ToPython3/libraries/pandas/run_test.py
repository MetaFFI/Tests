import os
import platform
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	build_metaffi('pandas', 'py', 'go', None)
	build_metaffi('pandas.core.indexing.py', 'py', 'go', None)
	build_metaffi('metaffi_objects.py', 'py', 'go', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go test -v')

	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('pandas_MetaFFIGuest.py')
	os.remove('pandas_core_indexing_MetaFFIGuest.py')
	os.remove('metaffi_objects.py')
	os.remove('metaffi_objects_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	shutil.rmtree('metaffi_objects')
	shutil.rmtree('pandas')
	shutil.rmtree('pandas_core_indexing')
