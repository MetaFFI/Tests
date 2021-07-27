
def hello_world():
    print('Hello World, from Python3')


def returns_an_error():
    raise Exception('Error')


def div_integers(x, y):
    return x/ y


def join_strings(arr):
	res = ','.join(arr)
	return res


class testmap:
	curdict: dict

	def __init__(self):
		self.curdict = dict()

	def set_key(self, k, v):
		self.curdict[k] = v

	def get_key(self, k):
		return self.curdict[k]

	def contains_key(self, k):
		return self.curdict[k] is not None
