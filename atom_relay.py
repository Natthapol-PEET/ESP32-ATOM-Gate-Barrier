
from machine import Pin
from time import sleep

relay1 = Pin(22, Pin.OUT)
relay2 = Pin(19, Pin.OUT)

while True:
    # RELAY ON
    print("RELAY ON")
    relay1.value(0)
    relay2.value(0)
    sleep(3)
    # RELAY OFF
    print("RELAY OFF")
    relay1.value(1)
    relay2.value(1)
    sleep(3)
  
    try:
        pass
    except KeyboardInterrupt:
        print('Got ctrl-c')
        exit(1)
    finally:
        # Optional cleanup code
        pass
