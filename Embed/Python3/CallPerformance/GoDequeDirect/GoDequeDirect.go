package main

// #include <stdint.h>
import "C"
import "fmt"

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

func goDoNothing(){

}

//export DoNothing
func DoNothing(out_err **C.char, out_err_len *C.uint64_t){

	goDoNothing()

	defer panicHandler(out_err, out_err_len)

}


func main(){}