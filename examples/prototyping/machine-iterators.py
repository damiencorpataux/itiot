"""
Micropython machine examples for interating generators.
The goal is to build pipes.
The goal it to be non-blocking.
"""

import machine
import time
# import sys

# Generic generators

def poll(pin, read=lambda pin: pin.read()):
    """
    Generate values by polling an object using function `read`.
    """
    while True:
        yield read(pin)

def debug(g, prefix='Value'):
    for value in g:
        print(prefix, value)
        yield value

def normalize(g, max):
    """
    Normalize value in range `min`..`max` to the range 0..1.
    """
    for value in g:
        yield value / max

def boolean(g, threshold=0.5):
    """
    Convert a value to boolean if value greater than `threshold`.
    """
    for value in g:
        yield value >= threshold

def average(g, n=10, partial=False, history=[]):
    """
    Average the last `n` values,
    waiting to have `n` values before yielding a value if `partial` is True.
    """
    for value in g:
        history = [value] + history[:n-1]  # prepend value and trim to first n elements
        if partial or len(history) >= n:
            yield sum(history) / len(history)

def onchange(g, delta=0.1, absolute=True, lastvalue=None):
    """
    Yield value only when difference with last value is equal or greater than `delta`.
    """
    for value in g:
        difference = value - lastvalue
        if (abs(difference) if absolute else difference) >= abs(delta):
            yield value

def consume(g, period=0.2, value=None):
    """
    Iterate a generator every `period` and return a tuple of
    (the created timer, a generator yielding the last received value)

    In order to be non-blocking, iteration on the returned generator can to be timed with `consume`, eg:
    `consume(period=1, consume(period=0.5, average(machine.Pin(4))))`.
    """
    print('Consuming pipe (press ^C to stop)')
    # try:
    #     for value in pipe:
    #         sys.stdout.write(str(value))
    #         time.sleep(period)
    #         sys.stdout.write(', ')
    # except KeyboardInterrupt:
    #     print('\nInterrupted by keyboard.')
    # Non blocking
    def handler(t):
        value = next(pipe)
    timer = machine.Timer(-1)
    timer.init(callback=handler)
    def g():
        while True:
            yield value
    return timer, g()

# Examples

def ex1():
    """
    Pipe 1:1 - read 1 sensor and update 1 led.
    """
    touch = machine.TouchPad(machine.Pin(4))
    led = machine.Pin(2, machine.Pin.OUT)  # onboard led

    update = lambda pin, g: (pin.on() if value else pin.off() for value in g)
    pipe = update(led, debug(g=boolean(threshold=0.3, g=normalize(max=1023, g=poll(touch)))))

    for _ in pipe:
        pass

def ex1a():
    """
    Pipe 1:1 - read 1 sensor and update 1 led, with average.
    """
    touch = machine.TouchPad(machine.Pin(4))
    led = machine.Pin(2, machine.Pin.OUT)  # onboard led

    update = lambda pin, g: (pin.on() if value else pin.off() for value in g)
    pipe = update(led, debug(g=boolean(threshold=0.3, g=average(n=5, g=normalize(max=1023, g=poll(touch))))))

    for _ in pipe:
        pass

def ex2():
    """
    Pipe 1:1 reuse - read 3 sensors and update 3 leds, using the same pipe definition.
    """
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
    # cf. basic-python-iterators.py
    pass

def ex4():
    """
    Pipe 1:n - read 1 sensor and update 2 leds, inverting value for 1 of the 2 leds.
    """
    # cf. basic-python-iterators.py
    pass

def ex5():
    """
    Pipe 1:1 advances - read 1 sensor continuously at a high rate
    and send information to a REST service.
    """
    import urequests

    # read sensor at high rate
    touch = machine.TouchPad(machine.Pin(4))
    pipe_read = average(touch)
    g = consume(pipe_read, period=0.1)

    # send information to REST service
    publish = lambda g: (urequests.put('http://httpbin.com/anything/somevalue', data=dict(value=value)) for value in g)
    pipe_publish = publish(onchange(g, delta=1))
    g = consume(pipe_publish, period=1)

    """
    # or a one-liner - re-using created pipes
    pipe_read = lambda g: average(g)  # to be reusable, pipes need to be a generator function
    pipe_publish = lambda g: publish(onchange(g, delta=1))
    g = consume(consume(pipe_publish(consume(period=0.1, g=pipe_read(touch)))))

    # or a one-liner - fully declarative oneliner, no pipe reuse
    g = consume(period=1, g=consume(publish(onchange(delta=1, g=consume(period=0.1, g=average(touch))))))
    """

    # optionnally log pipe output
    g = published_values  # it is what is is, actually
    while value in published_values:
        print('Sent REST message:', value)
