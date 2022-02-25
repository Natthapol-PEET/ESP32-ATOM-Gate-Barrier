import machine
import time

button = machine.Pin(39, machine.Pin.IN, machine.Pin.PULL_UP)

cnt = 0

while True:
    if not button.value():
        cnt += 1
        
        print(f"count: {cnt}")
        
    time.sleep(1)
