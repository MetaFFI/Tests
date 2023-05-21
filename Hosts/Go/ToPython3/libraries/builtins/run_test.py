import os
import platform
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	build_metaffi('builtins', 'py', 'go', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go test -v')

	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('builtins_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	shutil.rmtree('builtins')
