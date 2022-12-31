import unittest
from TestFuncs_MetaFFIHost import *
from datetime import datetime
import ctypes

"""metaffi-block: name=TestFuncs.go

package TestFuncs

func DoNothing(){
}

metaffi-end"""

class GoString(ctypes.Structure):
	_fields_ = [('p', ctypes.c_char_p),
	            ('n', ctypes.c_int)]


class TestCallPerformance(unittest.TestCase):

	def test_call_performance(self):
		load("TestFuncs_MetaFFIGuest")
		call_times = 1000000

		guestso = None
		if 'Windows' in platform.system():
			os.environ['path'] += ';' + os.path.join(os.path.abspath('.'))
			guestso = windll.LoadLibrary('TestFuncs_MetaFFIGuest.dll')
		else:
			guestso = CDLL(os.path.join(os.path.abspath('.'), 'TestFuncs_MetaFFIGuest.so'))


		#guestso.StartProfiler()

		#guestso.EndProfiler()

		# ------------------------------
		#
		godequedirect = None
		if 'Windows' in platform.system():
			os.environ['path'] += ';' + os.path.join(os.path.abspath('.'))
			godequedirect = windll.LoadLibrary('GoDequeDirect.dll')
		else:
			godequedirect = CDLL(os.path.join(os.path.abspath('.'), 'GoDequeDirect.so'))

		start = datetime.now()
		for i in range(call_times):
			out_error = (c_char_p * 1)(0)
			out_error_len = (c_ulonglong)(0)
			godequedirect.DoNothing(out_error, byref(out_error_len))
			pass
		direct_time = datetime.now() - start

		start = datetime.now()
		for i in range(call_times):
			DoNothing()
		go_time = datetime.now() - start
		print('MetaFFI Time: {}'.format(go_time))
		print('Direct FFI Time: {}'.format(direct_time))

		print('MetaFFI takes more time than FFI Time by {:.2f}%'.format((go_time/direct_time*100)-100))

		max_expected_length = direct_time*1.05

		self.assertTrue(go_time <= max_expected_length, 'Interop larger then direct call by {:.2f}%. MetaFFI time: {} Direct FFI time: {}. max expected length: {} (5%)'.format((go_time/direct_time*100)-100, go_time, direct_time, max_expected_length))
