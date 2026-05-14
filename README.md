Prototype based on these projects:
PSU_HUB: https://gitlab.cern.ch/shellesu/psu_hub

PSU_REMOTE: https://gitlab.cern.ch/shellesu/psu_remote

## Installation

The project can be installed as a Python package. It is recommended to use a virtual enviroment.

Clone the repository
```bash
git clone https://github.com/h676611/psu_remote.git
```

Create and activate a virtual environment

```bash
python -m venv .venv
```

### Linux / MacOS
```bash
source .venv/bin/activate
```

### Windows
```bash
.venv/Scripts/activate
```

### Install the project in editable mode
```bash
pip install -e .
```

## Running the application

After installation, the server can be started with
```bash
psu-server
```

The GUI can be started in another terminal with
```bash
psu-gui
```

The command-line clients can be started with the entry point for the corresponding instrument
```bash
psu-hmp4040
psu-k2400
psu-k2450
psu-k6500
```

To see the available commands for an instrument client, use the --help option
```bash
psu-hmp4040 --help
```

## Development setup

virtual environment

install requirements.txt