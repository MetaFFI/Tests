import time

def hello_world():
    print('Hello World, from Python3')


def returns_an_error():
    raise Exception('Error')


def div_integers(x, y):
    return x/ y


def join_strings(arr):
	res = ','.join(arr)
	return res

five_seconds = 5
def wait_a_bit(secs):
	time.sleep(secs)
	return None

class testmap:
	name: str
	curdict: dict

	def __init__(self):
		self.curdict = dict()

	def set(self, k, v):
		self.curdict[k] = v

	def get(self, k):
		return self.curdict[k]

	def contains(self, k):
		return self.curdict[k] is not None
