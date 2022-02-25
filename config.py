import network
from machine import Pin

ap_ssid = "Atom_WifiManager"
ap_password = "12345678"
ap_authmode = 3  # WPA2

NETWORK_PROFILES = 'wifi.dat'
STATIC_IP_PROFILES = 'static_ip.dat'

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

server_socket = None

OPEN = 1
CLOSE = 0
relay1 = Pin(22, Pin.OUT)
relay2 = Pin(19, Pin.OUT)

button = Pin(39, Pin.IN, Pin.PULL_UP)


