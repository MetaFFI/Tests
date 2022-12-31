package sanity;

import metaffi_host.*;

public class Main_test
{
	private static metaffi_host.go t = null;
	public static void main(String[] args)
	{
		try
		{

			metaffi_host.go.load("TestFuncs_MetaFFIGuest");
			t = new metaffi_host.go();

			testHelloWorld();
			testReturnsAnError();
			testDivIntegers();
			testJoinStrings();
			testWaitABit();
		}
		catch(Exception e)
		{
			System.out.println("Unexpected exception has occurred during tests");
			e.printStackTrace();
			System.exit(1);
		}
	}

	private static void testHelloWorld() throws Exception
	{
		t.HelloWorld();
	}

	private static void testReturnsAnError() throws Exception
	{
		try
		{
			t.ReturnsAnError();
			System.out.println("Test should have failed");
			System.exit(1);
		}
		catch(Exception e)
		{
			if(!e.getMessage().equals("Panic in Go function. Panic Data: An error from ReturnsAnError"))
			{
				System.out.println("Unexpected error message.\nExpected: Panic in Go function. Panic Data: An error from ReturnsAnError\nReceived: "+e.getMessage());
				System.exit(1);
			}
		}
	}

	private static void testDivIntegers() throws Exception
	{
		float res = t.DivIntegers(1, 2);
        if(res != 0.5)
        {
            System.out.println("Expected 0.5, got: "+res);
            System.exit(1);
        }

        try
        {
            t.DivIntegers(1, 0);
            System.out.println("Expected an error - divisor is 0");
            System.exit(1);
        }
        catch(Exception e)
        {
            if(!e.getMessage().equals("Panic in Go function. Panic Data: Divisor is 0"))
            {
                System.out.println("Unexpected error message.\nExpected: Panic in Go function. Panic Data: Divisor is 0\nReceived: "+e.getMessage());
                System.exit(1);
            }
        }
	}

	private static void testJoinStrings() throws Exception
	{
		String res = t.JoinStrings(new String[]{"A","b","C"});
    	if(!res.equals("A,b,C"))
    	{
    	    System.out.println("Expected A,b,C. Got: "+res);
    	    System.exit(1);
    	}
	}

	private static void testWaitABit() throws Exception
	{
		t.WaitABit(t.GetFiveSeconds());
	}

	private static void testTestMap() throws Exception
    {
        metaffi_host.TestMap m = new metaffi_host.TestMap();
        m.Set("one", 1);

        int one = (int)m.Get("one");
        if(one != 1)
        {
            System.out.printf("Expected one=1. one=%d\n", one);
            System.exit(1);
        }

        m.SetName("TheMap!");
        String name = m.GetName();
        if(!name.equals("TheMap!"))
        {
            System.out.printf("Expected name=TheMap!. name=%s\n", name);
            System.exit(1);
        }
    }
}