package main

import (
	"fmt"
	"os"
	. "test/builtins"
	"testing"
	metaffi "github.com/MetaFFI/lang-plugin-go/go-runtime"
)

func TestMain(m *testing.M) {
	MetaFFILoad("builtins_MetaFFIGuest")

	exitVal := m.Run()

	os.Exit(exitVal)
}

func TestDict(t *testing.T) {

	pydict, err := NewDict1()
	if err != nil {
		t.Fatalf("Failed to create Dict: %v", err)
	}

	innerDict, err := NewDict1()
	if err != nil {
		t.Fatalf("Failed to create inner Dict: %v", err)
	}

	err = innerDict.U___Setitem____("InnerInteger", 100)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	// create []int to place in deque
	arrayOfInts := make([]int, 0)
	arrayOfInts = append(arrayOfInts, 1, 2, 3)

	// create User (go object) to place in deque
	user := User{Name: "Tom"}

	// deque
	err = pydict.U___Setitem____("User", user)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = pydict.U___Setitem____("inner", innerDict)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = pydict.U___Setitem____("Integer", 2)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = pydict.U___Setitem____("String", "two")
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = pydict.U___Setitem____("Float", 3.5)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	err = pydict.U___Setitem____("Array", arrayOfInts)
	if err != nil {
		t.Fatalf("Failed to Setitem: %v", err)
	}

	// Notice, in this scenario, array returns as handle to Python list.
	// as python doesn't have an array, but a "list", which can contain anything, not just int64[]
	// TODO: this should be fixed by supporting array of "any".
	x, err := pydict.U___Getitem____("Array")
	if err != nil {
		t.Fatalf("Failed to GetItem from dictionary: %v", err)
	}

	l := List{}
	l.SetHandle(x.(metaffi.Handle))
	v, err := l.U___Getitem____(0)
	if err != nil {
        t.Fatalf("Failed to GetItem from List: %v", err)
    }

	fmt.Printf("%v\n", v)
	if v.(int64) != 1 {
		t.Fatalf("x[0] != 1")
	}

	v, err = l.U___Getitem____(1)
    if err != nil {
        t.Fatalf("Failed to GetItem from List: %v", err)
    }

    fmt.Printf("%v\n", v)
    if v.(int64) != 2 {
        t.Fatalf("x[1] != 2")
    }

	v, err = l.U___Getitem____(2)
	if err != nil {
        t.Fatalf("Failed to GetItem from List: %v", err)
    }

	fmt.Printf("%v\n", v)
	if v.(int64) != 3 {
		t.Fatalf("x[2] != 3")
	}

	x, err = pydict.U___Getitem____("Float")
	fmt.Printf("%v\n", x)
	if err != nil {
		t.Fatalf("Failed to GetItem Float: %v", err)
	}
	if x.(float64) != 3.5 {
		t.Fatalf("x != 3.5")
	}

	x, err = pydict.U___Getitem____("String")
	if err != nil {
		t.Fatalf("Failed to GetItem String: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(string) != "two" {
		t.Fatalf("x != two")
	}

	x, err = pydict.U___Getitem____("Integer")
	if err != nil {
		t.Fatalf("Failed to GetItem Integer: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(int64) != 2 {
		t.Fatalf("x != 2")
	}

	poppedInnerDict, err := pydict.U___Getitem____("inner")
	if err != nil {
		t.Fatalf("Failed to GetItem inner: %v", err)
	}
	x, err = (poppedInnerDict.(*Dict)).U___Getitem____("InnerInteger")
	if err != nil {
		t.Fatalf("Failed to GetItem InnerInteger: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(int64) != 100 {
		t.Fatalf("inner dict x != 100. x=%v", x.(int64))
	}

	x, err = pydict.U___Getitem____("User")
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}
	poppedUser := x.(User)
	poppedUser.SayMyName()
}
