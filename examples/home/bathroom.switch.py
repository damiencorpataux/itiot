from itiot import http, network, device
import machine
import uasyncio
import dht
import json
import time
import ulogging

ulogging.basicConfig(level=ulogging.INFO)
log = ulogging.getLogger(__name__)

ip = '192.168.0.252'
ssid = 'Wifi "Bel-Air"'
psk = 'Corpataux39'

dht = dht.DHT22(machine.Pin(26))
presence = device.Presence(27, timeout=3*60)
switch = device.Switch(13)
light = machine.Signal(machine.Pin(25, machine.Pin.OUT, value=0), invert=True)
socket = machine.Signal(machine.Pin(14, machine.Pin.OUT, value=1), invert=True)
# indicator = device.IndicatorRgb(5, 18, 19)
onboard_led = device.Indicator(2)
onboard_led.toggle(False)  # FIXME: should be turned off already

async def light_handler():
    # uasyncio.get_event_loop().create_task(switch.run())
    last = None
    while True:
        switch.step()
        if switch.state.value != last:
            light.value(not light.value())
            last = switch.state.value
            log.info('Physical switch changed light to %s' % (light.value()))
        # # for color, switch in zip(indicator.colors.values(), switches):
        # for i in (0, 2):
        #     color = list(indicator.colors.values())[i]
        #     switch = switches[i]
        #     color.to(switch.state)
        await uasyncio.sleep(1/100)

async def presence_handler():
    # uasyncio.get_event_loop().create_task(presence.run())
    while True:
        presence.step()
        # ratio = 1 - presence.delta/presence.timeout if presence.detected else 0
        # indicator.to(g=ratio)
        await uasyncio.sleep(5/10)

ht = {
    'humidity': None,
    'temperature': None
}
async def dht_handler():
    while True:
        try:
            # FIXME: value must be averaged
            dht.measure()
            ht['temperature'] = dht.temperature()
            ht['humidity'] = dht.humidity()
            log.debug('Measured DHT %s' % ht)
        except Exception as e:
            ht['temperature'] = None
            ht['humidity'] = None
            log.error('Cannot read sensor DHT %s' % dht)
        await uasyncio.sleep(5)

async def network_handler():
    # await network.Wifi().aconnect(ssid, psk, ip)
    import network
    nic = network.WLAN(network.STA_IF)
    nic.active(True)
    nic.connect(ssid, psk)
    while not nic.isconnected():
        print('Waiting for network on', nic)
        await uasyncio.sleep(1)
    if ip:
        nic.ifconfig([ip] + list(nic.ifconfig()[1:]))
    print('Network connected:', nic.ifconfig())
    onboard_led.toggle(True)

async def api_handler():
    await uasyncio.start_server(http.Asyncio(app).serve, '0.0.0.0', 80)


app = http.App(__name__)
# app.debug = True

@app.route('/')
def index():
    return json.dumps(app.endpoints.keys())

@app.route('/ht')
def api_ht():
    return json.dumps(ht)

@app.route('/temperature')
def api_temperature():
    return json.dumps(ht['temperature'])

@app.route('/humidity')
def api_humidity():
    return json.dumps(ht['humidity'])

@app.route('/presence')
def api_presence():
    return json.dumps(presence.detected)

@app.route('/light')
def get_light():
    return 'ON' if light.value() else 'OFF'

@app.route('/light', methods=['POST'])
def set_light():
    value = {'on': True, 'off': False}[app.request.body.lower()]
    light.value(value)
    log.info('API changed light to %s' % value)
    return get_light()

@app.route('/socket')
def get_socket():
    return 'ON' if socket.value() else 'OFF'

@app.route('/socket', methods=['POST'])
def set_socket():
    value = {'on': True, 'off': False}[app.request.body.lower()]
    socket.value(value)
    log.info('API changed socket to %s' % socket.value())
    return get_socket()

try:
    socket.value(True)  # FIXME: should be set by machine.Pin() instanciation
    loop = uasyncio.get_event_loop()
    loop.create_task(light_handler())
    loop.create_task(presence_handler())
    loop.create_task(dht_handler())
    loop.create_task(network_handler())
    loop.create_task(api_handler())
    loop.run_forever()
finally:
    loop.close()

