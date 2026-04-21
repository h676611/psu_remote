

from server.Translate import get_dic_for_PSU
from server.psu_queue import PSUQueue
from logger import setup_logger

logger = setup_logger("K2400queue")

class K2400Queue(PSUQueue):
    def __init__(self, psu, server):
        super().__init__(psu, server)
        self.name = "k2400"
        self.dic = get_dic_for_PSU(self.name)
        self.status ={
            1: {
                "voltage": 0.0,
                "current": 0.0,
                "output": 0
            }   
        }

    
    def handle_get_command(self, command, args):

        scpi_cmd = self.helper.cli_to_scpi(command, args)
    
        logger.info(f"Querying command: {scpi_cmd}")
        last_response = self.psu.query(scpi_cmd)

        logger.info(f"Response: {last_response}")

        return last_response
    

    def handle_set_command(self, command, args):
        try:
            scpi_cmd = self.helper.cli_to_scpi(command, args)

            logger.info(f"Writing (query) command: {scpi_cmd}")

            self.psu.write(scpi_cmd)

            if command == "set_voltage":
                self.status[1]["voltage"] = args
            elif command == "set_current":
                self.status[1]["current"] = args
            elif command == "set_output":
                self.status[1]["output"] = args

        except Exception as e:
            logger.error(f"Error processing command {command} in k2400 queue with args {args}: {e}")
            pass

    
    def refresh_status(self):
        try:
            voltage = self.psu.query(self.dic["get_voltage"])
            current = self.psu.query(self.dic["get_current"])


            self.status[1]["voltage"] = float(voltage)
            self.status[1]["current"] = float(current)

        except Exception as e:
            logger.error(f"Error refreshing status in k2400 queue: {e}")
            pass