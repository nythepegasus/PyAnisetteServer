import os
import json
import shutil
import secrets
import argparse
import subprocess
from quart import Quart, request

app = Quart(__name__)

start_identifier = secrets.token_hex(8)

async def genAnisette(file: bytes = None):
    DIR_SETTING = "."
    if file is not None:
        IDENTIFIER = file[0:16].decode()
        with open(f"./{IDENTIFIER}/adi.pb", "wb+") as f:
            print(file[16:])
            f.write(file[16:])
        result = subprocess.run(['./retrieve_headers', '--remember-machine=true', f'-f={IDENTIFIER}', f'-i={IDENTIFIER}'], stdout=subprocess.PIPE)
        shutil.rmtree(IDENTIFIER)
        return result.stdout.decode()
    IDENTIFIER = secrets.token_hex(8)
    os.mkdir(IDENTIFIER)
    result = subprocess.run(['./retrieve_headers', '--remember-machine=false', f'-f={start_identifier}', f'-i={start_identifier}'], stdout=subprocess.PIPE)
    shutil.rmtree(IDENTIFIER)
    return result.stdout.decode()

@app.route("/", methods=["GET", "POST"])
async def index():
    file = None
    if request.method == "POST":
        files = await request.files
        file = files['adi.pb'].read()

    anisette = await genAnisette(file)

    anisette = json.loads(anisette)
    anisette['X-Apple-I-SRL-NO'] = "This is set by SideStore anyway, lmao"

    print(anisette)

    return anisette

@app.get("/adi_file")
async def adi_file():
    identifier = secrets.token_hex(8)
    subprocess.run(['./retrieve_headers', f'-f={identifier}', f'--identifier={identifier}'], stdout=subprocess.PIPE)
    shutil.rmtree(IDENTIFIER)
    adi_data = open(f"{identifier}/adi.pb", "rb").read()
    return bytes(identifier, "ascii") + adi_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser("anisette_wrapper")
    parser.add_argument("host", help="Hostname to use for the server", type=str)
    parser.add_argument("port", help="Port to use for the server", type=str)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port)

