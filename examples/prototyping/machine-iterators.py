"""
Micropython machine examples for interating generators.
The goal is to build pipes.
The goal it to be non-blocking.
"""

import machine
import sys

# re-usable iterators
def poll(pin, f=lambda pin: pin.value()):
    for value in generator:
        yield f(pin)

def normalize(max, generator):
    for value in generator:
        yield value / max

def boolean(threshold, generator):
    for value in generator:
        yield value >= threshold

# 1:1 pipe - read a sensor and update a led
touch = machine.TouchPad(machine.Pin(4))
led = machine.Pin(2)  # onboard led
read = lambda g: (value for value in g)
actor = lambda g: (led.on() if value else led.off() for value in g)
pipe = boolean(threshold=0.3, normalize(max=1023, poll(touch)))
sys.stdout.write('Pipe 1:1 iterating (press ^C to continue)')
for _ in pipe:
    sys.stdout.write('.')
print()

# n:1 pipe - read 2 sensors, average values and update a led
