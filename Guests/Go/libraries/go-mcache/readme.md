Doesn't work as Go as guest is loaded as C-Shared dynamic library, and it does not
support loading Go plugin which holds the objects table.

Need to think of a way to place the objects table in "xllr.go".
One idea that I don't like:

Place objects in global slices and pass to the pointer to xllr.go which will hold them.