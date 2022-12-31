import unittest
from stringutils_MetaFFIHost import *

load('stringutils_MetaFFIGuest')
class TestSanity(unittest.TestCase):

	def test_diff(self):
		res = IndexOfDifference('ABCDEFG', 'ABCHEFG')
		if res != 3:
			self.fail('Expected 3. Got: '+res)
