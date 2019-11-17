from itiot import http, network
import machine
import json

app = http.App(__name__)
app.debug = True

pin = {
    'smoke': machine.ADC(machine.Pin(34)),
    'temperature': machine.ADC(machine.Pin(36)),
    'switch': [machine.Signal(machine.Pin(n, machine.Pin.OUT), invert=True)
               for n in (5, 18, 19)]}
pin['smoke'].atten(machine.ADC.ATTN_0DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten
pin['temperature'].atten(machine.ADC.ATTN_11DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten

@app.route('/')
def index():
    # return json.dumps({'smoke': smoke()})
    return json.dumps({route: endpoint[1]()
        for route, endpoint in app.endpoints.items()})

@app.route('/smoke')
def smoke():
    return pin['smoke'].read() / 4095

@app.route('/temperature')
def temperature():
    reading = pin['temperature'].read()
    voltage = reading / 4095 * 3.6
    temperature = (voltage - 0.5) / 0.01
    return temperature

@app.route('/switch/:id')
def switch(id):
    pin = pin['switch'][id]
    return 'ON' if pin.value() else 'OFF'

@app.route('/switch/:id', method=['POST'])
def set_switch(id):
    print('Request', app.request)
    if state:
        for i, pin in enumerate(pins):
            value = state.get(str(i))
            print('Pin command', i, pin, value)
            if value is not None:
                print('Setting pin %s to %s' % (pin, value))
                pin.value(value)

network.Wifi().connect('Wifi "Bel-Air"', 'Corpataux39', ip='192.168.0.254')
app.run(socket=http.Timer)
