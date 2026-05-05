import json
import threading

from .server import Server
from .zmq_server import ZmqServer

if __name__ == "__main__":

    with open('server/psu_config.json', 'r') as file:
        config_file = json.load(file)

    server = Server(config=config_file)
    zmq_server = ZmqServer(server=server)
    server.set_zmq_server(zmq_server)

    server_thread = threading.Thread(target=zmq_server.run, daemon=True)
    server_thread.start()

    server.start()

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Server shutting down...")
