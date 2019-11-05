"""
"""

sensor = device.get('tmp36', pin=1),

# get the current value and state, as of the last reading
print('Value:', sensor.value)
print('State:', sensor.state)

# get a single sensor value and state, triggering a reading
print('State:', sensor.read())
print('Value:', sensor.value)

# iterate a sensor values generator
for value in sensor.values():
    print('Value:', value)

# iterate a sensor states generator
for value in sensor.states():
    print('Value:', value)

# create an averaged sensor value generator
for average in filter.Average(size=10).iterate(sensor.values()):  # FIXME: could iterate sensor by adding __iter__ to Device (would make sensor.values() is implicit)
    print('Averaged value:', average)

# interact internally with devices: create a led that reacts to a touch pin
touch = device.touch(pin=11)
led = device.pwm(pin=12)
rgb.iterate(touch.values()))

# interact internally with more devices: create a rgb led that reacts to 3 touch pin

# publish information: create a REST client that publish averaged values
rest = service.RestClient(
    url='http://example.com/blackhole',
    method='put',
    headers={},
    data=lambda device, value: json.dumps({  # create the outgoing request body content
        'value': value,
        'unit': device.unit,
        'label': 'Home water closets'}),
    antiddos=5)                          # antiddos: min silent period for built-in rate moderator that prevent unwanted ddos

rate = filter.RateConstant(period=10)    # filter.RateConstant: used to give a rate to the flow with period=10 equals 6 per minute equals period=util.rate(6/60), filter.RateFixed: try filter.RateSleep(period=60))

average = Average(size=10)               # size=10 use the 10 last values to produce an average value

process = rest.iterate(rate.iterate(average.iterate(sensor.values())))

# subscribe to information: create a REST server that applies incoming states  # FIXME: applying incoming values would be more unifying (1)
rest = service.RestServer(
    routes=[{
        endpoint='/state',
        method='put',
        data=lambda request: {               # create a device.State from the incoming request body, request contains usual referer, headers,
            'r': json['red'] / 255,          # FIXME: creating a single value would be more unifying (1)
            'g': json['green'] / 255,
            'b': json['blue'] / 255
        }
    }]
)

rgb = device.rgb(r=5, g=18, b=19, invert=True)

process = rgb.iterate(rest.values())
