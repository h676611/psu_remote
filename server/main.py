import json
import threading

from .server import Server
from .zmq_server import ZmqServer
from importlib.resources import files

def load_config() -> dict:
    config_path = files("server").joinpath("psu_config.json")
    with config_path.open("r", encoding="utf8") as file:
        return json.load(file)

def main() -> None:
    config_file = load_config()

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

if __name__ == '__main__':
    main()