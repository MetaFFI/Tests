# usage: run_test.py [path to test]
import sys
from glob import glob
import os
import importlib
import distutils.ccompiler
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
		cmd += f'--host-options "{host_options}"'

	exec_cmd(cmd)


def get_dylib_ext():
	return distutils.ccompiler.new_compiler().shared_lib_extension


def usage():
	print('usage: run_test.py [path to test] - supports wildcards')
	exit(1)


def execute_path(path: str):
	print('given path: '+path)

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
			test_module.cleanup(tests_root_path, get_dylib_ext())
		finally:
			os.chdir(cur_dir)


def main():
	if len(sys.argv) != 2:
		usage()

	try:
		execute_path(sys.argv[1])
		exit(0)
	except Exception as e:
		print('Exception running test:')
		print(e)
		exit(2)


if __name__ == '__main__':
	sys.path.append(os.getcwd())
	main()
