package pythonStringUtils

import (
	"fmt"
	"testing"
	"pythonStringUtils/manipulation"
	"pythonStringUtils/validation"
)

func TestMain(t *testing.T){

	manipulation.Load("manipulation_MetaFFIGuest")
    validation.Load("validation_MetaFFIGuest")
	//defer manipulation.Free()

	isJson, err := validation.IsJson("[1, 2, 3")
	if err != nil{ t.Fatal(err) }
	fmt.Printf("[1, 2, 3? %v\n", isJson)

	isJson, err = validation.IsJson(`{ "a": 1 }`)
	if err != nil{ t.Fatal(err) }
    fmt.Printf("{ \"a\": 1 }? %v\n", isJson)

	stripped, err := manipulation.StripHtml(`"test: <a href="foo/bar">click here</a>"`, true)
	if err != nil{ t.Fatal(err) }

	fmt.Printf("Before: %v\n", `"test: <a href="foo/bar">click here</a>"`)
	fmt.Printf("After: %v\n", stripped)
}

