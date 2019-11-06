"""
Plain python examples of generator constructs,
a selection usable with micropython `machine` module.
The goal is to build pipes.
"""

import itertools
import time
import sys

# 1:1 pipe - basic and not factorized
g = (i for i in range(5))
for value in g:
    sys.stdout.write('Pipe 1:1 - Generator value -> %s' % value)
    value /= 10  # modify
    sys.stdout.write(' modify -> %s' % (value))
    if 0.2 <= value <= 0.3:  # filter
        sys.stdout.write(' filter -> %s' % (value))
    sys.stdout.write('\n')

# 1:1 pipe - with functions
modify = lambda g: (value / 10 for value in g)
filter = lambda g: (value for value in g if 0.2 <= value <= 0.3)
display = lambda g: (print('Pipe 1:1 - Pipe output value: %s' % value) for value in g)
pipe = lambda g: display(filter(modify(g)))
g = (i for i in range(5))
for _ in pipe(g):
    pass

# n:1 pipe - roundrobin 2 generators (zip, not itertools.chain)
g1 = (i for i in range(5))
g2 = (i+10 for i in range(5))
generators = (g1, g2)
for value in itertools.chain.from_iterable(zip(*generators)):
    print('Pipe n:1 - Roundrobin-ed generators iteration value %s' % (value))

# n:1 pipe - zip 2 generators (zip, not itertools.chain)
g1 = (i for i in range(5))
g2 = (i+10 for i in range(5))
generators = (g1, g2)
for values in zip(*generators):
    value = sum(values) / len(values)
    print('Pipe n:1 - Zip-ed generators iteration values %s average -> %s' % (values, value))

# 1:n pipe - split 1 generator
# - this is not possible: iteration can be done by only 1 consumer
# - we need to fall back to callbacks :(
consumer1 = lambda v: print('Pipe 1:n - Consumer 1 callback value %s' % value)
consumer2 = lambda v: print('Pipe 1:n - Consumer 2 callback value %s' % value)
consumers = (consumer1, consumer2)
g = (i for i in range(5))
for value in g:
    for consumer in consumers:
        consumer(value)

# Pipe consumption timing - consumer gives tempo
g = (i for i in range(5))
for value in g:
    time.sleep(0.5)
    print('Consumed value at %.1f after sleeping: %s' % (time.time(), value))

# Pipe consumption timing - producer gives tempo
def g():
    for i in range(5):
        time.sleep(0.5)
        yield i
for value in g():
    print('Consumed value at %.1f after waiting on producer: %s' % (time.time(), value))

# Pipe consumption timing - middle pipe element gives tempo
g = (i for i in range(5))
def middle(g):
    for value in g:
        time.sleep(0.5)
        yield value
for value in middle(g):
    print('Consumed value at %.1f after waiting on middle pipe element: %s' % (time.time(), value))

# Endless iteration
sys.stdout.write('Infinite generator iteration (press ^C to stop): ')
for value in itertools.cycle(range(3)):
    sys.stdout.write(str(value))
    sys.stdout.flush()
    time.sleep(0.5)
    sys.stdout.write(', ')
