package sanity;

import metaffi_host.*;

public class Main_test
{
	private static metaffi_host.TestFuncs t = null;
	public static void main(String[] args)
	{
		try
		{
			t = new metaffi_host.TestFuncs();

			testHelloWorld();
			testReturnsAnError();
			testDivIntegers();
			testJoinStrings();
			testTestMap();
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
		t.hello_world();
	}

	private static void testReturnsAnError() throws Exception
	{
		try
		{
			t.returns_an_error();
			System.out.println("Test should have failed");
			System.exit(1);
		}
		catch(Exception e)
		{
			if(!e.getMessage().contains("Exception: Error"))
			{
				System.out.println("Unexpected error message.\nExpected to contain: Exception: Error\nReceived: "+e.getMessage());
				System.exit(1);
			}
		}
	}

	private static void testDivIntegers() throws Exception
	{
		double res = t.div_integers(1, 2);
        if(res != 0.5)
        {
            System.out.println("Expected 0.5, got: "+res);
            System.exit(1);
        }

        try
        {
            t.div_integers(1, 0);
            System.out.println("Expected an error - divisor is 0");
            System.exit(1);
        }
        catch(Exception e)
        {
            if(!e.getMessage().contains("division by zero"))
            {
                System.out.println("Unexpected error message.\nExpected to contain: division by zero\nReceived: "+e.getMessage());
                System.exit(1);
            }
        }
	}

	private static void testJoinStrings() throws Exception
	{
		String res = t.join_strings(new String[]{"A","b","C"});
    	if(!res.equals("A,b,C"))
    	{
    	    System.out.println("testJoinStrings Failed - Expected A,b,C. Got: \""+res+"\"");
    	    System.exit(1);
    	}
	}

	private static void testWaitABit() throws Exception
    {
        t.wait_a_bit(t.Getfive_seconds());
    }

	private static void testTestMap() throws Exception
    {
        metaffi_host.testmap m = new metaffi_host.testmap();
        m.set("one", 1);

        long one = (long)m.get("one");
        if(one != 1)
        {
            System.out.printf("Expected one=1. one=%d\n", one);
            System.exit(1);
        }

        m.Setname("TheMap!");
        String name = m.Getname();
        if(!name.equals("TheMap!"))
        {
            System.out.printf("Expected name=TheMap!. name=%s\n", name);
            System.exit(1);
        }
    }
}