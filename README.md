Server, GUI client and CLI client for remote controlling instruments.

Based on:
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

## Configuration

The server loads configuration in this order:
1. [config.json](config.json) in the project root (if present)
2. [server/psu_config.json](server/psu_config.json) packaged with the project

Use this structure for either file:
```json
{
	"zmq": {
		"server_address": "tcp://*:5555",
		"client_address": "tcp://10.0.0.2:5555"
	},
	"devices": {
		"hmp4040": {
			"address": "ASRL5::INSTR",
			"display_name": "LV Connection"
		}
	},
	"simulate_psus": false
}
```
`zmq.server_address` binds address, `devices` lists PSU names and VISA addresses, and `simulate_psus` enables simulation by default.

If server is started with `psu-server --simulate`, the command-line flag overrides `simulate_psus` in the file.

## Running the application

After installation, the server can be started with
```bash
psu-server
```

To start it with simulated instruments defined in [psu_sims.yaml](psu_sims.yaml), use:
```bash
psu-server --simulate
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

## Authors
- [Herman Dahlberg](https://github.com/h676611)
- [Lars Paulsen Løge](https://github.com/larsploge)
- [Henning Øinas](https://github.com/669837)
