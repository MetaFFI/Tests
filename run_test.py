# usage: run_test.py [path to test]
import sys
from glob import glob
import os
import importlib
import shutil
import pathlib
from typing import Optional


def exec_cmd(cmd: str):
	print(cmd)
	if os.system(cmd) != 0:
		raise RuntimeError(f'Execution Failed: "{cmd}"')


def build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None):
	cmd = f'metaffi -c --idl {idl} '

	if idl_block is not None:
		cmd += f'-n {idl_block} '

	cmd += f'-g -h {host_lang} '

	if host_options is not None:
		cmd += f'--host-options "{host_options}" --print-idl'

	#cmd += '--print-idl'

	exec_cmd(cmd)


def usage():
	print('usage: run_test.py [path to test] - supports wildcards')
	exit(1)


def execute_paths(path: str):
	glob_matches = glob(path + '/run_test.py', recursive=True)
	if len(glob_matches) == 0:
		raise RuntimeError(f'No test were found in {path}')

	tests_root_path = os.getcwd()

	for match in glob_matches:
		print('executing ' + match)
		cur_dir = pathlib.Path().absolute()
		os.chdir(os.path.dirname(match))

		try:
			module_path = os.path.relpath(os.path.dirname(match))
			module_path = module_path.replace('.py', '')
			module_path = module_path.replace('.', '')
			module_path = module_path.replace('/', '.')
			module_path = module_path.replace('\\', '.')
			module_path += '.run_test'

			test_module = importlib.import_module(module_path)

			print('build metaffi stubs')
			test_module.build(tests_root_path, build_metaffi, exec_cmd)

			print('Running Tests')
			test_module.execute(tests_root_path, exec_cmd)
			print('Tests ran successfully!')

			print('Starting cleanup...')
			test_module.cleanup(tests_root_path)
		finally:
			os.chdir(cur_dir)


def main():
	if len(sys.argv) != 2:
		usage()

	try:
		execute_paths(sys.argv[1])
	except Exception as e:
		print(e)
		exit(2)


if __name__ == '__main__':
	sys.path.append(os.getcwd())
	main()
