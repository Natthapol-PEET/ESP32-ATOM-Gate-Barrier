from config import *
import wifi_manager
import time
import led
import _thread


def worker():
    # check connection wifi
    _thread.start_new_thread(wifi_manager.check_connection, ())

    # start server
    wifi_manager.start()


def main():
    '''
        send_header
        send_response
        handle_root
        handle_configure
        handle_not_found
        stop
        start
    '''
    
    # init relay off
    relay1.value(CLOSE)
    relay2.value(CLOSE)

    # manual start
    fixip_wait = True
    button_state = False
    cnt = 0

    # wait led status
    led.yellow()
    print('wait button setup network', end='')

    while fixip_wait and cnt < 10:
        if not button.value():
            led.blue()
            fixip_wait = False
            button_state = True

            # setup network, fix network and run server
            worker()
        
        print('.', end='')
        cnt = cnt + 1
        time.sleep(0.5)
        led.red()
        time.sleep(0.5)
        led.yellow()

    if not button_state:
        # auto start
        profiles = wifi_manager.read_profiles()
        static_network = wifi_manager.read_static_profiles()

        print(f"profiles: {profiles}")
        print(f"static_network: {static_network}")

        for ssid, password in profiles.items():
            wifi_manager.do_connect_fixip(ssid, password, static_network)

        # run server
        worker()


