package main

import (
	"fmt"
	"os"
	. "test/builtins"
	"testing"
)

func TestMain(m *testing.M) {
	Load("builtins_MetaFFIGuest")

	exitVal := m.Run()

	os.Exit(exitVal)
}

func TestDict(t *testing.T) {

	dq, err := NewDict()
	if err != nil {
		t.Fatalf("Failed to create Dict: %v", err)
	}

	innerDict, err := NewDict()
	if err != nil {
		t.Fatalf("Failed to create inner Dict: %v", err)
	}

	err = innerDict.Setitem("InnerInteger", 100)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	// create []int to place in deque
	arrayOfInts := make([]int, 0)
	arrayOfInts = append(arrayOfInts, 1, 2, 3)

	// create User (go object) to place in deque
	user := User{Name: "Tom"}

	// deque
	err = dq.Setitem("User", user)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = dq.Setitem("inner", innerDict)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = dq.Setitem("Integer", 2)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = dq.Setitem("String", "two")
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = dq.Setitem("Float", 3.5)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = dq.Setitem("Array", arrayOfInts)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	x, err := dq.Getitem("Array")
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.([]int64)[0] != 1 {
		t.Fatalf("x[0] != 1")
	}
	if x.([]int64)[1] != 2 {
		t.Fatalf("x[0] != 2")
	}
	if x.([]int64)[2] != 3 {
		t.Fatalf("x[0] != 3")
	}

	x, err = dq.Getitem("Float")
	fmt.Printf("%v\n", x)
	if err != nil {
		t.Fatalf("Failed to GetItem Float: %v", err)
	}
	if x.(float64) != 3.5 {
		t.Fatalf("x != 3.5")
	}

	x, err = dq.Getitem("String")
	if err != nil {
		t.Fatalf("Failed to GetItem String: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(string) != "two" {
		t.Fatalf("x != two")
	}

	x, err = dq.Getitem("Integer")
	if err != nil {
		t.Fatalf("Failed to GetItem Integer: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(int64) != 2 {
		t.Fatalf("x != 2")
	}

	poppedInnerDict, err := dq.Getitem("inner")
	if err != nil {
		t.Fatalf("Failed to GetItem inner: %v", err)
	}
	x, err = (poppedInnerDict.(*Dict)).Getitem("InnerInteger")
	if err != nil {
		t.Fatalf("Failed to GetItem InnerInteger: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(int64) != 100 {
		t.Fatalf("inner dict x != 100. x=%v", x.(int64))
	}

	x, err = dq.Getitem("User")
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}
	poppedUser := x.(User)
	poppedUser.SayMyName()
}