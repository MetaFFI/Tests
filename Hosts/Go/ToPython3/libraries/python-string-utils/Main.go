package main

import "fmt"

func main(){
	isJson, _ := Is_json("[1, 2, 3]")
	fmt.Printf("[1, 2, 3]? %v\n", isJson)

	stripped, _ := Strip_html(`"test: <a href="foo/bar">click here</a>"`)
	fmt.Printf("Before: %v\n", `"test: <a href="foo/bar">click here</a>"`)
	fmt.Printf("After: %v\n", stripped)
}

