
from logger import setup_logger
from server.Translate import get_dic_for_PSU
from server.psu_queue import PSUQueue

logger = setup_logger("K6500queue")


class K6500Queue(PSUQueue):
    def __init__(self, psu, server):
        super().__init__(psu, server)
        self.name = "k6500"
        self.dic = get_dic_for_PSU(self.name)
        self.num_channels = 10
        self.status = {channel: {"voltage": 0.0} for channel in range(1, self.num_channels + 1)}



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

            self.psu.query(scpi_cmd)
            if command == "set_voltage":
                channel = int(args[0])
                voltage = float(args[1])
                self.status[channel]["voltage"] = voltage

        except Exception as e:
            logger.error(f"Error processing command {command} in k6500 queue with args {args}: {e}")
            pass

    
    def refresh_status(self):
        try:
            for channel in range(1, self.num_channels + 1):
                self.psu.write(self.dic["set_channel"].format(channel))
                voltage = self.psu.query(self.dic["get_voltage"])
                self.status[channel]["voltage"] = 0.0 # Pretend to get voltage from psu because sim does not support querying voltage
                # self.status[channel]["voltage"] = float(voltage)
        except Exception as e:
            logger.error(f"Error refreshing status in k6500 queue: {e}")
            pass