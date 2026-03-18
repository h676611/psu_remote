import threading
import queue
from logger import setup_logger
from .Translate import get_dic_for_PSU

logger = setup_logger("PSUqueue")

class PSUQueue:
    """Manages a queue of SCPI commands for a PSU to ensure sequential processing."""

    def __init__(self, psu, server):
        self.psu = psu
        self.server = server
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.address = psu.address

        self.name = psu.name
        self.dic = get_dic_for_PSU(self.name)
        self.status = {}
        self.selected_channel = 1
        if self.name == "hmp4040":
            self.num_channels = 4
        else:
            self.num_channels = 1
        for channel in range(1, self.num_channels + 1):
            self.status[channel] = {
                "voltage": 0.0,
                "current": 0.0,
                "output": 0
            }

        self.thread.start()
        
    def add_command(self, identity, payload, request_id=None):
        self.queue.put((identity, payload, request_id))

    def worker(self):
        while True:
            identity, payload, request_id = self.queue.get()
            last_response = None
            reply_payload = {

            }

            # TODO: k6500 must use query for set commands

            if any(key.startswith("get") for key in payload): #If it is a get command we query the psu
                    for command, args in payload.items():
                        scpi_cmd = self.cli_to_scpi(command, args)

                        # logger.info(f"Querying command: {scpi_cmd}")
                        last_response = self.psu.query(scpi_cmd)

                        # logger.info(f"Response: {last_response}")

                        reply_payload[command] = last_response
            else: # if it is a set command we just send the command to the psu and then query the state of the psu
                for command, args in payload.items():
                    try:
                        scpi_cmd = self.cli_to_scpi(command, args)

                        # logger.info(f"Writing command: {scpi_cmd}")
                        self.psu.write(scpi_cmd)

                        # logger.info(f"Response: {last_response}")
                    except Exception as e:
                        # logger.error(f"Error processing command {command} with args {args}: {e}")
                        pass

                    if command == "set_channel":
                        self.selected_channel = args

                    if command == "set_voltage":
                        logger.debug(f'Updating status for channel {self.selected_channel} voltage to {args}')
                        self.status[self.selected_channel]["voltage"] = args
                    elif command == "set_current":
                        self.status[self.selected_channel]["current"] = args
                    elif command == "set_output":
                        self.status[self.selected_channel]["output"] = args


            reply = {
                "type": "scpi_reply",
                "name": self.name,
                "address": self.address,
                "request_id": request_id,
                "payload": reply_payload
            }

            if any(key.startswith("set") for key in payload):
                self.server.send_status(identity, self.address, request_id=request_id)

            self.server.send_response(identity, reply)


    def cli_to_scpi(self, command, args):
        base_scpi = self.dic.get(command)


        if base_scpi is None:
            raise ValueError(f"Unknown command: {command}")

        # No arguments
        if args is None or args == '':
            scpi_cmd = base_scpi
            # logger.debug(f'converted command: {scpi_cmd}')
            return scpi_cmd
        # ardument is list or tuple
        elif isinstance(args, (list, tuple)):
            scpi_cmd = base_scpi.format(*args)
        # argument is single value
        elif isinstance(args, (int, float, str)):
            scpi_cmd = base_scpi.format(args)
        
        return scpi_cmd
    

    def refresh_status(self):
        for channel in range(1, self.num_channels + 1):
            if "set_channel" in self.dic:
                ch_cmd = self.dic["set_channel"].format(channel)
                self.psu.write(ch_cmd)
                self.status[channel] = self.query_voltage_current()
            else:
                self.status[channel] = self.query_voltage_current()

    def query_voltage_current(self):
        voltage = None
        current = None
        if "get_voltage" in self.dic:
            voltage_cmd = self.dic["get_voltage"]
            voltage = self.psu.query(voltage_cmd)
        if "get_current" in self.dic:
            current_cmd = self.dic["get_current"]
            current = self.psu.query(current_cmd)
        return {"voltage": voltage, "current": current}
