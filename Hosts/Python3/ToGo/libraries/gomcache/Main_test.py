import unittest
import time
from mcache_MetaFFIHost import *

metaffi_load('mcache_MetaFFIGuest')
class TestSanity(unittest.TestCase):

	def test_mcache(self):

		INFINITY = GetTTL_FOREVER_metaffi_getter()

		mcache = CacheDriver()
		mcache.obj_handle = New()

		mcache.Set('integer', 101, INFINITY)
		l = mcache.Len()
		print('length: {}'.format(l))
		x, found = mcache.Get('integer')

		if x != 101:
			self.fail("x expected to be 101, while it is"+str(x))
			
		print(x)
