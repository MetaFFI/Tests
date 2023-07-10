package builtins;

import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args) throws metaffi.MetaFFIException
	{
		metaffi_host.builtins.metaffi_load("builtins_MetaFFIGuest");

		var pydict = new metaffi_host.dict();
        pydict.__setitem__("four", 4);
        pydict.__setitem__("test", "test");

        Object str = pydict.__getitem__("test");
        Object i = pydict.__getitem__("four");

        if( !((String)str).equals("test") )
        {
            System.out.printf("Popped string from deque is not the text \"test\", but: %s", str);
            System.exit(1);
        }

        if( (long)i != 4 )
        {
            System.out.printf("Popped integer from deque is not the 4, but: %d", i);
            System.exit(1);
        }

        System.out.println(str);
        System.out.println(i);
	}
}