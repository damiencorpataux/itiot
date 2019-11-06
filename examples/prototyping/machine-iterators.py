"""
Micropython machine examples for interating generators.
The goal is to build pipes.
The goal it to be non-blocking.
"""

import machine
import time
import sys

# Generic generators

def poll(pin, f=lambda pin: pin.value()):
    """
    Generate values by polling an object using function `f`.
    """
    for value in generator:
        yield f(pin)

def normalize(g, max):
    """
    Normalize value in range `min`..`max` to the range 0..1.
    """
    for value in generator:
        yield value / max

def boolean(g, threshold):
    """
    Convert a value to boolean.
    """
    for value in generator:
        yield value >= threshold

def consume(g, period=0.2):
    """
    Iterate a generator (blocking !).
    # FIXME: this is blocking: use a machine.Timer or threading ?
    """
    sys.stdout.write('Consuming pipe (press ^C to stop)')
    try:
        for value in pipe:
            sys.stdout.write(str(value))
            time.sleep(period)
            sys.stdout.write(', ')
    except KeyboardInterrupt:
        print('\nInterrupted by keyboard.')

# Examples

def ex1():
    """
    Pipe 1:1 - read 1 sensor and update 1 led.
    """
    print(__doc__)
    touch = machine.TouchPad(machine.Pin(4))
    led = machine.Pin(2)  # onboard led

    update = lambda pin, g: (pin.on() if value else pin.off() for value in g)
    pipe = update(led, boolean(threshold=0.3, g=normalize(max=1023, g=poll(touch))))
    consume(pipe)

def ex2():
    """
    Pipe 1:1 reuse - read 3 sensors and update 3 leds, using the same pipe definition.
    """
    print(__doc__)
    update = lambda pin, g: (pin.duty(value*1023) for value in g)
    pipe = lambda pin, sensor: update(pin, g=normalize(max=1023, g=poll(sensor)))

    touches = (machine.TouchPad(machine.Pin(n)) for n in (13, 12, 14))
    leds = (machine.TouchPad(machine.Pin(n)) for n in (5, 18, 19))
    pipes = (pipe(leds[i], touches[i]) for i in range(len(touches)))
    # for pipe in pipes:
    #     consume(pipe) # FIXME: this is blocking: use a machine.Timer or threading ?
    for pipe in pipes:
        for _ in pipe:
            pass  # FIXME: if one element of the pipe blocks, then everything blocks.

def ex3():
    """
    Pipe n:1 - read 2 sensors and update 1 led with average value.
    """
    pass

def ex4():
    """
    Pipe 1:n - read 1 sensor and update 2 leds, inverting value for 1 of the 2 leds.
    """
    pass
