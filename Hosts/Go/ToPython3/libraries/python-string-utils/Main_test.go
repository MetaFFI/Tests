package main

import (
	"fmt"
	"testing"
)

func TestMain(t *testing.T){
	isJson, err := Is_json("[1, 2, 3")
	if err != nil{ t.Fatalf(err) }
	fmt.Printf("[1, 2, 3? %v\n", isJson)

	isJson, err = Is_json(`{ "a": 1 }`)
	if err != nil{ t.Fatalf(err) }
    fmt.Printf("{ \"a\": 1 }? %v\n", isJson)

	stripped, err := Strip_html(`"test: <a href="foo/bar">click here</a>"`)
	if err != nil{ t.Fatalf(err) }

	fmt.Printf("Before: %v\n", `"test: <a href="foo/bar">click here</a>"`)
	fmt.Printf("After: %v\n", stripped)
}

