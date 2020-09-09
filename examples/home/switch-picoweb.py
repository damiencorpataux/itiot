import picoweb
import network
import time

nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect('Wifi "Bel-Air"', 'Corpataux39')
while not nic.isconnected():
    print('Waiting for network on', nic)
    time.sleep(1)
nic.ifconfig(['192.168.0.254']+list(nic.ifconfig()[1:]))
print('Network connected:', nic.ifconfig())

app = picoweb.WebApp(__name__)

@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("This is webapp #1")

if __name__ == "__main__":
    app.run(debug=True)
