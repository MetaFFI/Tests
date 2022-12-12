package sanity;
import java.util.HashMap;

public class TestMap
{
	public String name;
	private HashMap<String, Object> map;

	public TestMap()
	{
		map = new HashMap<String, Object>();
		name = "";
	}

	public void set(String k, Object v)
	{
		this.map.put(k, v);
	}

	public Object get(String k)
    {
        return this.map.get(k);
    }

    public boolean contains(String k)
    {
        return this.map.containsKey(k);
    }
}