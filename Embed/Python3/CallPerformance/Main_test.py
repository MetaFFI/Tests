import unittest
from TestFuncs_MetaFFIHost import *
from datetime import datetime
import ctypes

"""metaffi-block: name=TestFuncs.go

package TestFuncs

import (
	"github.com/edwingeng/deque"
)

type GoDeque struct{
	d deque.Deque
	Name string
}

func DoNothing(){
}

func newGoDeque() *GoDeque{
	return &GoDeque{ 
		d: deque.NewDeque(),
	}
}

func (this *GoDeque) push(v interface{}){
	this.d.PushBack(v)
}

func (this *GoDeque) pop() interface{}{
	return this.d.PopFront()
}

var instance *GoDeque

func NewGoDeque(){
	instance = newGoDeque()
}

func Push(v string){
	instance.push(v)
}

func Pop() int{
	return instance.pop().(int)
}
metaffi-end"""

class GoString(ctypes.Structure):
	_fields_ = [('p', ctypes.c_char_p),
	            ('n', ctypes.c_int)]


class TestCallPerformance(unittest.TestCase):

	def test_call_performance(self):

		guestso = None
		if 'Windows' in platform.system():
			os.environ['path'] += ';' + os.path.join(os.path.abspath('.'))
			guestso = windll.LoadLibrary('TestFuncs_MetaFFIGuest.dll')
		else:
			guestso = CDLL(os.path.join(os.path.abspath('.'), 'TestFuncs_MetaFFIGuest.so'))

		#NewGoDeque()

		#guestso.StartProfiler()
		start = datetime.now()
		for i in range(1000000):
			DoNothing()
		go_time = datetime.now() - start
		print(go_time)
		#guestso.EndProfiler()

		#self.assertTrue(False) #, 'Interop call took more than 10%. Interop time: {} Python time: {}. Percent larger: {}%'.format(go_time, python_time, diff_percent))

		# ------------------------------
		#
		godequedirect = None
		if 'Windows' in platform.system():
			os.environ['path'] += ';' + os.path.join(os.path.abspath('.'))
			godequedirect = windll.LoadLibrary('GoDequeDirect.dll')
		else:
			godequedirect = CDLL(os.path.join(os.path.abspath('.'), 'GoDequeDirect.so'))

		godequedirect.NewGoDeque()

		start = datetime.now()

		for i in range(1000000):
			godequedirect.DoNothing()
			pass
		direct_time = datetime.now() - start
		print(direct_time)

		max_expected_length = direct_time*2

		self.assertTrue(go_time <= max_expected_length, 'Interop call took more than 100%. MetaFFI time: {} Direct FFI time: {}. max expected length: {}'.format(go_time, direct_time, max_expected_length))
