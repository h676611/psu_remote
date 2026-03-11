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
            address = self.config[name]["address"]
            self.connect_psu(address=address, name=name)

        while True:
            identity = self.socket.recv()
            request = self.socket.recv_json()

            try:
                self.handle_request(identity, request)
            except Exception as e:
                logger.error(f"Couldn't handle request. error: {e}")
                self.send_error(identity=identity, message=str(e), address=address)

    def handle_request(self, identity, request):
        self.clients.add(identity)
        payload = request.get("payload", {})
        name = request.get("name")
        request_id = request.get("request_id")

        # Lookup the address from config
        try:
            address = self.config[name]["address"]
        except KeyError:
            self.send_error(identity, f"No PSU with name '{name}' in config", address=name, request_id=request_id)
            return

        logger.info(f"received request for {name} at {address}: {payload}")

        # Handle system commands
        system_commands = {"connect", "disconnect", "status"}
        for command, value in payload.items():
            if command in system_commands and value:
                self.handle_system_command(identity, address, command, name=name, request_id=request_id)
                return

        # Otherwise, send SCPI command
        self.handle_scpi_command(identity, address, payload, request_id=request_id)

        
    def handle_system_command(self, identity, address, command, name=None, request_id=None):
        dispatch = {
            "connect": self.connect_psu,
            "disconnect": self.disconnect_psu,
            "status": self.send_status,
        }

        handler = dispatch.get(command)

        if not handler:
            self.send_error(identity, f"Unknown system command: {command}", address, request_id=request_id)
            return

        handler(address=address, identity=identity, name=name, request_id=request_id)


    def handle_scpi_command(self, identity, address, payload, request_id=None):
        if address not in self.psu_queues:
            self.send_error(identity, "PSU not connected", address, request_id=request_id)
            return

        self.psu_queues[address].add_command(identity, payload, request_id=request_id)



    def connect_psu(self, address, identity=None, name=None, request_id=None):
        if address in self.psu_queues:
            logger.error(f"PSU {address} already connected")
            self.send_error(identity=identity, message="PSU already connected", address=address, request_id=request_id)
            return
        
        logger.debug(f'trying to connect {address}')
        if name:
            psu = PSU(self.rm.open_resource(address), name=name)
        else:
            psu = PSU(self.rm.open_resource(address))
        psu.connected = True
        self.psus[address] = psu
        self.psu_queues[address] = PSUQueue(self.psus[address], self)

        logger.info(f'connected psu: {psu.name}')

        if identity:
            self.broadcast_status(address)

            reply = {
                "type": "system_reply",
                "name": psu.name,
                "address": address,
                "request_id": request_id,
                "payload": {
                    "connect": "OK"
                }
            }
            self.send_response(identity, reply)
    
    def disconnect_psu(self, identity, address, name=None, request_id=None):
        if address not in self.psu_queues:
            logger.error(f"PSU {address} not connected")
            self.send_error(identity, "PSU not connected", address, request_id=request_id)
            return
        psu = self.psus[address]
        psu.connected = False
        del self.psu_queues[address]
        logger.info(f'Diconnected PSU {psu.name}')

        self.broadcast_status(address)

        reply = {
            "type": "system_reply",
            "name": psu.name,
            "address": address,
            "request_id": request_id,
            "payload": {
                "disconnect": "OK"
            }
        }

        self.send_response(identity, reply)


    def send_status(self, identity, address, name=None, request_id=None):
        psu = self.psus.get(address)
        status_message = {
            "type": "status_update",
            "name": psu.name,
            "status": psu.get_state(), 
            "address": address,
            "request_id": request_id
        }
        self.send_response(identity, status_message)


    def send_error(self, identity, message, address, request_id=None):
        reply = {
            "type": "error",
            "name": address,
            "request_id": request_id,
            "payload": {
                "message": message
            }
        }
        self.send_response(identity, reply)

    def broadcast_status(self, address):
        psu = self.psus.get(address)
        if not psu:
            return
        status_message = {
            "type": "status_update",
            "name": psu.name,
            "address": address,
            "status": psu.get_state()
        }
        self.broadcast(status_message)

    def broadcast(self, message):
        logger.info(f"Broadcasting status update")
        for client in self.clients:
            self.send_response(client, message)

    def send_response(self, identity, response):
        # logger.info(f'Sending response {response}')
        self.socket.send(identity, zmq.SNDMORE)
        self.socket.send_json(response)
