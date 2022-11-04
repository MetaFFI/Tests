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
    	    System.out.println("Expected A,b,C. Got: "+res);
    	    System.exit(1);
    	}
	}

	private static void testTestMap() throws Exception
    {
        var testmap = new metaffi_host.testmap();
        testmap.set("k1", "v1");
        Object v1 = testmap.get("k1");
        if(!(v1 instanceof String))
        {
            System.out.println("Expected returned type String. Got: "+v1.getClass().getSimpleName());
            System.exit(1);
        }

		String v1str = (String)v1;
        if(!"v1".equals(v1str))
        {
            System.out.println("Expected returned String \"v1\". Got: "+v1str);
            System.exit(1);
        }
    }
}