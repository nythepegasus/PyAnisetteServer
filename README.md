# PyAnisetteWrapper
This was my attempt in fixing SideStore's anisette issue with too many devices per server. What if we could give the client the server instance once, and then use that forever? Well now we can!

# Installation
First get a built version of [Provision](https://github.com/Nythepegasus/Provision), then move your Android `lib` folder and `retrieve_headers` binary into this directory.

Next you'll set up a `.env` file, here is an example one:
```
HOST=0.0.0.0
PORT=6969
REPROVISION_PASSWORD=thisissupersecure
METRICS_PASSWORD=thisissupersecure
```

Then I recommend setting up a Python virtual environment, I typically do:

```bash
python3 -m venv venv
source ./venv/bin/activate
```

Then you should run the following:

```bash
pip3 -r requirements.txt
python3 wrapper.py
```
Profit!
