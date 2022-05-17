package main

import "github.com/edwingeng/deque"
import "time"
import "fmt"

func main(){
	dq := deque.NewDeque()
	start:=time.Now()
    for i:=0 ; i<10000000 ; i++{
    	dq.PushBack(i)
    }

    for i:=0 ; i<10000000 ; i++{
    	dq.PopFront()
    }
    end:=time.Now()
    fmt.Printf("%v", end.Sub(start).Seconds())
}