# Complete project details at https://RandomNerdTutorials.com

import time
from config import *
import led
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()


def main():    
    # wait intenet connection 
    led.red()
    
    cnt = 0
    print('Trying to connect to %s...' % ssid)
    while station.isconnected() == False:
      # print('.', end='')
      # time.sleep(0.5)
      cnt += 1
      if cnt > 5000000:
          print('*---------- reset ----------*')
          machine.reset()

    # intenet connected
    led.yellow()

    print('Connection successful')
    print(station.ifconfig())

    try:
      client = connect_and_subscribe()
    except OSError as e:
      restart_and_reconnect()

    while True:
      try:
        if station.isconnected() == False:
            led.blue()
            restart_and_reconnect()
        # new_message = client.check_msg()
        # if new_message != 'None':
        #   client.publish(topic_pub, b'received')
        time.sleep(1)
      except KeyboardInterrupt:
        break
      except OSError as e:
        restart_and_reconnect()


def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(5)
  machine.reset()
  

def connect_and_subscribe():
  client = MQTTClient(client_id=client_id, server=mqtt_server, port=port)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  
  # connect mqtt
  led.green()
  
  return client
  
  
def sub_cb(topic, msg):
  print((topic, msg.decode("utf-8")))
  
  if msg.decode("utf-8") == 'open':
      remoteRelay1()
  elif msg.decode("utf-8") == 'close':
      remoteRelay2()
      
def remoteRelay1():
    relay1.value(OPEN)
    time.sleep(1)
    relay1.value(CLOSE)


def remoteRelay2():
    relay2.value(OPEN)
    time.sleep(1)
    relay2.value(CLOSE)





