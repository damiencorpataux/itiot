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

class Presence(object):
    def __init__(self, pin:machine.Pin, timeout=180):
        self.pin = pin
        self.timeout = timeout * 1000
        self.poll = 3/10
        self.reading = None
        self.last = None

    @property
    def detected(self):
        delta = time.ticks_diff(time.ticks_ms(), self.last)
        detected = delta < self.timeout and self.last is not None
        log.debug('Presence delta=%s detected=%s reading=%s' % (delta, detected, self.reading))
        return detected

    async def run(self):
        while True:
            self.reading = self.pin.value()
            if self.reading:
                self.last = time.ticks_ms()
            await uasyncio.sleep(self.poll)

class TouchSwitch(object):

    def __init__(self, touch:machine.TouchPad, switch:machine.Pin):
        self.touch = touch
        self.switch = switch
        self.last_touched = 0
        self.threshold = 500
        self.debounce = 3/10
        self.poll = 1/10

    async def run(self):
        while True:
            reading = self.touch.read()
            idle = time.ticks_diff(time.ticks_ms(), self.last_touched)
            if reading < self.threshold and (idle > self.debounce * 1000 or idle < 0):
                print('Touched %s reading=%s<%s idle=%sms -> toggling switch %s' %(self.touch, reading, self.threshold, idle, self.switch))
                self.last_touched = time.ticks_ms()
                self.switch.value(not self.switch.value())
            await uasyncio.sleep(self.poll)


pins = {
    'smoke': machine.ADC(machine.Pin(34)),
    'temperature': machine.ADC(machine.Pin(36)),
    'pir': machine.Pin(35, machine.Pin.IN),
    'dht': dht.DHT22(machine.Pin(4)),
    'switch': #[machine.PWM(machine.Pin(n)) for n in (5, 18, 19)]
              [machine.Signal(machine.Pin(n, machine.Pin.OUT), invert=True) for n in (5, 18, 19)]
             +[machine.Signal(machine.Pin(21, machine.Pin.OUT, machine.Pin.PULL_DOWN), invert=False)],
    'touch': [machine.TouchPad(machine.Pin(n)) for n in (13, 12, 14)]}
pins['smoke'].atten(machine.ADC.ATTN_0DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten
pins['temperature'].atten(machine.ADC.ATTN_11DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten

presence = Presence(pins['pir'])
touch = TouchSwitch(pins['touch'][index], pins['switch'][index])

async def touch_handler(index):
    await touch.run()

async def presence_handler():
    uasyncio.get_event_loop().create_task(presence.run())
    while True:
        pins['switch'][1].value(presence.detected)
        await uasyncio.sleep(5/10)

async def smoke_handler():
    while True:
        reading = smoke()
        danger = reading > 0.7
        print('Smoke', reading, danger)
        pins['switch'][0].value(danger)
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
    return 'ON' if pins['switch'][int(id)].value() else 'OFF'

@app.route('/switch/')
def get_switches():
    return json.dumps({id: get_switch(id) for id in range(len(pins['switch']))})

@app.route('/switch/:id', methods=['POST'])
def set_switch(id):
    pin = pins['switch'][int(id)]
    value = app.request.body
    print('Setting %s to %s' % (pin, value))
    pin.value(True if value.lower()=='on' else False)
    return get_switch(id)


# for switch in pins['switch']:
#     switch.off()
try:
    loop = uasyncio.get_event_loop()
    for i in range(len(pins['touch'])):
        loop.create_task(touch_handler(i))
    loop.create_task(presence_handler())
    loop.create_task(smoke_handler())
    loop.create_task(network_handler())
    loop.create_task(api_handler())
    loop.run_forever()
finally:
    loop.close()
