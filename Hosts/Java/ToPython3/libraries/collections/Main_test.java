package collections;

import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args) throws metaffi.MetaFFIException
	{
		metaffi_host.collections.load("collections_MetaFFIGuest");

		var pydeque = new metaffi_host.deque();
        pydeque.append(4);
        pydeque.append("test");

        Object str = pydeque.pop();
        Object i = pydeque.pop();

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