'''
    RGB LED(SK6812)
'''

import machine, neopixel

ledPin = machine.Pin(27, machine.Pin.OUT)

np = neopixel.NeoPixel(ledPin, 8)

'''
np[0] = (255, 255, 255) # set to red, full brightness
np[1] = (255, 255, 255) # set to green, half brightness
np[2] = (255, 255, 255)  # set to blue, quarter brightness
'''

def red():
    np[0] = (200, 0, 0)
    np.write()
    
def green():
    np[0] = (0, 200, 0)
    np.write()
    
def blue():
    np[0] = (0, 0, 200)
    np.write()

def yellow():
    np[0] = (200, 200, 0)
    np.write()

def off():
    np[0] = (0, 0, 0)
    np.write()
