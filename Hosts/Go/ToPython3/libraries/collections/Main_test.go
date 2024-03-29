package main

import (
	"fmt"
	"os"
	. "test/collections"
	"testing"
	metaffi "github.com/MetaFFI/lang-plugin-go/go-runtime"
)

func TestMain(m *testing.M) {

	MetaFFILoad("collections_MetaFFIGuest")

	exitVal := m.Run()

	os.Exit(exitVal)
}

func TestDeque(t *testing.T) {

	list1, err := NewUserList(nil)
	if err != nil {
        t.Fatalf("%v", err)
    }

	dq, err := NewDeque(list1.GetHandle(), nil)
	if err != nil {
		t.Fatalf("Failed to create Deque: %v", err)
	}

	list2, err := NewUserList(nil)
	if err != nil {
        t.Fatalf("%v", err)
    }

	innerDeque, err := NewDeque(list2.GetHandle(), nil)
	if err != nil {
		t.Fatalf("Failed to create inner Deque: %v", err)
	}

	err = innerDeque.Append(100)
	if err != nil {
		t.Fatalf("Failed to append: %v", err)
	}

	// create []int to place in deque
	arrayOfInts := make([]int, 0)
	arrayOfInts = append(arrayOfInts, 1, 2, 3)

	// create User (go object) to place in deque
	user := User{Name: "Tom"}

	// deque
	err = dq.Append(user)
	if err != nil {
		t.Fatalf("Failed to append: %v", err)
	}

	err = dq.Append(innerDeque)
	if err != nil {
		t.Fatalf("Failed to append: %v", err)
	}

	err = dq.Append(1)
	if err != nil {
		t.Fatalf("Failed to append: %v", err)
	}

	err = dq.Append("two")
	if err != nil {
		t.Fatalf("Failed to append: %v", err)
	}

	err = dq.Append(3.5)
	if err != nil {
		t.Fatalf("Failed to append: %v", err)
	}

	err = dq.Append(arrayOfInts)
	if err != nil {
		t.Fatalf("Failed to append: %v", err)
	}

	x, err := dq.Pop()
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}

	l := UserList{}
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

	x, err = dq.Pop()
	fmt.Printf("%v\n", x)
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}
	if x.(float64) != 3.5 {
		t.Fatalf("x != 3.5")
	}

	x, err = dq.Pop()
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(string) != "two" {
		t.Fatalf("x != two")
	}

	x, err = dq.Pop()
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(int64) != 1 {
		t.Fatalf("x != 1")
	}

	poppedInnerDeque, err := dq.Pop()
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}
	x, err = (poppedInnerDeque.(*Deque)).Pop()
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}
	fmt.Printf("%v\n", x)
	if x.(int64) != 100 {
		t.Fatalf("inner deque x != 100")
	}

	x, err = dq.Pop()
	if err != nil {
		t.Fatalf("Failed to Pop: %v", err)
	}
	poppedUser := x.(User)
	poppedUser.SayMyName()
}
