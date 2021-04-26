import openffi.*;

var t = Test();

fun main() {
	try
	{
		testHelloWorld();
		testReturnsAnError();
		testDivIntegers();
		testJoinStrings();
	}
	catch(e: Exception)
	{
		System.out.println("Unexpected exception has occurred during tests");
		e.printStackTrace();
		System.exit(1);
	}
}

fun testHelloWorld()
{
	t.HelloWorld();
}

fun testReturnsAnError()
{
	try
	{
		t.ReturnsAnError();
		System.out.println("Test should have failed");
		System.exit(1);
	}
	catch(e: Exception)
	{
		if(!e.message.equals("Panic in Go function. Panic Data: An error from ReturnsAnError"))
		{
			System.out.println("Unexpected error message.\nExpected: Panic in Go function. Panic Data: An error from ReturnsAnError\nReceived: "+e.message);
			System.exit(1);
		}
	}
}

fun testDivIntegers()
{
	var res = t.DivIntegers(1, 2);
    if(res != 0.5f)
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
    catch(e: Exception)
    {
        if(!e.message.equals("Panic in Go function. Panic Data: Divisor is 0"))
        {
            System.out.println("Unexpected error message.\nExpected: Panic in Go function. Panic Data: Divisor is 0\nReceived: "+e.message);
            System.exit(1);
        }
    }
}

fun testJoinStrings()
{
	var res = t.JoinStrings(arrayOf("A","b","C"));
    if(!res.equals("A,b,C"))
    {
        System.out.println("Expected A,b,C. Got: "+res);
        System.exit(1);
    }
}
