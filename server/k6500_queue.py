
from logger import setup_logger
from server.PSU import PSU
from server.Translate import get_dic_for_PSU
from server.psu_queue import PSUQueue
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .server import Server

logger = setup_logger("K6500queue")


class K6500Queue(PSUQueue):
    """Queue class for controlling the K6500 power supply, handling command translation and status updates."""
    def __init__(self, psu: PSU, server: "Server"):
        super().__init__(psu=psu, server=server)
        self.server = server
        self.name: str = "k6500"
        self.dic: dict = get_dic_for_PSU(self.name)
        self.num_channels: int = 10
        self.status: dict = {channel: {"voltage": 0.0} for channel in range(1, self.num_channels + 1)}


    def handle_get_command(self, command: str, args: list | tuple | None) -> str:

        scpi_cmd: str = self.helper.cli_to_scpi(command, args)
    
        last_response: str = self.psu.query(scpi_cmd)
        
        if command == "get_channel_voltage":
            channel: int = int(args)
            try:
                self.status[channel]["voltage"] = float(last_response)
            except (ValueError, TypeError) as e:
                self.status[channel]["voltage"] = last_response
                logger.error(f"Error parsing response for {command} with args {args}: {last_response} - Error: {e}")

        self.server.send_status_to_GUI(psu_name=self.name)

        return last_response
    

    def handle_set_command(self, command: str, args: list | tuple | None) -> None:
        try:
            scpi_cmd: str = self.helper.cli_to_scpi(command, args)

            self.psu.query(scpi_cmd)
            if command == "set_voltage":
                channel: int = int(args[0])
                voltage: float = float(args[1])
                self.status[channel]["voltage"] = voltage

        except Exception as e:
            logger.error(f"Error processing command {command} in k6500 queue with args {args}: {e}")
            pass
        