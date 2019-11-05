"""
Electronic Component abstraction.

WARNING! Python Generators on Steroids ahead.
WARNING! Itergenerateous people out there.

A single file. It's a micropython microframework.
It's all a `Wheel`, and we keep reinvent it.
Now let's iterate IoT.
                                                                      - an itiot
"""

import machine
import logging

# class State(object):  # FIXME: no state class for now: -KISS-
# """
# A state can always boil down to a value.
# """
#     __int__ = lambda self: int(self.state['value'])
#     __float__ = lambda self: float(self.state['value'])
#     __long__ = lambda self: float(self.state['value'])

class Wheel(object):
    """
    Abstract.
    It's an iterator and also a generator, designed to bind things toghether
    and make them run.
    """
    state = {'value': None}  # state MUST have a 'value' key
                             # and it should not start with underscore (_)

    @property
    def o(self):
        """
        Shorthand for `self.options.get`. Example: `self.o('pin', 1)`.
        """
        return self.options.get

    def __init__(self, _state={} **options):
        self.log = logging.getLogger(self.__module__+'+'+self.__class__.__name__)
        self.options = dict({}, **options)  # FIXME: use deepcopy, but it fails on micropython
        self.state = dict(dict({}, Wheel.state), **_state)

    def iterate(self, iterator):
        """
        Process `state` yielded from `iterator`.
        """
        # TODO: implement __iter__ etc.
        for state in iterator:
            self.commit(state)

    def commit(self, state):
        """
        Process `state` and apply result to `state`.
        """
        raise NotImplementedError()

    def states(self):
        """
        Return a generator that yield processed `state`.
        """
        while True:
            yield self.state

class Filter(Wheeé):
    """
    Abstract.
    I/O state processing unit.
    """
    # FIXME: how do I connect the pipes... look at the examples/tutorial.py
    def iterate(self, iterator):
        """
        Process states yielded from `iterator`.
        """
        for state in iterator: # FIXME: output the processed state
            processed = self.process(state, state['value'])  # helper and unification enforcement

    def process(self, state):
        """
        Process the value and update state.
        Most of the filters will return a scalar.
        You can create your own filters to adapt the structure of the values.
        """
        self.state = state  # neutral filter

    def states(self):
        """
        Return a generator that yield processed states.
        """
        while True:
            yield self.state

class average(Filter):

    def __init__(self, size=10, values=[]):
        super().__init__(size=size, values=values)

    def process(self, state, value):
        self.values = [value] + self.values[:self.o('size')-1]  # lifo queue
        if len(self.values) >= self.o('size'):
            self.state = sum(self.values) / len(self.values)

class Device(Wheel):
    """
    Abstract.
    Electronic components abstraction.
    Sensor components are only generators, active components are only iterators.
    """
    unit_name = None  # the <unit_name> is 20 <unit> (<symbol>)
    unit = None       # the temperature is 20 degree Celcius ('C)
    symbol = None     # only ascii characters (eg. 'C), for compatibility with the chaos...

    def __init__(self, **options):
        super().__init__(self, cycle=cycle, **kwargs)
        self.state = dict(dict({}, Device.state), **_state)  # FIXME: not dry with Wheel.__init__, can we get the parent class programmatically ?

    def poll(self):
        """
        Poll device and return a sensible state.
        """
        raise NotImplementedError()

    def read(self):
        """
        Poll device, apply state to device and return updated state.
        See `self.apply`.
        """
        Device.apply(self, **self.poll())
        return self.state

    def apply(self, **state, _commit=True):
        """
        Apply `state` to `self.state`, commit to MCU if `_commit` is not False.
        See `self.commit`.
        """
        if _commit:
            self.commit(**state)
        for key, value in state.items():
            self.state[key] = value

    def commit(self, **state):
        """
        Commit state to physical device (through MCU pins, usually).
        """
        raise NotImplementedError()

    def states(self, limit=10, dry=False):
        """
        Return a generator that yield device states.
        Method `read` is called if `dry` is False, otherwise `poll`.
        """
        # FIX: is there a lag between poll and actual yielding
        # when the consumer sleeps between iterations ?
        if limit:
            for _ in range(limit): yield self.poll() if dry else self.read()
        else:
            while True: yield self.poll() if dry else self.read()

    def iterate(self, iterator, commit=True):
        """
        Apply states yielded from `iterator`.
        """
        for state in iterator:
            self.apply(**state, _commit=commit)

class mock(Wheel):

    def __init__(self, cycle=(0,1), unit_name=None, unit=None, symbol=None, **kwargs):
        import itertools.cycle
        super().__init__(self, cycle=cycle, **kwargs)
        self.symbol = symbol
        self.unit = unit
        self.unit_name = unit_name
        self.cycle = itertools.cycle(self.o('cycle'))

    def poll(self):
        return dict(value=self.cycle.next())

    def apply(self, **state):
        return super().apply(**state)  # any state will do

class led(Wheel):
    unit_name = 'logic level'
    unit = 'binary'
    symbol = '!!'

    def __init__(self, pin=11, **kwargs):
        super().__init__(self, pin=pin, **kwargs)
        self.pin = machine.Pin(self.options['pin'], machine.Pin.OUT)

    def poll(self):
        return dict(value=self.pin.value())  # value 0 or 1 is better than boolean
                                             # for math operations, ie. average
    def commit(self, value):
        if self.value is None:
            pass  # None means unknown
        elif self.value:
            self.pin.on()
        else:
            self.pin.off()

class rgb(Wheel):
    pass

class pwm(Wheel):
    pass

class touch(Wheel):
    unit_name = 'level'
    unit = ''
    symbol = ''

    def __init__(self, pin=11, **kwargs):
        super().__init__(self, pin=pin, **kwargs)
        self.pin = machine.TouchPad(machine.Pin(self.options['pin']))

    def poll(self):
        reading = self.pin.read()
        value = reading / 1023  # TODO: normalize value
        return dict(value=value, reading=reading)

class tmp36(Wheel):
    unit_name = 'temperature'
    unit = 'degree Celcius'
    symbol = '\'C'
    # TODO

class mq2(Wheel):
    unit_name = 'smoke'
    unit = 'unknown'
    symbol = ':('
    # TODO
