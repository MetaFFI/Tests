package main

import "fmt"
/*
#include <stdint.h>
void* int64_to_unsafeptr(int64_t p)
{
	return (void*)p;
}
*/
import "C"

func main(){

	deque, _ := Deque()
	innerDeque, _ := Deque()

	Append(innerDeque, 100)

	arrayOfInts := make([]int, 0)
	arrayOfInts = append(arrayOfInts, 1, 2, 3)

	Append(deque, innerDeque)
	Append(deque, 1)
	Append(deque, "two")
	Append(deque, 3.5)
	Append(deque, arrayOfInts)

	x, _ := Pop(deque)
    fmt.Printf("%v\n", x)
    if x.([]int64)[0] != 1 { panic("x[0] != 1") }
    if x.([]int64)[1] != 2 { panic("x[0] != 2") }
    if x.([]int64)[2] != 3 { panic("x[0] != 3") }

    x, _ = Pop(deque)
	fmt.Printf("%v\n", x)
	if x.(float64) != 3.5{ panic("x != 3.5") }

	x, _ = Pop(deque)
	fmt.Printf("%v\n", x)
	if x.(string) != "two"{ panic("x != two") }

	x, _ = Pop(deque)
    if x.(int64) != 1 { panic("x != 1") }

    popedInnerDeque, _ := Pop(deque)
    x, _ = Pop(popedInnerDeque.(handle))
    if x.(int64) != 100 { panic("inner deque x != 100") }
}

