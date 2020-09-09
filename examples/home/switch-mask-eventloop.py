from itiot import http, network
import machine
import dht
import uasyncio
import json
import time
import ulogging

ulogging.basicConfig(level=ulogging.DEBUG)
log = ulogging.getLogger(__name__)

def cache(timeout=2):
    """
    Minimalistic cache decorator.
    """
    # from https://stackoverflow.com/a/53918439/1300775
    cache = dict()
    def wrapper(f):
        def wrapped(*args, **kwargs):
            key = args + tuple((k,v) for k,v in kwargs.items())
            result, stamp = cache.get(key, (None, None))
            print('CACHE lookup', f, result, timeout, time.time(), stamp)
            if stamp is not None and time.time() - stamp < timeout:
                print('CACHE hit   ', f, result, timeout, time.time(), stamp)
                return result
            else:
                result = f(*args, **kwargs)
                cache[key] = result, time.time()
                print('CACHE save  ', f, result, timeout, time.time())
                return result
        return wrapped
    return wrapper

# def average(size=10):
#     """
#     Average decorator.
#     """
#     history = []
#     print(history)
#     def wrapper(f):
#         print(history)
#         def wrapped(*args, **kwargs):
#             print(history)
#             result = f(*args, **kwargs)
#             history.insert(0, result)
#             history =  history[:size]
#             return sum(history) / len(history)
#         return wrapped
#     return wrapper

class average(object):
    def __init__(self, size=10):
        self.size = size
        self.history = []
    def __call__(self, f):
        def wrapped(*args, **kwargs):
            result = f(*args, **kwargs)
            self.history.insert(0, result)
            self.history = self.history[:self.size]
            return sum(self.history) / len(self.history)
        return wrapped

class Indicator(object):

    def __init__(self, pin:int, invert=False):
        self.invert = invert
        self.pin = pin
        self.pwm = machine.PWM(machine.Pin(pin))
        self.pwm.init()

    @property
    def brightness(self):
        duty = self.pwm.duty()
        return (1023-duty if self.invert else duty) / 1023

    def toggle(self):
        self.to(0 if self.brightness else 1)

    def to(self, brightness):
        """
        Set indicator to given brightness. Valid values are 0..1, True and False.
        """
        brightness = max(0, min({False: 0, True: 1}.get(brightness, brightness), 1))
        duty = round((brightness if not self.invert else 1-brightness) * 1023)
        if True: #duty != self.pwm.duty():
            log.debug('Indicator pin=%s to brightness=%s duty=%s' % (self.pin, brightness, duty))
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
            self.to(self.brightness + step)
            await uasyncio.sleep(resolution)
        self.to(brightness)

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

class Presence(object):
    def __init__(self, pin:int, timeout=180):
        self.pin = machine.Pin(pin, machine.Pin.IN)
        self.timeout = timeout * 1000
        self.poll = 3/10
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

    async def run(self):
        while True:
            self.step()
            await uasyncio.sleep(self.poll)

class Switch(object):
    def __init__(self):
        self.values = (False, True)
        self.state = self.values[0]

    def toggle(self):
        next = (self.values.index(self.state) + 1) % len(self.values)
        self.state = self.values[next]

    async def run(self):
        pass

class TouchSwitch(Switch):

    def __init__(self, pin:int):
        super().__init__()
        self.pin = pin
        self.touch = machine.TouchPad(machine.Pin(pin))
        self.last_touched = 0
        self.threshold = 500
        self.debounce = 3/10
        self.poll = 1/10

    async def run(self):
        while True:
            reading = self.touch.read()
            idle = time.ticks_diff(time.ticks_ms(), self.last_touched)
            if reading < self.threshold and (idle > self.debounce * 1000 or idle < 0):
                self.toggle()
                log.info('%s touched %s pin=%s state=%s reading=%s<%s idle=%sms' %(self, self.touch, self.pin, self.state, reading, self.threshold, idle))
                self.last_touched = time.ticks_ms()
                # FIXME: use pub/sub for touch event ?
                #self.switch.value(not self.switch.value())
            await uasyncio.sleep(self.poll)

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
        self.poll = 5/100

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
            await uasyncio.sleep(self.poll)


pins = {
    'smoke': machine.ADC(machine.Pin(34)),
    'temperature': machine.ADC(machine.Pin(36)),
    'dht': dht.DHT22(machine.Pin(4))}
pins['smoke'].atten(machine.ADC.ATTN_0DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten
pins['temperature'].atten(machine.ADC.ATTN_11DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten

presence = Presence(35)#, timeout=10)
switches = [TouchSwitch(n) for n in (13, 12, 14)] + [Switch()]
onboard = Indicator(2)
indicator = IndicatorRgb(5, 18, 19, invert=True)

async def switches_handler():
    for button in switches:
        uasyncio.get_event_loop().create_task(button.run())
    while True:
        # for color, switch in zip(indicator.colors.values(), switches):
        for i in (0, 2):
            color = list(indicator.colors.values())[i]
            switch = switches[i]
            color.to(switch.state)
        await uasyncio.sleep(1/10)

async def presence_handler():
    # uasyncio.get_event_loop().create_task(presence.run())
    while True:
        presence.step()
        ratio = 1 - presence.delta/presence.timeout if presence.detected else 0
        indicator.to(g=ratio)
        await uasyncio.sleep(1/10)

async def smoke_handler():
    while True:
        unhealthy = 0.7
        danger = 0.9
        reading = smoke()
        ratio = reading#(max(unhealthy, min(reading, danger)) - unhealthy) / 1/(danger-unhealthy)
        print('Smoke', reading, ratio)
        # indicator.to(r=ratio)
        onboard.to(ratio)
        await uasyncio.sleep(1)

async def network_handler():
    ip = '192.168.0.254'
    ssid = 'Wifi "Bel-Air"'
    psk = 'Corpataux39'
    import network
    # FIXME: should not block to let other tasks run while connecting to wifi
    nic = network.WLAN(network.STA_IF)
    nic.active(True)
    nic.connect(ssid, psk)
    while not nic.isconnected():
        print('Waiting for network on', nic)
        await uasyncio.sleep(1)
    if ip:
        nic.ifconfig([ip] + list(nic.ifconfig()[1:]))
    print('Network connected:', nic.ifconfig())

async def api_handler():
    await uasyncio.start_server(http.Asyncio(app).serve, '0.0.0.0', 80)


app = http.App(__name__)
# app.debug = True

@app.route('/')
def index():
    values = {}
    for route, callback in app.endpoints.items():
        if route[0] != '/':
            print('CALL ROUTE', route, callback)
            try:
                values[route] = callback()#json.loads(callback())
            except Exception as e:
                print('CALL FAIL!', route, callback, e.__class__.__name__, e)
                values[route] = e
    return json.dumps(values)

@app.route('/uptime')
def uptime():
    return time.time()

@app.route('/smoke')
def smoke():
    return pins['smoke'].read() / 4095

@app.route('/temperature')
def temperature():
    reading = pins['temperature'].read()
    voltage = reading / 4095 * 3.6
    temperature = (voltage - 0.5) / 0.01
    return temperature

@app.route('/dht')
@cache(3)
def dht_all():
    pin = pins['dht']
    try:
        pin.measure()
        return json.dumps({'temperature': pin.temperature(),
                           'humidity': pin.humidity()})
    except Exception as e:
        raise http.HTTPException('%s: %s' % (e.__class__.__name__, str(e)), status=500)

@app.route('/dht/temperature')
def dht_temperature():
    return json.dumps(json.loads(dht_all())['temperature'])

@app.route('/dht/humidity')
def dht_humidity():
    return json.dumps(json.loads(dht_all())['humidity'])

@app.route('/presence')
def api_presence():
    return json.dumps(presence.detected)

@app.route('/switch/:id')
def get_switch(id):
    return 'ON' if switches[int(id)].state else 'OFF'

@app.route('/switch/')
def get_switches():
    return json.dumps({id: get_switch(id) for id in range(len(switches))})

@app.route('/switch/:id', methods=['POST'])
def set_switch(id):
    switch = switches[int(id)]
    value = app.request.body
    log.info('Setting switch %s to %s' % (id, value))
    switch.state = True if value.lower()=='on' else False
    return get_switch(id)

switches[2].state = True
try:
    loop = uasyncio.get_event_loop()
    loop.create_task(switches_handler())
    loop.create_task(presence_handler())
    loop.create_task(smoke_handler())
    loop.create_task(network_handler())
    loop.create_task(api_handler())
    loop.run_forever()
finally:
    loop.close()
