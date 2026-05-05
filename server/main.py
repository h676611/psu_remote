import json
import threading

from .server import Server
from .zmq_server import ZmqServer

def main() -> None:

    with open('config.json', 'r') as file:
        config_file = json.load(file)

    # Extract device config for Server
    device_config = config_file.get('devices', {})

    print(f'simulation: {config_file.get("simulate_psus", False)}')
    server = Server(config=device_config, simulation=config_file.get('simulate_psus', False))
    
    # Create ZmqServer with address from config
    zmq_address = config_file.get('zmq', {}).get('server_address', 'tcp://*:1234')
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