import os
import platform
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Python3/libraries/deque/deque.json', 'deque.json')
	build_metaffi('deque.json', None, 'go', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go get -u')
	exec_cmd('go test')

	
def cleanup(tests_root_path: str):
	os.remove('deque.json')
	os.remove('deque_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	os.remove('deque_MetaFFIHost.go')
	os.remove('go.sum')
