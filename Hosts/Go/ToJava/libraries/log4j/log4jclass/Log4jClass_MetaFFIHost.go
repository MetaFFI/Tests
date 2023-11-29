
// Code generated by MetaFFI. DO NOT EDIT.
// Host code for Log4jClass.java
package Log4jClass

import "fmt"
import "unsafe"
import . "github.com/MetaFFI/lang-plugin-go/go-runtime"



// function IDs








var Log4jClass_Getlogger_id unsafe.Pointer




var Log4jClass_Log4jClass_id unsafe.Pointer


var Log4jClass_ReleaseLog4jClass_id unsafe.Pointer




func MetaFFILoad(modulePath string){
	LoadCDTCAPI()

	runtimePlugin := "xllr.openjdk"
	err := XLLRLoadRuntimePlugin(runtimePlugin)
	if err != nil{
		panic(err)
	}

	// load functions
	loadFF := func(modulePath string, fpath string, paramsCount int8, retvalCount int8) unsafe.Pointer{
		id, err := XLLRLoadFunction(runtimePlugin, modulePath, fpath, nil, paramsCount, retvalCount)
		if err != nil{ // failed
			panic(err)
		}

		return id
	}

	
	

	

	
	
	Log4jClass_Getlogger_id = loadFF(modulePath, `entrypoint_class=Log4jClass_Entrypoints,entrypoint_function=EntryPoint_Log4jClass_get_Getlogger,metaffi_guest_lib=Log4jClass_MetaFFIGuest,module=C:\src\github.com\MetaFFI\Tests\Hosts\Go\ToJava\libraries\log4j\Log4jClass,package=log4j`, 0, 1)
	
	
	
	
	Log4jClass_Log4jClass_id = loadFF(modulePath, `entrypoint_class=Log4jClass_Entrypoints,entrypoint_function=EntryPoint_Log4jClass_Log4jClass,metaffi_guest_lib=Log4jClass_MetaFFIGuest,module=C:\src\github.com\MetaFFI\Tests\Hosts\Go\ToJava\libraries\log4j\Log4jClass,package=log4j`, 0, 1)
	
	
	Log4jClass_ReleaseLog4jClass_id = loadFF(modulePath, `entrypoint_class=Log4jClass_Entrypoints,entrypoint_function=EntryPoint_Log4jClass_ReleaseLog4jClass,metaffi_guest_lib=Log4jClass_MetaFFIGuest,module=C:\src\github.com\MetaFFI\Tests\Hosts\Go\ToJava\libraries\log4j\Log4jClass,package=log4j`, 1, 0)
	
	
	
}

func Free(){
	err := XLLRFreeRuntimePlugin("xllr.openjdk")
	if err != nil{ panic(err) }
}









// Code to call foreign functions in module Log4jClass via XLLR



type Log4jClass struct{
	h Handle
}


func NewLog4jClass() (instance *Log4jClass, err error){
	

	xcall_params, _, return_valuesCDTS := XLLRAllocCDTSBuffer(0, 1)

	
	// parameters
	

		err = XLLRXCallNoParamsRet(Log4jClass_Log4jClass_id, xcall_params)  // call function pointer Log4jClass_Log4jClass_id via XLLR
	
	// check errors
	if err != nil{
		err = fmt.Errorf("Failed calling functionLog4jClass.Log4jClass. Error: %v", err)
		return
	}

	
	inst := &Log4jClass{}

	
	instanceAsInterface := FromCDTToGo(return_valuesCDTS, 0)
	if instanceAsInterface != nil{
		inst.h = instanceAsInterface.(Handle)
	} else {
		return nil, fmt.Errorf("Object creation returned nil")
	}
		
	

	return inst, nil	
}


func (this *Log4jClass) GetHandle() Handle{
	return this.h
}

func (this *Log4jClass) SetHandle(h Handle){
	this.h = h
}



func  Log4jClass_Getlogger_MetaFFIGetter() (logger interface{}, err error){
	
	

	xcall_params, _, return_valuesCDTS := XLLRAllocCDTSBuffer(0, 1)

	
	// get parameters
	
	 
	 


		err = XLLRXCallNoParamsRet(Log4jClass_Getlogger_id, xcall_params)  // call function pointer Log4jClass_Getlogger_id via XLLR
	
	// check errors
	if err != nil{
		err = fmt.Errorf("Failed calling functionLog4jClass.Getlogger. Error: %v", err)
		return
	}

	
	
	loggerAsInterface := FromCDTToGo(return_valuesCDTS, 0)
	if loggerAsInterface != nil{
		 
		// handle
		
		if obj, ok := loggerAsInterface.(Handle); ok{ // None Go object			
			logger = obj
		} else {
			logger = interface{}(loggerAsInterface.(interface{}))
		}
		

		
	}

	

	return logger, nil	
}





func (this *Log4jClass) ReleaseLog4jClass( this_instance interface{}) ( err error){
	
	xcall_params, parametersCDTS, _ := XLLRAllocCDTSBuffer(1, 0)

	
	// parameters
	FromGoToCDT(this.h, parametersCDTS, 0) // object
	

		err = XLLRXCallParamsNoRet(Log4jClass_ReleaseLog4jClass_id, xcall_params)  // call function pointer Log4jClass_ReleaseLog4jClass_id via XLLR
	
	// check errors
	if err != nil{
		err = fmt.Errorf("Failed calling functionLog4jClass.ReleaseLog4jClass. Error: %v", err)
		return
	}

	
	

	return  nil
}




