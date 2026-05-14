import json
from pathlib import Path
import threading

from .server import Server
from .zmq_server import ZmqServer

def main() -> None:
    """Entry point for the server application."""

    config_file = {}
    try:
        config_path = Path(__file__).resolve().parents[1] / 'config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as file:
                config_file = json.load(file)
    except Exception:
        config_file = {}

    # Extract device config for Server
    device_config = config_file.get('devices', {})

    server = Server(config=device_config, simulation=config_file.get('simulate_psus', False))
    
    # Create ZmqServer with address from config
    zmq_address = config_file.get('zmq', {}).get('server_address', 'tcp://*:5555')
    zmq_server = ZmqServer(server=server, address=zmq_address)
    server.set_zmq_server(zmq_server)

    server_thread = threading.Thread(target=zmq_server.run, daemon=True)
    server_thread.start()

    server.start()

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Server shutting down...")

if __name__ == '__main__':
    main()