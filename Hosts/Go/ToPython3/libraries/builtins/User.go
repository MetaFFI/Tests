package main

import "fmt"

type User struct{
	Name string
}

func (this *User) SayMyName(){
	fmt.Printf("My name is: %v\n", this.Name)
}

