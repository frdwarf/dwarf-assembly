#!/usr/bin/env python3

import re
import sys

line = input()
regex = \
    re.compile(r'Total unwind time: ([0-9]*) s ([0-9]*) ns, ([0-9]*) calls')

match = regex.match(line.strip())
if not match:
    print('Badly formatted line', file=sys.stderr)
    sys.exit(1)

sec = int(match.group(1))
ns = int(match.group(2))
calls = int(match.group(3))

time = sec * 10**9 + ns

print("{} & {} & {} & ??".format(calls, time, time // calls))
