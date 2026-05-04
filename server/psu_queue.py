import threading
import queue
from typing import TYPE_CHECKING
from logger import setup_logger
from server.payload import process_payload
from server.PSU import PSU
from .Translate import get_dic_for_PSU
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .server import Server

logger = setup_logger("PSUqueue")

class PSUQueue(ABC):
    """Abstract base class for PSU command queues. Handles command processing and status management for a specific PSU.
    Subclasses should implement the handle_get_command, handle_set_command, and refresh_status methods for their specific PSU model.
    """

    def __init__(self, psu: PSU, server: "Server"):
        from .Helper import Helper

        self.psu: PSU = psu
        self.server: "Server" = server
        self.queue: queue.Queue = queue.Queue()
        self.thread: threading.Thread = threading.Thread(target=self.worker, daemon=True)
        self.address: str = psu.address
        self.helper: Helper = Helper(psu)
        self.thread.start()
        
    @abstractmethod
    def handle_get_command(self, command: str, args: list | tuple | None) -> str:
        """Process a get command for the PSU. Should return the response from the PSU."""
        pass
    @abstractmethod
    def handle_set_command(self, command: str, args: list | tuple | None) -> None:
        """Process a set command for the PSU. Should send the command to the PSU and update internal status accordingly."""
        pass
    @abstractmethod
    def refresh_status(self) -> None:
        """Refresh the internal status of the PSU by querying it. Should update the self.status dictionary with the latest values."""
        pass

    def should_split_aggregated_commands(self) -> bool:
        """Return whether aggregated CLI commands should be split before queueing."""
        return True

    
    def add_command(self, identity: bytes, payload: dict) -> None:
        
        # if self.should_split_aggregated_commands():
        #     payload = self.helper.seperate_aggregated_commands(payload)
        payload = process_payload(payload)
        logger.debug(f"Payload after processing: {payload}")
        self.queue.put((identity, payload))

    def worker(self):
        while True:
            identity, payload = self.queue.get()
            last_response: str | None = None
            reply_payload: dict = {

            }
            for command, args in payload.items():
                if (command.startswith("get")): #If it is a get command we query the psu
                        last_response: str = self.handle_get_command(command, args)
                        reply_payload[command] = last_response
                        logger.debug(f"handeling get command: {command}, args: {args}")

                else: # if it is a set command we just send the command to the psu and then query the state of the psu
                    logger.debug(f"handeling set command: {command}, args: {args}")
                    reply_payload[command] = self.handle_set_command(command, args)

            # TODO sende bedre response på query i stedet for status update 
            
            reply = {
                "type": "scpi_reply",
                "name": self.name,
                "payload": reply_payload
            }

            self.server.send_response(identity, reply)

            self.refresh_status()

            self.server.send_status(identity, psu_name=self.name)

            if any(key.startswith("set") for key in payload):
                self.server.send_status_to_GUI(psu_name=self.name)


            # self.server.send_status_update_to_all(self.status, psu_name=self.name)
    


            