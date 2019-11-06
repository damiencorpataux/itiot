"""
Electronic Component abstraction.
"""

import itiot
import machine
import itertools

# class State(object):  # FIXME: no state class for now: -KISS-
# """
# A state can always boil down to a value.
# """
#     __int__ = lambda self: int(self.state['value'])
#     __float__ = lambda self: float(self.state['value'])
#     __long__ = lambda self: float(self.state['value'])

class Device(itiot.Wheel):
    """
    Abstract.
    Electronic components abstraction.
    Sensor components are only generators, active components are only iterators.
    This class adds man-in-the-middle methods `poll`, `read` and `apply`.
    """
    unit_name = None  # the <unit_name> is 20 <unit> (<symbol>)
    unit = None       # the temperature is 20 degree Celcius ('C)
    symbol = None     # only ascii characters (eg. 'C), for compatibility with the chaos...
    pin = None        # `machine.Pin` object (or `device.Wiring`)

    def __init__(self, **options):
        super().__init__(**options)
        if 'pin' in options:
            self.log.info('%s is on pin %s', self, self.o('pin'))

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
        self.apply(**self.poll())
        return self.state

    def apply(self, _commit=True, **state):  # NOTE: _commit is not used from anywhere yet
        """
        Apply `state` to `self.state`, commit to MCU if `_commit` is not False.
        See `self.commit`.
        """
        for key, value in state.items():
            self.state[key] = value
        if _commit:
            self.commit(**state)

    def commit(self, **state):
        """
        Commit `state` to physical device.
        """
        pass  # sensors do not implement this method

    def states(self, limit=None, dry=False):  # NOTE: `limit` is not necessary, `dry` is not used from anywhere yet
        """
        Return a generator that yield device states.
        Method `read` is called if `dry` is False, otherwise `poll`.
        """
        # FIX: is there a lag between poll and actual yielding
        # when the consumer sleeps between iterations ?
        source = self.poll if dry else self.read
        if limit:
            for _ in range(limit): yield source()
        else:
            while True: yield source()

    def iterate(self, iterator, commit=True):  # NOTE: commit is not used from anywhere yet
        """
        Apply states yielded from `iterator`.
        """
        for state in iterator:
            self.apply(**state, _commit=commit)
            yield self.state


class mock(Device):
    """
    Mock a device by cycling values.
    """
    def __init__(self, cycle=(0,1), unit_name=None, unit=None, symbol=None, **kwargs):
        super().__init__(cycle=cycle, **kwargs)
        self.symbol = symbol
        self.unit = unit
        self.unit_name = unit_name
        self.cycle = itertools.cycle(self.o('cycle'))

    def poll(self):
        return dict(value=next(self.cycle))

    def commit(self, **state):
        pass  # any state will do

class led(Device):
    unit_name = 'logic level'
    unit = 'binary'
    symbol = '!!'

    def __init__(self, pin=11, **kwargs):
        super().__init__(pin=pin, **kwargs)
        self.pin = machine.Pin(self.options['pin'], machine.Pin.OUT)

    def poll(self):
        return dict(value=self.pin.value())  # value 0 or 1 is better than boolean
                                             # for math operations, ie. average
    def commit(self, value):
        if self.value is None:
            self.log.warning('%s ignoring commit: value is None' % self)
        elif self.value:
            self.pin.on()
        else:
            self.pin.off()

class pwm(Device):
    unit_name = 'ratio'
    unit = ''
    symbol = ':'

class rgb(Device):
    pass

class touch(Device):
    unit_name = 'level'
    unit = ''
    symbol = ''

    def __init__(self, pin=11, **kwargs):
        super().__init__(pin=pin, **kwargs)
        self.pin = machine.TouchPad(machine.Pin(self.options['pin']))

    def poll(self):
        reading = self.pin.read()
        value = reading / 1023  # TODO: normalize value
        return dict(value=value, reading=reading)

class tmp36(Device):
    unit_name = 'temperature'
    unit = 'degree Celcius'
    symbol = '\'C'
    # TODO

class mq2(Device):
    unit_name = 'smoke'
    unit = 'unknown'
    symbol = ':('
    # TODO
