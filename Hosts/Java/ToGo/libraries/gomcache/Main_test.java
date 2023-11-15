package gomcache;

import metaffi_host.*;
import metaffi.*;

public class Main_test
{
	public static void main(String[] args)
	{
		int errorCode = 0;

		try
		{
			metaffi_host.mcache.metaffi_load("mcache_MetaFFIGuest");

			/*
			INFINITY = GetTTL_FOREVER_metaffi_getter()

            mcache = CacheDriver()
            mcache.obj_handle = New()

            mcache.Set('integer', 101, INFINITY)
            l = mcache.Len()
            print('length: {}'.format(l))
            x, found = mcache.Get('integer')

            if x != 101:
                self.fail("x expected to be 101, while it is"+str(x))

            print(x)
			*/

			var INFINITY = metaffi_host.mcache.GetTTL_FOREVER_MetaFFIGetter();
			var mc = new metaffi_host.CacheDriver((metaffi.MetaFFIHandle)metaffi_host.mcache.New());

			mc.Set("integer", 101, INFINITY);
			var l = mc.Len();
			System.out.println(String.format("length: %d", l));
			var x = mc.Get("integer");

			if(!x.r1){
				throw new Exception(String.format("the key \"integer\" was not found"));
			}

			if((int)x.r0 != 101){
				throw new Exception(String.format("x expected to be 101, while it is %d", x));
			}

			System.out.println("Done");
		}
		catch(Exception e)
		{
			System.out.println("Unexpected exception has occurred during tests");
			e.printStackTrace();
			System.exit(1);
		}

	}
}