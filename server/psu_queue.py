import threading
import queue
from time import sleep
from logger import setup_logger
from server.Helper import Helper
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
        self.helper = Helper(psu)
        self.thread.start()
        
    def add_command(self, identity, payload):
        payload = self.helper.seperate_aggregated_commands(payload)
        logger.debug(f"Adding command to queue: {payload}")
        self.queue.put((identity, payload))

    def worker(self):
        while True:
            identity, payload = self.queue.get()
            last_response = None
            reply_payload = {

            }

            if any(key.startswith("get") for key in payload): #If it is a get command we query the psu
                    for command, args in payload.items():
                        last_response = self.handle_get_command(command, args)
                        reply_payload[command] = last_response

            else: # if it is a set command we just send the command to the psu and then query the state of the psu
                for command, args in payload.items():
                    self.handle_set_command(command, args)

            reply = {
                "type": "scpi_reply",
                "name": self.name,
                "payload": reply_payload
            }

            # if any(key.startswith("set") for key in payload):
            #     self.server.send_status(identity=identity, psu_name=self.name)

            self.server.send_response(identity, reply)

            self.refresh_status()
            #self.server.send_status_update_to_all(self.status, psu_name=self.name)
    

    # def refresh_status(self):
    #     if self.name == "hmp4040":
    #         for channel in range(1, self.num_channels + 1):
    #             # handle set channel and get voltage as two queries for hmp4040 since it needs to know which channel to query from
    #             set_channel_cmd = self.dic.get("set_channel").format(channel)
    #             self.psu.query(set_channel_cmd)
    #             voltage_cmd = self.dic.get("get_voltage")
    #             current_cmd = self.dic.get("get_current")
    #             voltage_response = self.psu.query(voltage_cmd)
    #             current_response = self.psu.query(current_cmd)

    #             if voltage_response is not None and str(voltage_response).strip() != "":
    #                 self.status[channel]["voltage"] = voltage_response
    #             if current_response is not None and str(current_response).strip() != "":
    #                 self.status[channel]["current"] = current_response
    #     else:
    #         voltage_cmd = self.dic.get("get_voltage")
    #         current_cmd = self.dic.get("get_current")
    #         voltage_response = self.psu.query(voltage_cmd)
    #         current_response = self.psu.query(current_cmd)
    #         if voltage_response is not None and str(voltage_response).strip() != "":
    #             self.status[1]["voltage"] = voltage_response
    #         if current_response is not None and str(current_response).strip() != "":
    #             self.status[1]["current"] = current_response

            