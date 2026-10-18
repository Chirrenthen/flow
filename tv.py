import asyncio
import json
import os
import shutil
import socket
import subprocess
import threading
from zeroconf import ServiceBrowser, Zeroconf
from androidtvremote2 import AndroidTVRemote, CannotConnect, InvalidAuth
import config

_loop = None
_remote = None
_mode = None
_host = None
_connected = False

REMOTE_KEYS = {
    "UP": "DPAD_UP",
    "DOWN": "DPAD_DOWN",
    "LEFT": "DPAD_LEFT",
    "RIGHT": "DPAD_RIGHT",
    "SELECT": "DPAD_CENTER",
    "BACK": "BACK",
    "VOL_UP": "VOLUME_UP",
    "VOL_DOWN": "VOLUME_DOWN",
    "POWER": "POWER",
}

ADB_KEYS = {
    "UP": "19",
    "DOWN": "20",
    "LEFT": "21",
    "RIGHT": "22",
    "SELECT": "23",
    "BACK": "4",
    "VOL_UP": "24",
    "VOL_DOWN": "25",
    "POWER": "26",
}


class _MDNSListener:
    def __init__(self):
        self.found = []

    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info and info.addresses:
            ip = socket.inet_ntoa(info.addresses[0])
            clean_name = name.replace("._androidtvremote2._tcp.local.", "")
            self.found.append((clean_name, ip))

    def update_service(self, zc, type_, name):
        pass

    def remove_service(self, zc, type_, name):
        pass


def discover_tv():
    print("Scanning local network for Android TVs (3 seconds)...")
    zc = Zeroconf()
    listener = _MDNSListener()
    ServiceBrowser(zc, "_androidtvremote2._tcp.local.", listener)
    asyncio.run(asyncio.sleep(3.0))
    zc.close()

    if listener.found:
        name, ip = listener.found[0]
        print(f"Found TV: {name} at {ip}")
        return ip

    return input("No TV auto-discovered. Enter your TV IP address manually: ").strip()


async def _async_setup_remote(ip):
    global _remote, _connected
    _remote = AndroidTVRemote(
        client_name="WaveTV Gesture Remote",
        certfile=config.CERT_FILE,
        keyfile=config.KEY_FILE,
        host=ip,
    )
    await _remote.async_generate_cert_if_missing()

    while True:
        try:
            await _remote.async_connect()
            _connected = True
            print(f"Connected to Android TV at {ip} (Remote Protocol v2)!")
            return True
        except InvalidAuth:
            print("\n--- FIRST-TIME TV PAIRING ---")
            await _remote.async_start_pairing()
            pin = input("Enter the 6-digit PIN shown on your TV screen: ").strip()
            await _remote.async_finish_pairing(pin)
            print("Pairing successful! Connecting...")
        except (CannotConnect, OSError) as err:
            print(f"Remote protocol v2 unavailable ({err}).")
            return False


def _setup_adb_fallback(ip):
    global _connected
    if not shutil.which("adb"):
        print("ERROR: ADB tool not installed. Cannot use ADB fallback.")
        return False

    print(f"Trying ADB fallback on {ip}:5555...")
    res = subprocess.run(["adb", "connect", f"{ip}:5555"], capture_output=True, text=True)
    if "connected" in res.stdout.lower():
        print("Check your TV screen and click 'Allow USB Debugging' if prompted.")
        _connected = True
        return True
    print(f"ADB connection failed: {res.stdout.strip()}")
    return False


def init_tv():
    global _loop, _mode, _host
    if os.path.exists(config.STATE_FILE):
        with open(config.STATE_FILE, "r") as f:
            data = json.load(f)
            _host = data.get("host")
            _mode = data.get("mode", "remote")

    if not _host:
        _host = discover_tv()

    _loop = asyncio.new_event_loop()
    ok = _loop.run_until_complete(_async_setup_remote(_host))
    if ok:
        _mode = "remote"
        threading.Thread(target=_loop.run_forever, daemon=True).start()
    elif _setup_adb_fallback(_host):
        _mode = "adb"
    else:
        print("WARNING: Running in offline camera test mode (TV not reachable).")
        return

    with open(config.STATE_FILE, "w") as f:
        json.dump({"host": _host, "mode": _mode}, f)


def send_command(action):
    if action in ("WAKE", "SLEEP") or not _connected:
        return

    if _mode == "remote" and action in REMOTE_KEYS:
        keycode = REMOTE_KEYS[action]
        try:
            _loop.call_soon_threadsafe(_remote.send_key_command, keycode)
        except Exception as err:
            print(f"Command error: {err}")

    elif _mode == "adb" and action in ADB_KEYS:
        keycode = ADB_KEYS[action]
        subprocess.Popen(
            ["adb", "-s", f"{_host}:5555", "shell", "input", "keyevent", keycode],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def close_tv():
    if _mode == "remote" and _remote and _loop:
        _loop.call_soon_threadsafe(_remote.disconnect)
        _loop.call_soon_threadsafe(_loop.stop)
