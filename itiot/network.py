import network
import time

class Wifi(object):

    def connect(self, ssid, psk, ip=None, mask=None, gateway=None, dns=None):
        self.nic = network.WLAN(network.STA_IF)
        self.nic.active(True)
        self.nic.connect(ssid, psk)
        while not self.nic.isconnected():
            print('Waiting for network on', self.nic)
            time.sleep(1)
        if ip:
            self.nic.ifconfig([ip] + list(self.nic.ifconfig()[1:]))
        print('Network connected:', self.nic.ifconfig())

    async def aconnect(ssid, psk, ip=None):
        raise NotImplementedError('todo.')
