from collections.abc import Callable

import pyvisa
import zmq

from .Helper import make_queue
from .psu_queue import PSUQueue
from .PSU import PSU
from logger import setup_logger

logger = setup_logger(name="server")

class Server:
    """A server to handle client requests for PSU control via SCPI commands over ZeroMQ."""

    def __init__(self, config: dict, address: str = "tcp://*:5555"):
        self.context: zmq.Context = zmq.Context()
        self.socket: zmq.Socket = self.context.socket(zmq.ROUTER)
        self.socket.bind(address)
        self.psu_queues: dict[str, PSUQueue] = {}
        self.rm: pyvisa.ResourceManager = pyvisa.ResourceManager('psu_sims.yaml@sim')  # Load the resource manager with the simulation config
        self.clients: set[bytes] = set()

        self.config: dict = config

        self.psus: dict[str, PSU] = {}

        self.connected_GUIs: set[bytes] = set() # contains the identities of connected GUIs to send status updates to

    def start(self) -> None:
        logger.info("Server started")

        logger.info("Connecting to PSUs")

        for name, psu in self.config.items():
            self.connect_psu(psu_name=name)

        while True:
            identity: bytes = self.socket.recv()
            request: dict = self.socket.recv_json()

            try:
                self.handle_request(identity, request)
            except Exception as e:
                logger.error(f"Couldn't handle request. error: {e}")
                self.send_error(identity=identity, message=str(e), psu_name=name)

    def handle_request(self, identity: bytes, request: dict):
        self.clients.add(identity)
        payload: dict = request.get("payload", {})
        psu_name: str | None = request.get("name")

        logger.info(f"received request: {request}")

        # Handle system commands
        system_commands = {"connect", "disconnect", "status", "refresh", "connect_GUI"}
        for command, value in payload.items():
            if command in system_commands and value:
                self.handle_system_command(identity, command, psu_name=psu_name)
                return

        # Otherwise, send SCPI command
        self.handle_scpi_command(identity, psu_name, payload)

        
    def handle_system_command(self, identity: bytes, command: str, psu_name: str | None = None) -> None:
        dispatch = {
            "connect": self.connect_psu,
            "disconnect": self.disconnect_psu,
            "status": self.send_status,
            "refresh": self.refresh_status,
            "connect_GUI": self.connect_GUI,
        }

        handler: Callable[..., None] = dispatch.get(command)

        if not handler:
            self.send_error(identity, f"Unknown system command: {command}", psu_name=psu_name)
            return

        handler(identity=identity, psu_name=psu_name)

    def refresh_status(self, identity: bytes, psu_name: str) -> None:
        if psu_name not in self.psu_queues:
            self.send_error(identity, "PSU not connected", psu_name=psu_name)
            return

        psu_queue: PSUQueue = self.psu_queues[psu_name]

        # TODO add refresh as a command in the queue instead of refreshing directly from server thread
        # to keep it thread safe (maybe)

        # create message with cli commands for refreshing status

        if psu_name == "HMP4040":
            refresh_message: dict = {
                "name": psu_name,
                "payload": {
                }
            }
            for channel in range(1, 5):
                refresh_message["payload"] =  {
                    "set_channel": channel,
                    "get_voltage": True,
                    "get_current": True
                }
        else:
            refresh_message: dict = {
                "name": psu_name,
                "payload": {
                    "get_voltage": True,
                    "get_current": True
                }
            }
        psu_queue.add_command(identity, refresh_message["payload"])
        self.send_status(identity, psu_name=psu_name)

    def handle_scpi_command(self, identity: bytes, psu_name: str , payload: dict) -> None:
        if psu_name not in self.psu_queues:
            self.send_error(identity, "PSU not connected", psu_name=psu_name)
            return

        self.psu_queues[psu_name].add_command(identity, payload)


    def connect_psu(self, identity: bytes = None, psu_name: str | None = None) -> None:
        if psu_name in self.psu_queues:
            logger.error(f"PSU {psu_name} already connected")
            self.send_error(identity=identity, message="PSU already connected", psu_name=psu_name)
            return
        
        if psu_name not in self.config:
            logger.error(f"PSU {psu_name} not in config")
            self.send_error(identity=identity, message="PSU not in config", psu_name=psu_name)
            return
        address: str = self.config[psu_name]["address"]
        psu: PSU = PSU(self.rm.open_resource(address), name=psu_name)

        psu.address = address
        psu.connected = True
        self.psus[psu_name] = psu
        self.psu_queues[psu_name] = make_queue(psu=psu, server=self)

        logger.info(f'connected psu: {psu.name}')

        if identity:
            reply: dict = {
                "type": "system_reply",
                "name": psu.name,
                "payload": {
                    "connect": "OK"
                }
            }
            self.send_response(identity, reply)
    
    def disconnect_psu(self, identity: bytes, psu_name: str) -> None:
        if psu_name not in self.psu_queues:
            logger.error(f"PSU {psu_name} not connected")
            self.send_error(identity, "PSU not connected", psu_name=psu_name)
            return
        psu: PSU = self.psus[psu_name]
        psu.connected = False
        del self.psu_queues[psu_name]
        logger.info(f'Diconnected PSU {psu.name}')

        reply: dict = {
            "type": "system_reply",
            "name": psu.name,
            "payload": {
                "disconnect": "OK"
            }
        }

        self.send_response(identity, reply)

    def connect_GUI(self, identity: bytes, psu_name: str | None = None) -> None:
        self.connected_GUIs.add(identity)
        logger.info(f"Connected GUI with identity {identity}")

        reply: dict = {
            "type": "system_reply",
            "payload": {
                "connect_GUI": "OK"
            }
        }
        self.send_response(identity, reply)

    def send_status(self, identity: bytes, psu_name: str) -> None:
        psu: PSU | None = self.psus.get(psu_name)
        psu_queue: PSUQueue = self.psu_queues[psu_name]
        status = psu_queue.status
        status_message: dict = {
            "type": "status_update",
            "name": psu.name if psu else None,
            "status": status,
            "psu_name": psu_name
        }
        self.send_response(identity, status_message)

    def send_status_to_GUI(self, psu_name: str) -> None:
        psu: PSU | None = self.psus.get(psu_name)
        psu_queue: PSUQueue = self.psu_queues[psu_name]
        status = psu_queue.status
        status_message: dict = {
            "type": "status_update",
            "name": psu.name if psu else None,
            "status": status,
            "psu_name": psu_name
        }
        for GUI in self.connected_GUIs:
            self.send_response(GUI, status_message)


    def send_error(self, identity: bytes, message: str, psu_name: str) -> None:
        reply: dict = {
            "type": "error",
            "name": psu_name,
            "payload": {
                "message": message
            }
        }
        self.send_response(identity, reply)

    def send_response(self, identity: bytes, response: dict) -> None:
        self.socket.send(identity, zmq.SNDMORE)
        self.socket.send_json(response)

    def send_status_update_to_all(self, status: str, psu_name: str) -> None:
        # pass
        for client in self.clients:
           self.send_status(identity=client, psu_name=psu_name)