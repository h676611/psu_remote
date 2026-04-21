import threading
import queue
from logger import setup_logger
from .Translate import get_dic_for_PSU

logger = setup_logger("PSUqueue")

class PSUQueue:
    """Manages a queue of SCPI commands for a PSU to ensure sequential processing."""

    def __init__(self, psu, server):
        from .Helper import Helper

        self.psu = psu
        self.server = server
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.address = psu.address
        self.helper = Helper(psu)
        self.thread.start()
        
    def add_command(self, identity, payload):
        payload = self.helper.seperate_aggregated_commands(payload)
        self.queue.put((identity, payload))

    def worker(self):
        while True:
            identity, payload = self.queue.get()
            last_response = None
            reply_payload = {

            }
            for command, args in payload.items():
                if any(key.startswith("get") for key in payload): #If it is a get command we query the psu
                        last_response = self.handle_get_command(command, args)
                        reply_payload[command] = last_response
                        logger.debug(f"handeling get command: {command}, args: {args}")

                else: # if it is a set command we just send the command to the psu and then query the state of the psu
                    logger.debug(f"handeling set command: {command}, args: {args}")
                    reply_payload[command] = self.handle_set_command(command, args)

            # reply = {
            #     "type": "scpi_reply",
            #     "name": self.name,
            #     "payload": reply_payload
            # }

            self.refresh_status()

            self.server.send_status(identity, psu_name=self.name)

            if any(key.startswith("set") for key in payload):
                self.server.send_status_to_GUI(psu_name=self.name)


            # self.server.send_status_update_to_all(self.status, psu_name=self.name)
    


            