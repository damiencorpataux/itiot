import uasyncio as asyncio
import machine
import network
import ulogging as logging
import json
import time
import re

nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect('Wifi "Bel-Air"', 'Corpataux39')
while not nic.isconnected():
    print('Waiting for network on', nic)
    time.sleep(1)
nic.ifconfig(['192.168.0.254']+list(nic.ifconfig()[1:]))
print('Network connected:', nic.ifconfig())

def smoke():
    pin = machine.ADC(machine.Pin(34))
    pin.atten(machine.ADC.ATTN_0DB)  # https://docs.micropython.org/en/latest/esp32/quickref.html#ADC.atten
    return pin.read() / 4095

def temperature():
    pin = machine.ADC(machine.Pin(36))
    pin.atten(machine.ADC.ATTN_11DB)
    reading = pin.read()
    voltage = reading / 4095 * 3.6
    temperature = (voltage - 0.5) / 0.01
    return temperature

def switches(**state):
    pins = [machine.Signal(machine.Pin(n, machine.Pin.OUT), invert=True)
            for n in (5, 18, 19)]
    print(state)
    if state:
        for i, pin in enumerate(pins):
            value = state.get(str(i))
            print('Pin command', i, pin, value)
            if value is not None:
                print('Setting pin %s to %s' % (pin, value))
                pin.value(value)
    return {str(i): 'ON' if pin.value() else 'OFF' for i, pin in enumerate(pins)}

class Request(object):
    def __init__(self, bites):
        print('Request', bites)
        bang, *content = bites.splitlines()
        self.method, self.path, self.protocol = bang.decode().lower().split()
        self.body = b''.join(content[1+content.index(b''):])
        self.headers = {}
        for header in content[:content.index(b'')]:
            k, v = header.split(b':', 1)
            self.headers[k.decode().strip().lower()] = v.strip()
    def __str__(self):
        return '%s %s' % (self.method, self.path)

@asyncio.coroutine
def serve(reader, writer):
    request = yield from reader.read()
    if request:
        r = Request(request)
        print('REST Request', r, r.body)

        match = re.match('^/switch/(\d+)$', r.path)
        if match:
            id = match.group(1)
            if r.method == 'post':
                try:
                    command = r.body.decode()#json.loads(r.body)
                    print(command)
                    switches(**{id: command == 'ON'})
                except ValueError as e:
                    pass
            data = switches()[id]
        else:
            data = {"smoke": smoke(),
                    "temperature": temperature(),
                    "switch": switches()}

        body = json.dumps(data)
        print('Response:', body)
        yield from writer.awrite('HTTP/1.0 200 OK\r\n\r\n%s\r\n' % body)
    yield from writer.aclose()

#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

def run():
    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.start_server(serve, "0.0.0.0", 80))
    loop.run_forever()
    loop.close()

run()
