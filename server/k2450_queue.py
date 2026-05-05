from time import sleep

from logger import setup_logger
from server.PSU import PSU
from server.psu_queue import PSUQueue
from .Translate import get_dic_for_PSU
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .server import Server

logger = setup_logger("K2450queue")

class K2450Queue(PSUQueue):
    def __init__(self, psu: PSU, server: "Server"):
        super().__init__(psu=psu, server=server)
        self.name: str = "k2450"
        self.dic: dict = get_dic_for_PSU(self.name)
        self.status: dict = {
            1: {
                "voltage": 0.0,
                "current": 0.0,
                "output": 0
            }   
        }

    def handle_get_command(self, command: str, args: list | tuple | None) -> str:

        scpi_cmd: str = self.helper.cli_to_scpi(command, args)
    
        logger.info(f"Querying command: {scpi_cmd}")
        last_response: str = self.psu.query(scpi_cmd)

        logger.info(f"Response: {last_response}")

        return last_response
    

    def handle_set_command(self, command: str, args: list | tuple | None) -> None:
        try:
            scpi_cmd: str = self.helper.cli_to_scpi(command, args)

            logger.info(f"Writing (query) command: {scpi_cmd}")

            self.psu.write(scpi_cmd)

            if command == "set_voltage":
                self.status[1]["voltage"] = args
            elif command == "set_current":
                self.status[1]["current"] = args
            elif command == "set_output":
                self.status[1]["output"] = args
                
            

        except Exception as e:
            logger.error(f"Error processing command {command} in k2450 queue with args {args}: {e}")
            pass

    
    def refresh_status(self) -> None:
        pass
        # try:
        #     voltage: str = self.psu.query(self.dic["get_display_voltage"])
        #     current: str = self.psu.query(self.dic["get_display_current"])

        #     self.status[1]["voltage"] = float(voltage)
        #     self.status[1]["current"] = float(current)

        # except Exception as e:
        #     logger.error(f"Error refreshing status in k2450 queue: {e}")
        #     pass