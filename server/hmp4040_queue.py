from server.PSU import PSU
from typing import TYPE_CHECKING
from .psu_queue import PSUQueue
from .Translate import get_dic_for_PSU
from logger import setup_logger

if TYPE_CHECKING:
    from .server import Server

logger = setup_logger("HMP4040queue")

class HMP4040Queue(PSUQueue):
    def __init__(self, psu: PSU, server: "Server"):
        super().__init__(psu=psu, server=server)
        self.name: str = "hmp4040"
        self.dic: dict = get_dic_for_PSU(self.name)
        self.status: dict = {
            1: {
                "voltage": 0.0,
                "current": 0.0,
                "output": 0
            },
            2: {
                "voltage": 0.0,
                "current": 0.0,
                "output": 0
            },
            3: {
                "voltage": 0.0,
                "current": 0.0,
                "output": 0
            },
            4: {
                "voltage": 0.0,
                "current": 0.0,
                "output": 0
            }   
        }
        self.selected_channel = 1

    def handle_get_command(self, command: str, args: list | tuple | int | None) -> str:

        scpi_cmd: str = self.helper.cli_to_scpi(command, args)

        logger.info(f"Querying command: {scpi_cmd}")
        last_response: str = self.psu.query(scpi_cmd)
        
        
        
        #TODO lag mer elegant
        if command == "get_display_voltage":
            self.status[1]["voltage"] = float(last_response)
        elif command == "get_display_current":
            self.status[1]["current"] = float(last_response)
        elif command.startswith("get_channel_"):
            try:
                if command.endswith("current"):
                    self.status[args]["current"] = float(last_response)
                elif command.endswith("voltage"):
                    self.status[args]["voltage"] = float(last_response)
                elif command.endswith("output"):
                    self.status[args]["output"] = int(last_response)
            except AttributeError:
                logger.error(f"Error parsing response for {command}: {last_response}")

        logger.info(f"Response: {last_response}")

        return last_response

    def handle_set_command(self, command: str, args: list | tuple | None) -> None:
        try:

            scpi_cmd: str = self.helper.cli_to_scpi(command, args)

            logger.info(f"Writing (query) command: {scpi_cmd}")

            last_response: str = self.psu.write(scpi_cmd)
            # logger.info(f"Response from write (query): {last_response}")

            if command == "set_channel":
                self.selected_channel = args
            elif command == "set_voltage":
                self.status[self.selected_channel]["voltage"] = args
            elif command == "set_current":
                self.status[self.selected_channel]["current"] = args
            elif command == "set_output":
                self.status[self.selected_channel]["output"] = args

            return args

        except Exception as e:
            logger.error(f"Error processing command {command} in hmp4040 queue with args {args}: {e}")
            pass
        