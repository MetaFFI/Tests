package numpy;

import metaffi.MetaFFIHandle;
import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args) throws Exception
	{
		numpy.metaffi_load("numpy_MetaFFIGuest");
    	metaffi_objects.metaffi_load("metaffi_objects_MetaFFIGuest");

		var input = new Integer[]{1,2,3,4,5};
        var varargs = new metaffi_positional_args();
        varargs.set_arg(input);
		var numpyArray = new ndarray((MetaFFIHandle)numpy.array(varargs.getHandle()));
		var m = numpy.mean(numpyArray.getHandle());

        if((double)m != 3.0)
        {
	        throw new Exception(String.format("Expected mean 3.0, got %f", m));
        }
	}
}