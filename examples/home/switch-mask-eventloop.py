from itiot import http, network
import machine
import dht
import uasyncio
import json
import time

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


app = http.App(__name__)
# app.debug = True

pins = {
    'smoke': machine.ADC(machine.Pin(34)),
    'temperature': machine.ADC(machine.Pin(36)),
    'pir': machine.Pin(35, machine.Pin.IN),
    'dht': dht.DHT22(machine.Pin(4)),
    'switch': [machine.Signal(machine.Pin(n, machine.Pin.OUT), invert=True) for n in (5, 18, 19)]
             +[machine.Signal(machine.Pin(21, machine.Pin.OUT, machine.Pin.PULL_DOWN), invert=False)],
    'touch': [machine.TouchPad(machine.Pin(n)) for n in (13, 12, 14)]}
pins['smoke'].atten(machine.ADC.ATTN_0DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten
pins['temperature'].atten(machine.ADC.ATTN_11DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten

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
def presence():
    return json.dumps(pins['pir'].value())

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

# class Presence(object):
#     def __init__(self, timeout=60):
#         self.last_detection = None
#         self.timeout = timeout
#     def update(value):
#         if value:
#             self.last_detection = time.time()
#     def sombody(self):
#         # FIXME: time.time() will cycle, handle this
#         return time.time() - self.last_detection < timeout

# class TouchDim(object):
#     def __init__(self, pin):
#         self.pin = pin
#     def loop(self):
#         pass

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
    await uasyncio.start_server(http.Asyncio(app).serve, '0.0.0.0', 80)

@average()
def presence():
    return pins['pir'].value()

touch_handler_state = {}
async def touch_handler():
    threshold = 500
    timeout = 1000
    while True:
        for i, touch in enumerate(pins['touch']):
            reading = touch.read()
            touched = touch_handler_state.get(i, -float('inf'))
            age = time.ticks_ms() - touched
            if reading < threshold and age > timeout or age < 0:  # age < 0 when time.ticks_ms() value cycles
                touch_handler_state[i] = time.ticks_ms()
                switch = pins['switch'][i]
                print('Touched %s %s reading=%s<%s age=%sms -> toggling switch %s %s' %(
                    i, touch, reading, threshold, age, i, switch))
                switch.value(not switch.value())
        await uasyncio.sleep(5/100)

async def presence_handler():
    while True:
        reading = presence()
        somebody = reading > 0
        print('Presence', reading, somebody)
        pins['switch'][1].value(somebody)
        await uasyncio.sleep(1)

async def smoke_handler():
    while True:
        reading = smoke()
        danger = reading > 0.7
        print('Smoke', reading, danger)
        pins['switch'][0].value(danger)
        await uasyncio.sleep(1)

for switch in pins['switch']:
    switch.off()
try:
    loop = uasyncio.get_event_loop()
    loop.create_task(touch_handler())
    loop.create_task(presence_handler())
    loop.create_task(smoke_handler())
    loop.create_task(network_handler())
    loop.run_forever()
finally:
    loop.close()
