import unittest
from TestFuncs_MetaFFIHost import *
import collections
from datetime import datetime


"""metaffi-block: name=TestFuncs.go

package TestFuncs

import (
	"github.com/edwingeng/deque"
)

func HelloWorld() {
	println("Hello World, From Go!")
}

type GoDeque struct{
	d deque.Deque
	Name string
}

func NewGoDeque() *GoDeque{
	return &GoDeque{ 
		d: deque.NewDeque(),
	}
}

func (this *GoDeque) Push(v interface{}){
	this.d.PushBack(v)
}

func (this *GoDeque) Pop() interface{}{
	return this.d.PopFront()
}
metaffi-end"""


if __name__ == '__main__':
	HelloWorld()

	d = GoDeque()
	d.Push(250)
	d.Push(['test', 'me'])

	deq = collections.deque()
	deq.append(600)
	d.Push(deq)

	print(d.Pop())
	print(d.Pop())
	print(d.Pop())

	d.SetName('GoDeque')
	print(d.GetName())


		
