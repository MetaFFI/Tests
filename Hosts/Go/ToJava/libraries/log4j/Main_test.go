package sanity

import (
	logger "GoToJava/logger"
	log4jclass "GoToJava/log4jclass"
	"fmt"
	"os"
	"runtime"
	"testing"

	metaffi "github.com/MetaFFI/lang-plugin-go/go-runtime"
)

func trace(s string) {
	pc := make([]uintptr, 10) // at least 1 entry needed
	runtime.Callers(2, pc)
	f := runtime.FuncForPC(pc[0])
	file, line := f.FileLine(pc[0])
	fmt.Printf("+++ (%v) %s:%d %s\n", s, file, line, f.Name())
}

func getDynamicLibSuffix() string {
	switch runtime.GOOS {
	case "windows":
		return ".dll"
	case "darwin":
		return ".dylib"
	default: // We might need to make this more specific in the future
		return ".so"
	}
}

func TestMain(m *testing.M) {
	p, err := os.Getwd()
	if err != nil {
		panic(err)
	}

	logger.MetaFFILoad(fmt.Sprintf("%v/Logger_MetaFFIGuest%v;%v/TestFuncs_MetaFFIGuest.jar", p, getDynamicLibSuffix(), p))
	log4jclass.MetaFFILoad(fmt.Sprintf("%v/Log4jClass_MetaFFIGuest%v;%v/TestMap_MetaFFIGuest.jar", p, getDynamicLibSuffix(), p))
	exitVal := m.Run()
	os.Exit(exitVal)
}

// --------------------------------------------------------------------
func TestHelloWorld(t *testing.T) {

	logobj, err := log4jclass.NewLog4jClass()
	if err != nil{
		t.Fatal(err)
	}

	loggerHandle, err := logobj.Log4jClass_Getlogger_MetaFFIGetter()
	l4j := &logger.Logger{}
	l4j.SetHandle(loggerHandle.(metaffi.MetaFFIHandle))

	l4j.Trace
}

//--------------------------------------------------------------------
