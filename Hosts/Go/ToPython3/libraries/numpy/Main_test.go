package main

import (
	"fmt"
	metaffi "github.com/MetaFFI/lang-plugin-go/go-runtime"
	"os"
	"test/metaffi_objects"
	"test/numpy"
	"testing"
)

func TestMain(m *testing.M) {

	numpy.MetaFFILoad("numpy_MetaFFIGuest")
	metaffi_objects.MetaFFILoad("metaffi_objects_MetaFFIGuest")

	exitVal := m.Run()

	os.Exit(exitVal)
}

func TestNumpy(t *testing.T) {

	/*
		# Create a 1D array
	    arr = np.array([1, 2, 3, 4, 5])

	    # Perform element-wise addition
	    arr = arr + 1

	    # Calculate the mean of the array
	    mean = np.mean(arr)

	    print(f"Array: {arr}")
	    print(f"Mean: {mean}")
	*/

	arr := make([]int64, 0)
	arr = append(arr, 1, 2, 3, 4, 5)
	varargs, err := metaffi_objects.NewMetaffi_Positional_Args()
	if err != nil {
		t.Fatal(err)
	}

	err = varargs.Set_Arg(arr)
	if err != nil {
		t.Fatal(err)
	}

	kwargs, err := metaffi_objects.NewMetaffi_Keyword_Args()

	arrayHandle, err := numpy.Array(varargs.GetHandle(), kwargs.GetHandle())
	if err != nil {
		t.Fatal(err)
	}

	numpyArr := numpy.Ndarray{}
	numpyArr.SetHandle(arrayHandle.(metaffi.Handle))

	mean, err := numpy.Mean1(arrayHandle.(metaffi.Handle))
	if err != nil {
		t.Fatal(err)
	}

	if mean != 3.0 {
		t.Fatalf("Mean should be 3, while it is %v", mean)
	}

	fmt.Printf("Mean: %v\n", mean)

}
