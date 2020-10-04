from itiot import http, network
import machine
import dht
import uasyncio
import json
import time
import ulogging

ulogging.basicConfig(level=ulogging.DEBUG)
log = ulogging.getLogger(__name__)

class Indicator(object):

    def __init__(self, pin:int, invert=False):
        self.invert = invert
        self.pin = pin
        self.history = []
        self.pwm = machine.PWM(machine.Pin(pin))
        self.pwm.init()

    @property
    def brightness(self):
        duty = self.pwm.duty()
        return (1023-duty if self.invert else duty) / 1023

    def toggle(self, brightness=None):
        if brightness is not None:
            next = brightness
        else:
            if self.history:
                next = self.history[0]
            else:
                next = 0 if self.brightness else 1
        self.to(next)

    def to(self, brightness, historize=True):
        """
        Set indicator to given brightness. Valid values are 0..1, True and False.
        """
        brightness = max(0, min({False: 0, True: 1}.get(brightness, brightness), 1))
        duty = round((brightness if not self.invert else 1-brightness) * 1023)
        if True: #duty != self.pwm.duty():
            log.debug('Indicator pin=%s to brightness=%s duty=%s' % (self.pin, brightness, duty))
            if historize:
                self.history = ([self.brightness] + self.history)[-2:]
            self.pwm.duty(duty)

    def transition(self, *args, **kwargs):
        uasyncio.get_event_loop().run_until_complete(self.atransition(*args, **kwargs))

    async def atransition(self, brightness, length=1):
        # FIXME: witl fail on racing conditions: implement a queue
        resolution = 5/100  # seconds
        delta = brightness - self.brightness
        steps = round(length/resolution)
        step = delta / steps
        print('Transition', resolution, delta, steps, step)
        for i in range(steps):
            print(self.brightness, step, '=', self.brightness + step)
            self.to(self.brightness + step, historize=False)
            await uasyncio.sleep(resolution)
        self.to(brightness, historize=True)

    def pulse(self, *args, **kwargs):
        uasyncio.get_event_loop().run_until_complete(self.apulse(*args, **kwargs))

    async def apulse(self, times=1, length=2/100, period=3/10):
        # FIXME: witl fail on racing conditions: implement a queue
        for i in range(times):
            self.toggle()
            await uasyncio.sleep(length)
            self.toggle()
            await uasyncio.sleep(period-length)

class IndicatorRgb(object):

    def __init__(self, r:int, g:int, b:int, invert=False):
        import collections
        self.colors = collections.OrderedDict((
            ('r', Indicator(r, invert)),
            ('g', Indicator(g, invert)),
            ('b', Indicator(b, invert))))

    def get(self, color):
        return self.colors[color]

    def toggle(self, colors='rgb'):
        for color in colors:
            self.get(color).toggle()

    def to(self, **colors):
        for color, brightness in colors.items():
            self.colors[color].to(brightness)

    def pulse(self, colors='rgb', *args, **kwargs):
        # loop = uasyncio.get_event_loop()
        # for color in colors:
        #     loop.create_task(self.get(color).apulse(*args, **kwargs))
        # loop.run_forever()
        uasyncio.get_event_loop().run_until_complete(self.apulse(colors, *args, **kwargs))

    async def apulse(self, colors='rgb', *args, **kwargs):
        loop = uasyncio.get_event_loop()
        for color in colors:
            loop.create_task(self.get(color).apulse(*args, **kwargs))

class Poller(object):

    interval = 1/10

    async def run(self):
        # FIXME: factorize in base class
        while True:
            log.debug('Poller step, interval %ss' % self.interval)
            self.step()
            await uasyncio.sleep(self.interval)

class Presence(Poller):

    def __init__(self, pin:int, timeout=180):
        self.pin = machine.Pin(pin, machine.Pin.IN)
        self.timeout = timeout * 1000
        self.interval = 3/10
        self.reading = None
        self.last = None

    @property
    def delta(self):
        return time.ticks_diff(time.ticks_ms(), self.last)

    @property
    def detected(self):
        detected = self.delta < self.timeout and self.last is not None
        return detected

    def step(self):
        last_reading = self.reading
        last_detected = self.detected
        self.reading = self.pin.value()
        # log.debug('Presence reading: delta=%s detected=%s reading=%s' % (self.delta, detected, self.reading))
        if self.reading:
            self.last = time.ticks_ms()
        if last_reading != self.reading:
            log.info('Presence sensor changed: from %s to %s' % (last_reading, self.reading))
        if last_detected != self.detected:
            log.info('Presence state changed: from %s to %s' % (last_detected, self.detected))

class State(object):

    def __init__(self, values = (False, True)):
        self.values = values
        self.value = self.values[0]

    def set(self, value):
        self.values.index(value)
        self.value = value

    def toggle(self):
        next = (self.values.index(self.value) + 1) % len(self.values)
        self.value = self.values[next]

class Switch(Poller):

    def __init__(self, pin:int, values=(False, True)):
        super().__init__()
        self.state = State(values)
        self.pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_DOWN)

    def step(self):
        self.state.set(bool(self.pin.value()))
        log.debug('Switch state: %s' % self.state.value)

class TouchSwitch(Switch):

    def __init__(self, pin:int):
        super().__init__()
        self.pin = pin
        self.touch = machine.TouchPad(machine.Pin(pin))
        self.last_touched = 0
        self.threshold = 500
        self.debounce = 3/10
        self.interval = 1/10

    def step(self):
        reading = self.touch.read()
        idle = time.ticks_diff(time.ticks_ms(), self.last_touched)
        if reading < self.threshold and (idle > self.debounce * 1000 or idle < 0):
            self.toggle()
            log.info('%s touched %s pin=%s state=%s reading=%s<%s idle=%sms' %(self, self.touch, self.pin, self.state, reading, self.threshold, idle))
            self.last_touched = time.ticks_ms()
            # FIXME: use pub/sub for touch event ?
            #self.switch.value(not self.switch.value())

class TouchDimmer(TouchSwitch):

    def __init__(self, touch:machine.TouchPad, pwm:machine.PWM):
        self.touch = touch
        self.pwm = pwm
        self.last_reading = float('inf')
        self.last_touched = 0
        self.last_duty = 1023
        self.threshold = 500
        self.debounce = 500
        self.step = 10
        self.interval = 5/100

    async def run_simpler(self):
        while True:
            touch = self.touch.read() < self.threshold
            if touch and not self.touch:
                self.touch = touch
                # trigger touch in
                print('Touch in')
            if touch and self.touch:
                # trigger touching
                print('Touch touching')
            if not touch and self.touch:
                self.touch = touch
                # trigger touch out
                print('Touch out')

    async def run(self):
        while True:
            reading = self.touch.read()
            idle = time.ticks_ms() - self.last_touched  # idle < 0 when ticks_ms() value cycles
            if reading > self.threshold:
                if reading > self.last_reading:
                    self.last_touched = time.ticks_ms()
                if 0 <= idle < self.debounce:
                    print('Switching on/off')
                    self.pwm.duty(0 if self.duty() else self.last_duty)  # toggle on/off
            else:
                # if idle > self.debounce or age < 0:
                print('Dimming')
                self.pwm.duty((self.pwm.duty() + self.step) % 1023)
                self.last_duty = self.pwm.duty()
                self.last_reading = reading
            await uasyncio.sleep(self.interval)

