package sanity;

import openffi._;

class Main_test; object Main_test
{
	var t: Test = null;
	def main(args: Array[String])
	{
		try
		{
			t = new Test();

			testHelloWorld();
			testReturnsAnError();
			testDivIntegers();
			testJoinStrings();
		}
		catch
		{
			case e: Exception =>
				System.out.println("Unexpected exception has occurred during tests");
				e.printStackTrace();
				System.exit(1);
		}
	}

	def testHelloWorld()
	{
		t.HelloWorld();
	}

	def testReturnsAnError()
	{
		try
		{
			t.ReturnsAnError();
			System.out.println("Test should have failed");
			System.exit(1);
		}
		catch
		{
			case e: Exception =>
				if(!e.getMessage().equals("Panic in Go function. Panic Data: An error from ReturnsAnError"))
				{
					System.out.println("Unexpected error message.\nExpected: Panic in Go function. Panic Data: An error from ReturnsAnError\nReceived: "+e.getMessage());
					System.exit(1);
				}
		}
	}

	def testDivIntegers()
	{
		var res = t.DivIntegers(1, 2);
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
        catch
        {
            case e: Exception =>
	            if(!e.getMessage().equals("Panic in Go function. Panic Data: Divisor is 0"))
	            {
	                System.out.println("Unexpected error message.\nExpected: Panic in Go function. Panic Data: Divisor is 0\nReceived: "+e.getMessage());
	                System.exit(1);
	            }
        }
	}

	def testJoinStrings()
	{
		var res = t.JoinStrings(Array("A","b","C"));
    	if(!res.equals("A,b,C"))
    	{
    	    System.out.println("Expected A,b,C. Got: "+res);
    	    System.exit(1);
    	}
	}
}