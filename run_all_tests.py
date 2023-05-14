import run_test
import sys
import os

def main():
	try:
		run_test.execute_path('./Hosts/Go/ToPython3/sanity')
		run_test.execute_path('./Hosts/Go/ToPython3/libraries/deque')
		run_test.execute_path('./Hosts/Go/ToPython3/libraries/python-string-utils')
		run_test.execute_path('./Hosts/Go/ToJava/sanity')
		run_test.execute_path('./Hosts/Python3/ToGo/sanity')
		run_test.execute_path('./Hosts/Python3/ToGo/libraries/go-mcache')
		run_test.execute_path('./Hosts/Python3/ToJava/sanity')
		run_test.execute_path('./Hosts/Java/ToPython3/sanity')
		run_test.execute_path('./Hosts/Java/ToGo/sanity')
		run_test.execute_path('./Hosts/Java/ToPython3/libraries/python_string_utils')
	except Exception as e:
		print('Exception running test:')
		print(e)
		exit(2)


if __name__ == '__main__':
	sys.path.append(os.getcwd())
	main()
