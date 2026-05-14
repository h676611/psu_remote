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
    Subclasses should implement the handle_get_command and handle_set_command methods for their specific PSU model.
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


    def refresh_status(self) -> None:
        self.server.send_status_to_GUI(psu_name=self.name)

    def add_command(self, identity: bytes | None, payload: dict) -> None:
        payload = process_payload(payload)
        self.queue.put((identity, payload))

    def worker(self):
        while True:
            identity, payload = self.queue.get()
            last_response: str | None = None
            reply_payload: dict = {

            }
            for command, args in payload.items():
                if command.startswith("get"):
                    last_response: str = self.handle_get_command(command, args)
                    reply_payload[command] = last_response

                elif command.startswith("set"):
                    self.handle_set_command(command, args)
                    reply_payload[command] = "OK"

                elif command == "refresh":
                    self.refresh_status()
            
            reply = {
                "type": "scpi_reply",
                "name": self.name,
                "payload": reply_payload
            }
            # If identity is None, command was added internally by the server, so we don't need to send a reply to any specific client
            if identity:
                self.server.send_response(identity, reply)

            # If any set command was processed, we want to update the GUI with the new status
            if any(key.startswith("set") for key in payload):
                self.server.send_status_to_GUI(psu_name=self.name)

    


            