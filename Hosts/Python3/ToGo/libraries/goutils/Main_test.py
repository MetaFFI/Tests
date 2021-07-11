import unittest
from Test_OpenFFIHost import *

class TestSanity(unittest.TestCase):

	def test_initials(self):
		res = Initials('James Tiberius Kirk')
		if res != 'JTK':
			self.fail('Expected JTK. Got: '+res)
