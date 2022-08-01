package main

// #include <stdint.h>
import "C"
import "github.com/edwingeng/deque"
import "fmt"

type Student struct{
	Name string
}

type GoDeque struct{
	d deque.Deque
	Name string
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

//-----

var instance *GoDeque

func panicHandler(out_err **C.char, out_err_len *C.uint64_t){
	if rec := recover(); rec != nil{
		msg := "Panic in Go function. Panic Data: "
		switch recType := rec.(type){
			case error: msg += (rec.(error)).Error()
			case string: msg += rec.(string)
			default: msg += fmt.Sprintf("Panic with type: %v - %v", recType, rec)
		}

		*out_err = C.CString(msg)
		*out_err_len = C.uint64_t(len(msg))
	}
}

//export DoNothing
func DoNothing(){

	var out_err **C.char
	var out_err_len *C.uint64_t
	defer panicHandler(out_err, out_err_len)

}

//export NewGoDeque
func NewGoDeque(){
	instance = newGoDeque()
}

//export Push
func Push(v string){
	instance.push(v)
}

//export Pop
func Pop() int{
	return instance.pop().(int)
}

func main(){}