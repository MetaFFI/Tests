package sanity;

import openffi.*;

public class Main_test
{
	private static Test t = null;
	public static void main(String[] args)
	{
		try
		{
			t = new Test();

			testHelloWorld();
			testReturnsAnError();
			testDivIntegers();
			testJoinStrings();
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
}