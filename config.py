import network
from machine import Pin
import time

ssid = 'ARTANI_BUILDING_TWO_2G'
password = 'TEDEls@84'
# mqtt_server = 'broker.hivemq.com'
mqtt_server = '192.168.1.85'
#EXAMPLE IP ADDRESS
client_id = 'esp32-atom'
topic_sub = b'/mqtt/gate'
topic_pub = b'notification'
port = 1883

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

button = Pin(39, Pin.IN, Pin.PULL_UP)

OPEN = 0
CLOSE = 1
relay1 = Pin(22, Pin.OUT)
relay2 = Pin(19, Pin.OUT)

# init relay off
relay1.value(CLOSE)
relay2.value(CLOSE)

time.sleep(0.5)
relay2.value(OPEN)
time.sleep(1)
relay2.value(CLOSE)
    
