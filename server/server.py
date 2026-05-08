from collections.abc import Callable
import time
from typing import TYPE_CHECKING

import pyvisa

from .Helper import make_queue
from .PSU import PSU
from .psu_queue import PSUQueue
from logger import setup_logger

if TYPE_CHECKING:
    from .zmq_server import ZmqServer

logger = setup_logger(name="server")


class Server:
    """A server to handle client requests for PSU control via SCPI commands over ZeroMQ."""

    def __init__(self, config: dict, simulation: bool = False) -> None:
        self.psu_queues: dict[str, PSUQueue] = {}
        
        self.simulation: bool = simulation
        self.rm: pyvisa.ResourceManager = pyvisa.ResourceManager("psu_sims.yaml@sim") if simulation else pyvisa.ResourceManager()
        self.config: dict = config
        self.zmq_server: "ZmqServer | None" = None
        self.psus: dict[str, PSU] = {}
        self.connected_GUIs: set[bytes] = set()

    def set_zmq_server(self, zmq_server: "ZmqServer") -> None:
        self.zmq_server = zmq_server

    def start(self) -> None:
        logger.info("Server started")
        logger.info("Connecting to PSUs")

        for name, psu in self.config.items():
            self.connect_psu(psu_name=name)

    def handle_request(self, identity: bytes, request: dict):
        payload: dict = request.get("payload", {})
        psu_name: str | None = request.get("name")

        logger.info(f"received request: {request}")

        system_commands = {"connect", "disconnect", "status", "refresh", "connect_GUI"}
        for command, value in payload.items():
            if command in system_commands and value:
                self.handle_system_command(identity, command, psu_name=psu_name)
                return

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

        if psu_name == "hmp4040":
            for channel in range(1, 5):
                refresh_payload: dict = {
                    "get_channel_display_voltage": channel,
                    "get_channel_display_current": channel,
                    "get_channel_output": channel,
                    "refresh": True
                }
                psu_queue.add_command(None, refresh_payload)
        elif psu_name == "k6500":
            refresh_payload = {
                "get_voltage": True
            }
            psu_queue.add_command(None, refresh_payload)
        else:
            refresh_payload = {
                "get_display_current_voltage_output": True,
                "refresh": True
            }
            psu_queue.add_command(None, refresh_payload)

        logger.info(f"Adding refresh command to queue for PSU {psu_name}")

    def handle_scpi_command(self, identity: bytes, psu_name: str, payload: dict) -> None:
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

        logger.info(f"connected psu: {psu.name}")

        if identity:
            reply: dict = {
                "type": "system_reply",
                "name": psu.name,
                "payload": {
                    "connect": "OK"
                }
            }
            self.send_response(identity, reply)
            self.send_system_to_GUI(reply)
        

    def disconnect_psu(self, identity: bytes, psu_name: str) -> None:
        if psu_name not in self.psu_queues:
            logger.error(f"PSU {psu_name} not connected")
            self.send_error(identity, "PSU not connected", psu_name=psu_name)
            return

        psu: PSU = self.psus[psu_name]
        psu.connected = False
        del self.psu_queues[psu_name]
        logger.info(f"Diconnected PSU {psu.name}")

        reply: dict = {
            "type": "system_reply",
            "name": psu.name,
            "payload": {
                "disconnect": "OK"
            }
        }

        self.send_response(identity, reply)
        self.send_system_to_GUI(reply)

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
        logger.debug(F"sending status: {status}")
        for gui in self.connected_GUIs:
            self.send_response(gui, status_message)

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
        if self.zmq_server is None:
            raise RuntimeError("ZMQ server is not attached")
        self.zmq_server.send_response(identity, response)
    def send_system_to_GUI(self, reply):
         for gui in self.connected_GUIs:
            self.send_response(gui, reply)


    def check_psu_addresses(self) -> None:
        """On startup, check if PSUs in config are on the correct addresses."""

        for address in self.config.values():
            if self.simulation:
                logger.info(f"Simulated PSU at {address} is ready")
            else:
                logger.info(f"Checking connection to PSU at {address}")
                try:
                    resource = self.rm.open_resource(address)
                    response = resource.query("*IDN?")
                    if response:
                        logger.info(f"Successfully connected to PSU at {address}: {response.strip()}")
                except Exception as e:
                    logger.error(f"Failed to connect to PSU at {address}: {e}")

    