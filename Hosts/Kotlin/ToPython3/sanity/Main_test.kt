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
	t.hello_world();
}

fun testReturnsAnError()
{
	try
	{
		t.returns_an_error();
		System.out.println("Test should have failed");
		System.exit(1);
	}
	catch(e: Exception)
	{
		var msg = e.message as String;
		if(!msg.contains("Exception: Error"))
		{
			System.out.println("Unexpected error message.\nExpected to contain: Exception: Error\nReceived: "+e.message);
			System.exit(1);
		}
	}
}

fun testDivIntegers()
{
	var res = t.div_integers(1, 2);
    if(res != 0.5f)
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
    catch(e: Exception)
    {
        var msg = e.message as String;
        if(!msg.contains("division by zero"))
        {
            System.out.println("Unexpected error message.\nExpected to contain: division by zero\nReceived: "+e.message);
            System.exit(1);
        }
    }
}

fun testJoinStrings()
{
	var res = t.join_strings(arrayOf("A","b","C"));
    if(!res.equals("A, b, C"))
    {
        System.out.println("Expected A,b,C. Got: "+res);
        System.exit(1);
    }
}
