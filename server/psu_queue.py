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

        self.thread.start()
        
    def add_command(self, identity, payload, request_id=None):
        self.queue.put((identity, payload, request_id))

    def worker(self):
        while True:
            identity, payload, request_id = self.queue.get()
            last_response = None
            reply_payload = {

            }
            if any(key.startswith("get") for key in payload): #If it is a get command we query the psu
                    for command, args in payload.items():
                        scpi_cmd = self.cli_to_scpi(command, args)

                        logger.info(f"Querying command: {scpi_cmd}")
                        last_response = self.psu.query(scpi_cmd)

                        logger.info(f"Response: {last_response}")

                        reply_payload[command] = last_response
            else: # if it is a set command we just send the command to the psu and then query the state of the psu
                for command, args in payload.items():
                    try:
                        scpi_cmd = self.cli_to_scpi(command, args)

                        logger.info(f"Writing command: {scpi_cmd}")
                        self.psu.write(scpi_cmd)

                        logger.info(f"Response: {last_response}")
                    except Exception as e:
                        logger.error(f"Error processing command {command} with args {args}: {e}")

                # After processing set commands, we query all get commands to update the state
                reply_payload.update(self.query_all_get_commands())
                


            if any(key.startswith("set") for key in payload):
                self.broadcast_update()

            reply = {
                "type": "scpi_reply",
                "name": self.name,
                "address": self.address,
                "request_id": request_id,
                "payload": reply_payload
            }


            self.server.send_response(identity, reply)


    def broadcast_update(self):
        # state = self.query_all_get_commands()
        # state_message = {
        #     "type": "status_update",
        #     "name": self.name,
        #     "status": state,
        #     "address": self.address
        # }
        # self.server.broadcast(state_message)
        pass

    def cli_to_scpi(self, command, args):
        base_scpi = self.dic.get(command)


        if base_scpi is None:
            raise ValueError(f"Unknown command: {command}")

        # No arguments
        if args is None or args == '':
            scpi_cmd = base_scpi
            logger.debug(f'converted command: {scpi_cmd}')
            return scpi_cmd
        # ardument is list or tuple
        elif isinstance(args, (list, tuple)):
            scpi_cmd = base_scpi.format(*args)
        # argument is single value
        elif isinstance(args, (int, float, str)):
            scpi_cmd = base_scpi.format(args)
        
        return scpi_cmd
    

    def query_all_get_commands(self):
        logger.debug('Querying all get commands to update state')
        state = {}
        # for command, scpi_template in self.dic.items():
        #     if command.startswith("get") and isinstance(scpi_template, str):
        #         scpi_cmd = scpi_template.format(*["?"] * scpi_template.count("{}"))
        #         response = self.psu.query(scpi_cmd)
        #         state[command] = response
        # return state
        commands = ["get_voltage","get_current", "get_output"]
        for command in commands:
            scpi_template = self.dic.get(command)
            if scpi_template:
                scpi_cmd = scpi_template.format(*["?"] * scpi_template.count("{}"))
                response = self.psu.query(scpi_cmd)
                state[command] = response
        return state


