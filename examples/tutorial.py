print("""

    Pipe it yourself.

    Welcome and congrats !

""")
import sys
sys.path.insert(0, 'itiot')  # for `./mcu lint`
debug = True
def t(title, period=0.1):
    print()
    if debug:
        period = 0
    for l in title + ' ... Ready...Set...':
        sys.stdout.write(l)
        time.sleep(period)
    print('Go!')
    time.sleep(10 * period)

# Welcome !

import device, taylor
import machine
import time

limit = 5
period = 0.5 if not debug else 0

# Play with a device (sensor)
sensor = device.touch(pin=4)
print("Let's play with a device, say a %s")
print("Here it is: %s" % sensor)

t("Get the current state, as of the last reading")
print(sensor.state)

t("Read the current state, triggering a reading on the MCU pin and state update of the device object")
print(sensor.read())

t("Iterate a sensor states generator")
for state in sensor.states(limit=limit):
    print(state)

t("Not so fast pleeease!")
for state in sensor.states(limit=limit):
    print(state)
    time.sleep(period)

t("Please don't block")
#pipe = taylor.log().iterate(sensor.states(limit=limit))
# pipe = sensor.states()
# timer = machine.Timer(-1)
# timer.init(period=period*1000, callback=lambda t: next(pipe))

# create an averaged sensor value generator
# for average in taylor.average(size=50).iterate(sensor.states()):  # FIXME: could iterate sensor by adding __iter__ to Device (would make sensor.values() is implicit)
#     print('Averaged value:', average)
#     time.sleep(0.5)

# light a led on threshold
led = device.led(pin=2)
log = taylor.log(level='info')
trigger = taylor.function(threshold=0.3,
                          f=lambda d,s,v: {'value': bool(v > d.o('threshold'))})
pipe2 = led.iterate(log.iterate(trigger.iterate(sensor.states())))
# for state in pipe2:
#     print(state)

timer = machine.Timer(-1)
timer.init(period=1000, callback=lambda t: next(pipe2))

# # interact internally with devices: create a led that reacts to a touch pin
# touch = device.touch(pin=11)
# led = device.pwm(pin=12)
# rgb.iterate(touch.values()))
#
# # interact internally with more devices: create a rgb led that reacts to 3 touch pin
#

# Mocking devices

t("Use a mock object to mock any device, let's create a mock device")
mock = device.mock()
print('Here it is: %s' % mock)
t("Iterate %s %s times with a period of %ss" % (mock, limit, period))
for state in mock.states(limit=limit):
    print('Pipe output state is', state)
    time.sleep(period)

touch = device.touch(pin=4)
t("Iterate %s %s times with a variable period - it is the iterator that sets the rate" % (mock, limit))
for state in mock.states(limit=10):
    print('Pipe output state is', state)
    time.sleep(period)
    period = period / 2
# TODO: example with custom cycle


# Interact with communication protocols

# # publish information: create a REST client that publish averaged values
# rest = service.RestClient(
#     url='http://example.com/blackhole',
#     method='put',
#     headers={},
#     data=lambda device, value: json.dumps({  # create the outgoing request body content
#         'value': value,
#         'unit': device.unit,
#         'label': 'Home water closets'}),
#     antiddos=5)                          # antiddos: min silent period for built-in rate moderator that prevent unwanted ddos
#
# rate = filter.RateConstant(period=10)    # filter.RateConstant: used to give a rate to the flow with period=10 equals 6 per minute equals period=util.rate(6/60), filter.RateFixed: try filter.RateSleep(period=60))
#
# average = Average(size=10)               # size=10 use the 10 last values to produce an average value
#
# process = rest.iterate(rate.iterate(average.iterate(sensor.values())))
#
# # subscribe to information: create a REST server that applies incoming states  # FIXME: applying incoming values would be more unifying (1)
# rest = service.RestServer(
#     routes=[{
#         endpoint='/state',
#         method='put',
#         data=lambda request: {               # create a device.State from the incoming request body, request contains usual referer, headers,
#             'r': json['red'] / 255,          # FIXME: creating a single value would be more unifying (1)
#             'g': json['green'] / 255,
#             'b': json['blue'] / 255
#         }
#     }]
# )
#
# rgb = device.rgb(r=5, g=18, b=19, invert=True)
#
# process = rgb.iterate(rest.values())
