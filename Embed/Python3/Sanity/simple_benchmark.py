from datetime import datetime
from collections import deque

d = deque()
start = datetime.now()
for i in range(0, 10000000):
	d.append(i)

for i in range(0, 10000000):
	d.pop()

print(datetime.now()-start)