import machine
import network
import urequests
import itertools

class Changed(object):  # this generator needs to latch a value, so we need a class
    def __init__(self, g, delta=0, value=None):
        self.source = g
        self.delta = delta
        self.value = value

    def __iter__(self):
        self.g = self.generator(self.source)
        return self

    def __next__(self):
        return next(self.g)  # FIXME: it's blocking :(  need to return as in class Consumer

    def generator(self, g):
        for value in g:
            if self.value is None or value != self.value and abs(value - self.value) >= self.delta:
                self.value = value
                yield value

def wifi(ssid, psk):
    nic = network.WLAN(network.STA_IF)
    nic.active(True)
    nic.connect(ssid, psk)
    while not nic.isconnected():
        time.sleep(0.2)
    print('Network connected:', nic.ifconfig())

def make_pipes(nmin=0, nmax=650, delta=0, onchange=True, n=None):
    global Changed  # wtf ?
    touches = [machine.TouchPad(machine.Pin(n)) for n in (13, 12, 14)]
    leds = [machine.PWM(machine.Pin(n)) for n in (5, 18, 19)]

    read = lambda touch: (touch.read() for _ in itertools.repeat(None))  # oneliner infinite generator
    normalize = lambda g, min=0, max=1023: ((value-min)/(max-min) for value in g)
    clamp = lambda g, min_=0, max_=1: (max(min(max_, value), min_) for value in g)
    apply = lambda g, pwm: (pwm.duty(int(value*1023)) or value for value in g)

    if not onchange:
        Changed = lambda g, delta=None: (v for v in g)  # neutralize Changed

    pipes = [
        apply(pwm=leds[i],
            #g=Changed(delta=delta,
                g=clamp(normalize(min=nmin, max=nmax,
                    g=read(touches[i]))))
            #)
                        for i in range(n or len(touches))]
    return pipes

def run(*args, **kwargs):
    #wifi('Wifi "Bel-Air"', 'Corpataux39')

    pipes = make_pipes(*args, **kwargs)
    def pull(pipe):
        value = next(pipe)
        print('Value %s from pipe %s' % (value, pipe))

    # for i, pipe in enumerate(pipes[:2]):
    #     timer = machine.Timer(-1-i)
    #     timer.init(
    #         period=100,
    #         callback=lambda t: pull(pipe))
    #     print('Initialized pipe %s %s with timer %s' % (i, pipe, timer))

    # def pullall():
    #     for i, pipe in enumerate(pipes):
    #         pull(pipe)
    # timer = machine.Timer(-1)
    # timer.init(
    #     period=10,
    #     callback=lambda t: pullall())

    while True:
        for i, pipe in enumerate(pipes):
            pull(pipe)

run()
