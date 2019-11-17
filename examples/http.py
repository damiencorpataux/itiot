from itiot import http, network

app = http.App(__name__)

@app.route('/other/:arg')
def a(arg):
    return 'h3770 w027d -> %s' % arg

@app.route('other/:arg/:arg2')
def b(arg, arg2='unknown!'):
    return '-------> %s AND %s' % (arg, arg2)

@app.route('/')
def index():
    return 'h3770 w027d'

print()
r = app.handle(b'GET / HTTP/1.1\r\nHost: 192.168.0.254\r\nUser-Agent: HomeAssistant/0.101.3 aiohttp/3.6.1 Python/3.7\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\n\r\n')
print(r)
r = app.handle(b'GET /other HTTP/1.1\r\nHost: 192.168.0.254\r\nUser-Agent: HomeAssistant/0.101.3 aiohttp/3.6.1 Python/3.7\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\n\r\n')
print(r)
r = app.handle(b'GET /other/ HTTP/1.1\r\nHost: 192.168.0.254\r\nUser-Agent: HomeAssistant/0.101.3 aiohttp/3.6.1 Python/3.7\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\n\r\n')
print(r)
r = app.handle(b'GET /other/a HTTP/1.1\r\nHost: 192.168.0.254\r\nUser-Agent: HomeAssistant/0.101.3 aiohttp/3.6.1 Python/3.7\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\n\r\n')
print(r)
r = app.handle(b'GET /other/a/a HTTP/1.1\r\nHost: 192.168.0.254\r\nUser-Agent: HomeAssistant/0.101.3 aiohttp/3.6.1 Python/3.7\r\nAccept: */*\r\nAccept-Encoding: gzip, deflate\r\n\r\n')
print(r)

network.Wifi().connect('Wifi "Bel-Air"', 'Corpataux39', ip='192.168.0.254')
app.run(socket=http.Timer)
