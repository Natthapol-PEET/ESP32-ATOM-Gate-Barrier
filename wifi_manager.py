
from config import *
import led
import socket
import ure
import time
import _thread


def get_connection():
    """return a working WLAN(STA_IF) instance or None"""

    # First check if there already is any connection:
    if wlan_sta.isconnected():
        return wlan_sta

    connected = False
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if wlan_sta.isconnected():
            return wlan_sta

        # Read known network profiles from file
        profiles = read_profiles()

        # Search WiFis in range
        wlan_sta.active(True)
        networks = wlan_sta.scan()

        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK",
                    3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            encrypted = authmode > 0
            print("ssid: %s chan: %d rssi: %d authmode: %s" %
                  (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = do_connect(ssid, password)
                else:
                    print("skipping unknown encrypted network")
            else:  # open
                connected = do_connect(ssid, None)
            if connected:
                break

    except OSError as e:
        print("exception", str(e))

    # start web server for connection manager:
    if not connected:
        connected = start()

    return wlan_sta if connected else None


def read_profiles():
    with open(NETWORK_PROFILES, 'r') as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")
    profiles[ssid] = password
    # profiles = {"peet": "10042541"}

    return profiles


def write_profiles(profiles):
    lines = []
    for ssid, password in profiles.items():
        lines = ["%s;%s\n" % (ssid, password)]
        # lines.append("%s;%s\n" % (ssid, password))
    with open(NETWORK_PROFILES, "w") as f:
        f.write(''.join(lines))


def do_connect(ssid, password):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        return None
    print('Trying to connect to %s...' % ssid)
    wlan_sta.connect(ssid, password)
    for retry in range(100):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print('\nConnected. Network config: ', wlan_sta.ifconfig())
        staticIp, subnet, gateway, dns = wlan_sta.ifconfig()
        write_static_profiles(staticIp, subnet, gateway, dns)
        time.sleep(5)
    else:
        print('\nFailed. Not Connected to: ' + ssid)
    return connected


# def do_connect_fixip(ssid, password, static_ip, subnet, gateway, dns):
def do_connect_fixip(ssid, password, static_network):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        return None

    print('Trying to connect to %s...' % ssid)

    static_ip, subnet, gateway, dns = static_network
    wlan_sta.ifconfig((static_ip, subnet, gateway, dns))

    wlan_sta.connect(ssid, password)
    for retry in range(100):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print('\nConnected. Network config: ', wlan_sta.ifconfig())
    else:
        print('\nFailed. Not Connected to: ' + ssid)

    print(f"isConnect: {wlan_sta.isconnected()}")

    return connected


def send_header(client, status_code=200, content_length=None):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
        client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()


def handle_root(client):
    wlan_sta.active(True)
    ssids = sorted(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan())
    send_header(client)
    client.sendall("""\
        <html>
            <h1 style="color: #5e9ca0; text-align: center;">
                <span style="color: #ff0000;">
                    Wi-Fi Client Setup
                </span>
            </h1>
            <form action="configure" method="post">
                <table style="margin-left: auto; margin-right: auto;">
                    <tbody>
    """)
    while len(ssids):
        ssid = ssids.pop(0)
        client.sendall("""\
                        <tr>
                            <td colspan="2">
                                <input type="radio" name="ssid" value="{0}" />{0}
                            </td>
                        </tr>
        """.format(ssid))
    client.sendall("""\
                        <tr>
                            <td>Password:</td>
                            <td><input name="password" type="password" /></td>
                        </tr>
                    </tbody>
                </table>
                <p style="text-align: center;">
                    <input type="submit" value="Submit" />
                </p>
            </form>
            <p>&nbsp;</p>
            <hr />
            <h5>
                <span style="color: #ff0000;">
                    Your ssid and password information will be saved into the
                    "%(filename)s" file in your ESP module for future usage.
                    Be careful about security!
                </span>
            </h5>
            <hr />
            <h2 style="color: #2e6c80;">
                Some useful infos:
            </h2>
            <ul>
                <li>
                    Original code from <a href="https://github.com/cpopp/MicroPythonSamples"
                        target="_blank" rel="noopener">cpopp/MicroPythonSamples</a>.
                </li>
                <li>
                    This code available at <a href="https://github.com/tayfunulu/WiFiManager"
                        target="_blank" rel="noopener">tayfunulu/WiFiManager</a>.
                </li>
            </ul>
        </html>
    """ % dict(filename=NETWORK_PROFILES))
    client.close()


def handle_configure(client, request):
    match = ure.search("ssid=([^&]*)&password=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        ssid = match.group(1).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(2).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")

    print(f"ssid: {ssid}")
    print(f"password: {password}")

    if len(ssid) == 0:
        send_response(client, "SSID must be provided", status_code=400)
        return False

    if do_connect(ssid, password):
        ip, subnet, gateway, dns = wlan_sta.ifconfig()

        response = f"""
            <html>
                <center>
                    <br><br>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP successfully connected to WiFi network {ssid}.
                        </span>
                    </h1>
                            <br><h3>ifconfig</h3>
                            <h4>IP: {ip}</h4>
                            <h4>Subnet {subnet}</h4>
                            <h4>Gateway {gateway}</h4>
                            <h4>DNS {dns}</h4>
                    <br><br>
                    <a href="http://192.168.4.1/ifconfig">Config IP</a><br><br>
                    <a href="http://192.168.4.1/close">Close</a>
                </center>
            </html>
        """

        send_response(client, response)
        # try:
        #     profiles = read_profiles()
        # except OSError:
        #     profiles = {}
        profiles = {}
        profiles[ssid] = password
        write_profiles(profiles)

        time.sleep(5)

    else:
        response = """\
            <html>
                <center>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP could not connect to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                    <form>
                        <input type="button" value="Go back!" onclick="history.back()"></input>
                    </form>
                </center>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        return False


def handle_ifconfig(client):
    ifcon = wlan_sta.ifconfig()
    ip = ifcon[0]
    subnet = ifcon[1]
    gateway = ifcon[2]
    dns = ifcon[3]

    response = f'''
        <html>
        <body>
            <center>
                <br><br>
                <h2>IP Config</h2>
                <form action="ifconfig-submit" method="post">
                    <label for="static ip">Static IP:</label>
                    <input type="text" id="static" name="static" value="{ip}"><br><br>
                    <label for="subnet">Subnet Mark:</label>
                    <input type="text" id="subnet" name="subnet" value="{subnet}"><br><br>
                    <label for="gateway">Gateway:</label>
                    <input type="text" id="gateway" name="gateway" value="{gateway}"><br><br>
                    <label for="dns">DNS Server:</label>
                    <input type="text" id="dns" name="dns" value="{dns}"><br><br>
                    <input type="submit" value="Submit">
                </form>
            </center>
        </body>
        </html>
    '''
    send_response(client, response)


def handle_ifconfig_submit(client, request):
    match = ure.search(
        "static=(.*)&subnet=(.*)&gateway=(.*)&dns=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        static = match.group(1).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
        subnet = match.group(2).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
        gateway = match.group(2).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
        dns = match.group(2).decode(
            "utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        static = match.group(1).replace("%3F", "?").replace("%21", "!")
        subnet = match.group(2).replace("%3F", "?").replace("%21", "!")
        gateway = match.group(3).replace("%3F", "?").replace("%21", "!")
        dns = match.group(4).replace("%3F", "?").replace("%21", "!")

    print(static, subnet, gateway, dns)
    write_static_profiles(static, subnet, gateway, dns)
    time.sleep(5)

    send_response(client, "<h1>Fix Success</h1>")

    return True


def write_static_profiles(staticIp, subnet, gateway, dns):
    lines = []
    lines.append(f"{staticIp};{subnet};{gateway};{dns}\n")

    with open(STATIC_IP_PROFILES, "w") as f:
        f.write(''.join(lines))


def read_static_profiles():
    with open(STATIC_IP_PROFILES) as f:
        lines = f.readlines()
    for line in lines:
        staticIp, subnet, gateway, dns = line.strip("\n").split(";")
        profiles = [staticIp, subnet, gateway, dns]
    return profiles


def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


def handle_close(client):
    send_response(client, "<h1>Success</h1>")


def handle_ok(client, request):
    send_response(client, "<h1>Success</h1>")


def stop():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None


def start(port=80):
    global server_socket

    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

    stop()

    wlan_sta.active(True)
    wlan_ap.active(True)

    wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)

    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)

    print('Connect to WiFi ssid ' + ap_ssid +
          ', default password: ' + ap_password)
    print('and access the ESP via your favorite web browser at 192.168.4.1.')
    print('Listening on:', addr)

    while True:
        client, addr = server_socket.accept()
        print('client connected from', addr)
        try:
            client.settimeout(5.0)

            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)
            except OSError:
                pass

            print("Request is: {}".format(request))
            led.green()

            if "HTTP" not in request:  # skip invalid requests
                continue

            # version 1.9 compatibility
            try:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP",
                                 request).group(1).decode("utf-8").rstrip("/")
            except Exception:
                url = ure.search(
                    "(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
            print("URL is {}".format(url))

            if url == "":
                handle_root(client)
                led.yellow()
            elif url == "configure":
                handle_configure(client, request)
                led.yellow()
            elif url == "ifconfig":
                handle_ifconfig(client)
                led.yellow()
            elif url == "ifconfig-submit":
                handle_ifconfig_submit(client, request)
                led.blue()
            elif url == "close":
                handle_close(client)
                led.blue()
            elif url == "user=admin&password=secret&command=OpenGate":
                _thread.start_new_thread(remoteRelay1, ())
                handle_ok(client, request)
                led.blue()
            elif url == "user=admin&password=secret&command=CloseGate":
                _thread.start_new_thread(remoteRelay2, ())
                handle_ok(client, request)
                led.blue()
            else:
                handle_not_found(client, url)
                led.blue()

        finally:
            client.close()


def check_connection():
    time.sleep(5)
    if wlan_sta.isconnected():
        led.green()
    else:
        led.red()

    while True:
        time.sleep(30)
        if wlan_sta.isconnected():
            led.green()
        else:
            led.red()


def remoteRelay1():
    relay1.value(OPEN)
    time.sleep(1)
    relay1.value(CLOSE)


def remoteRelay2():
    relay2.value(OPEN)
    time.sleep(1)
    relay2.value(CLOSE)


