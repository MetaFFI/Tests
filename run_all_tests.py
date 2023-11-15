import run_test
import sys
import os
import glob


def main():
	testdir = 'No test path'
	try:
		tests = glob.glob('./Hosts/**/run_test.py', recursive=True)
		for testfile in tests:
			testdir = os.path.dirname(testfile)
			run_test.execute_path(testdir)

	except Exception as e:
		print('Exception running test:')
		print(e)
		print('rerun with the command "python3 run_test.py '+testdir+'"')
		exit(2)


if __name__ == '__main__':
	sys.path.append(os.getcwd())
	main()
