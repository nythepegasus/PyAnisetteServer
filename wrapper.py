import os
import json
import shutil
import string
import secrets
import logging
import binascii
import argparse
import subprocess
from dotenv import dotenv_values
from quart import Quart, request

config = dotenv_values(".env")

try:
    os.mkdir("logs")
except FileExistsError:
    pass

ip_logs = logging.getLogger("v0.0.1-ip")
anisette_logs = logging.getLogger("v0.0.1-anisette")

anisette_handler = logging.FileHandler("logs/anisette.log")
ip_handler = logging.FileHandler("logs/ip.log")
anisette_logs.setLevel(logging.INFO)
ip_logs.setLevel(logging.INFO)
anisette_handler.setFormatter(logging.Formatter('[%(asctime)s]  [%(name)s]  [%(levelname)s] - %(message)s'))
ip_handler.setFormatter(logging.Formatter('[%(asctime)s]  [%(name)s]  [%(levelname)s] - %(message)s'))

anisette_logs.addHandler(anisette_handler)
ip_logs.addHandler(ip_handler)

app = Quart(__name__)

start_identifier = binascii.b2a_hex(os.urandom(8)).decode()
subprocess.run(['./retrieve_headers', f'-a={start_identifier}'], stdout=subprocess.PIPE)
connected_ips = []
total_ever_ips = []
current_identifier = secrets.token_hex(8)

async def genAnisette(file: bytes = None):
    global start_identifier
    if file is not None:
        IDENTIFIER = file[0:16].decode()
        if not all(c in string.hexdigits for c in IDENTIFIER):
            anisette_logs.info(f"IDENTIFIER: {IDENTIFIER} is not hex!")
            return "Nice try bozo"
        try:
            os.mkdir(IDENTIFIER)
        except FileExistsError:
            pass
        with open(f"./{IDENTIFIER}/adi.pb", "wb+") as f:
            print(file[16:])
            f.write(file[16:])
        result = subprocess.run(['./retrieve_headers', '--remember-machine=true', f'-a={IDENTIFIER}'], stdout=subprocess.PIPE)
        anisette_logs.info(result.stdout.decode())
        return result.stdout.decode()
    result = subprocess.run(['./retrieve_headers', '--remember-machine=true', f'-a={start_identifier}'], stdout=subprocess.PIPE)
    anisette_logs.info(result.stdout.decode())
    return result.stdout.decode()

@app.route("/", methods=["GET", "POST"])
async def index():
    global total_ever_ips
    if request.remote_addr not in total_ever_ips:
        ip_logs.info(request.remote_addr)
        total_ever_ips.append(request.remote_addr)
    file = None
    if request.method == "POST":
        files = await request.files
        file = files['adi.pb'].read()
        anisette_logs.info(f"adi.pb file: {file}")

    anisette = await genAnisette(file)
    if anisette == "Nice try bozo":
        ip_logs.info(f"{request.remote_addr} has a janky adi.pb file :(")
        return anisette

    anisette = json.loads(anisette)
    anisette['X-Apple-I-SRL-NO'] = "This is set by SideStore anyway, lmao"
    anisette['X-MMe-Client-Info'] = "<iMac20,2> <Mac OS X;13.1;22C65> <com.apple.AuthKit/1 (com.apple.dt.Xcode/3594.4.19)>"

    return anisette

@app.get("/reprovision")
async def reprovision():
    global start_identifier
    key = request.args.get("key")
    ip_logs.info(f"{request.remote_addr} tried `key`: {key}")
    if key != config['REPROVISION_PASSWORD']:
        ip_logs.info(f"{request.remote_addr} tried to access stuff (/reprovision) they shouldn't D:<")
        return {"Status": "DENIEDDD", "note": "Your attempt has been logged, please refrain from continuing. You may be IP banned if shenanigans continue."}
    start_identifier = binascii.b2a_hex(os.urandom(8)).decode()
    anisette_logs.info(f"Reprovisioned with start identifier: {start_identifier}")
    subprocess.run(['./retrieve_headers', f'-a={start_identifier}'], stdout=subprocess.PIPE)
    return {"Status": "Success, yayyyyy!"}

@app.get("/adi_file")
async def adi_file():
    global connected_ips
    global current_identifier
    global total_ever_ips
    if request.remote_addr not in total_ever_ips:
        ip_logs.info(f"Adding '{request.remote_addr}' to `total_ever_ips`")
        total_ever_ips.append(request.remote_addr)
    if request.remote_addr not in connected_ips:
        ip_logs.info(f"Adding '{request.remote_addr}' to `connected_ips`")
        connected_ips.append(request.remote_addr)
    ip_logs.info(f"`connected_ips` counter: {len(connected_ips)}")
    if len(connected_ips) == 5:
        connected_ips.clear()
        connected_ips.append(request.remote_addr)
        current_identifier = binascii.b2a_hex(os.urandom(8)).decode()
        ip_logs.info(f"`connected_ips` counter has reached 5, refreshing!")
        subprocess.run(['./retrieve_headers', f'-a={current_identifier}'], stdout=subprocess.PIPE)

    try:
        anisette_logs.info(f"Refreshing current anisette with: {current_identifier}")
        adi_data = open(f"{current_identifier}/adi.pb", "rb").read()
    except FileNotFoundError:
        anisette_logs.error(f"No `adi.pb` directory! Refreshing current anisette with: {current_identifier}")
        subprocess.run(['./retrieve_headers', f'-a={current_identifier}'], stdout=subprocess.PIPE)
    finally:
        adi_data = open(f"{current_identifier}/adi.pb", "rb").read()

    return bytes(current_identifier, "ascii") + adi_data

@app.get("/metrics")
async def metrics():
    global connected_ips
    global total_ever_ips
    key = request.args.get("admin")
    ip_logs.info(f"{request.remote_addr} tried `key`: {key}")
    if key != config['METRICS_PASSWORD']:
        ip_logs.info(f"{request.remote_addr} tried to access stuff (/metrics) they shouldn't D:<")
        return {"Status": "Stay out, there be dragons here..", "note": "Your attempt has been logged, please refrain from continuing. You may be IP banned if shenanigans continue."}
    elif key == config['METRICS_PASSWORD']:
        ip_logs.info(f"{request.remote_addr} successfully accessed /metrics")
        return {"Status": "Okay, wise guy..", "all-since-boot-ips": total_ever_ips, "current-queued-ips": connected_ips}

if __name__ == '__main__':
    try:
        app.run(host=config['HOST'], port=config['PORT'])
    except KeyError:
        parser = argparse.ArgumentParser("anisette_wrapper")
        parser.add_argument("host", help="Hostname to use for the server", type=str)
        parser.add_argument("port", help="Port to use for the server", type=str)
        args = parser.parse_args()
        app.run(host=args.host, port=args.port)

