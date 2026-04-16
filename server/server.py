import pyvisa
import zmq
from .psu_queue import PSUQueue
from .PSU import PSU
from logger import setup_logger

logger = setup_logger(name="server")

class Server:
    """A server to handle client requests for PSU control via SCPI commands over ZeroMQ."""

    def __init__(self, config, address="tcp://*:5555"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.bind(address)
        self.psu_queues = {}
        self.rm = pyvisa.ResourceManager('psu_sims.yaml@sim')
        self.clients = set()

        self.config = config

        self.psus = {}

    def start(self):
        logger.info("Server started")

        logger.info("Connecting to PSUs")

        for name, psu in self.config.items():
            self.connect_psu(psu_name=name)

        while True:
            identity = self.socket.recv()
            request = self.socket.recv_json()

            try:
                self.handle_request(identity, request)
            except Exception as e:
                logger.error(f"Couldn't handle request. error: {e}")
                self.send_error(identity=identity, message=str(e), psu_name=name)

    def handle_request(self, identity, request):
        self.clients.add(identity)
        payload = request.get("payload", {})
        psu_name = request.get("name")

        logger.info(f"received request for {psu_name} with payload: {payload}")

        # Handle system commands
        system_commands = {"connect", "disconnect", "status", "refresh"}
        for command, value in payload.items():
            if command in system_commands and value:
                self.handle_system_command(identity, command, psu_name=psu_name)
                return

        # Otherwise, send SCPI command
        self.handle_scpi_command(identity, psu_name, payload)

        
    def handle_system_command(self, identity, command, psu_name=None):
        dispatch = {
            "connect": self.connect_psu,
            "disconnect": self.disconnect_psu,
            "status": self.send_status,
            "refresh": self.refresh_status
        }

        handler = dispatch.get(command)

        if not handler:
            self.send_error(identity, f"Unknown system command: {command}", psu_name=psu_name)
            return

        handler(identity=identity, psu_name=psu_name)

    def refresh_status(self, identity, psu_name):
        if psu_name not in self.psu_queues:
            self.send_error(identity, "PSU not connected", psu_name=psu_name)
            return

        psu_queue = self.psu_queues[psu_name]
        psu_queue.refresh_status()
        self.send_status(identity, psu_name=psu_name)

    def handle_scpi_command(self, identity, psu_name, payload):
        if psu_name not in self.psu_queues:
            self.send_error(identity, "PSU not connected", psu_name=psu_name)
            return

        self.psu_queues[psu_name].add_command(identity, payload)


    def connect_psu(self, identity=None, psu_name=None):
        if psu_name in self.psu_queues:
            logger.error(f"PSU {psu_name} already connected")
            self.send_error(identity=identity, message="PSU already connected", psu_name=psu_name)
            return
        
        logger.debug(f'trying to connect {psu_name}')
        if psu_name not in self.config:
            logger.error(f"PSU {psu_name} not in config")
            self.send_error(identity=identity, message="PSU not in config", psu_name=psu_name)
            return
        address = self.config[psu_name]["address"]
        psu = PSU(self.rm.open_resource(address), name=psu_name)

        psu.address = address
        psu.connected = True
        self.psus[psu_name] = psu
        self.psu_queues[psu_name] = PSUQueue(psu=psu, server=self)

        logger.info(f'connected psu: {psu.name}')

        if identity:
            reply = {
                "type": "system_reply",
                "name": psu.name,
                "payload": {
                    "connect": "OK"
                }
            }
            self.send_response(identity, reply)
    
    def disconnect_psu(self, identity, psu_name):
        if psu_name not in self.psu_queues:
            logger.error(f"PSU {psu_name} not connected")
            self.send_error(identity, "PSU not connected", psu_name=psu_name)
            return
        psu = self.psus[psu_name]
        psu.connected = False
        del self.psu_queues[psu_name]
        logger.info(f'Diconnected PSU {psu.name}')

        reply = {
            "type": "system_reply",
            "name": psu.name,
            "payload": {
                "disconnect": "OK"
            }
        }

        self.send_response(identity, reply)

    def send_status(self, identity, psu_name):
        psu = self.psus.get(psu_name)
        psu_queue = self.psu_queues[psu_name]
        status = psu_queue.status
        status_message = {
            "type": "status_update",
            "name": psu.name,
            "status": status,
            "psu_name": psu_name
        }
        logger.debug(f'Sending status update: {status_message}')
        self.send_response(identity, status_message)


    def send_error(self, identity, message, psu_name):
        reply = {
            "type": "error",
            "name": psu_name,
            "payload": {
                "message": message
            }
        }
        self.send_response(identity, reply)

    def send_response(self, identity, response):
        self.socket.send(identity, zmq.SNDMORE)
        self.socket.send_json(response)

    def send_status_update_to_all(self, status, psu_name):
        logger.debug(f'Sending status update to all clients: {status}')
        for client in self.clients:
            self.send_status(identity=client, psu_name=psu_name)