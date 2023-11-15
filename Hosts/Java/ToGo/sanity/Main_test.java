package sanity;

import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args)
	{
		int errorCode = 0;

		try
		{
			TestFuncs.metaffi_load("TestFuncs_MetaFFIGuest");

			System.out.println("Calling HelloWorld");
			testHelloWorld();
			System.out.println("Calling ReturnsAnError");
			testReturnsAnError();
			System.out.println("Calling DivIntegers");
			testDivIntegers();
			System.out.println("Calling JoinStrings");
			testJoinStrings();
			System.out.println("Calling WaitABit");
			testWaitABit();
			System.out.println("Calling TestMap");
			testTestMap();
			System.out.println("Done Tests");
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
		TestFuncs.HelloWorld();
	}

	private static void testReturnsAnError() throws Exception
	{
		try
		{
			System.out.println("Calling testReturnsAnError");
			TestFuncs.ReturnsAnError();
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
		float res = TestFuncs.DivIntegers(1, 2);
        if(res != 0.5)
        {
            System.out.println("Expected 0.5, got: "+res);
            System.exit(1);
        }

        try
        {
			TestFuncs.DivIntegers(1, 0);
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
		String res = TestFuncs.JoinStrings(new String[]{"A","b","C"});
    	if(!res.equals("A,b,C"))
    	{
    	    System.out.println("Expected A,b,C. Got: "+res);
    	    System.exit(1);
    	}
	}

	private static void testWaitABit() throws Exception
	{
		TestFuncs.WaitABit(TestFuncs.GetFiveSeconds_MetaFFIGetter());
	}

	private static void testTestMap() throws Exception
    {
        TestMap m = new TestMap((metaffi.MetaFFIHandle)TestFuncs.NewTestMap());
        m.Set("one", 1);

        int one = (int)m.Get("one");
        if(one != 1)
        {
            System.out.printf("Expected one=1. one=%d\n", one);
            System.exit(1);
        }

        m.SetName_MetaFFISetter("TheMap!");
        String name = m.GetName_MetaFFIGetter();
        if(!name.equals("TheMap!"))
        {
            System.out.printf("Expected name=TheMap!. name=%s\n", name);
            System.exit(1);
        }
    }
}