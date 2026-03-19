import re
from logger import setup_logger
from .Translate import get_dic_for_PSU

logger = setup_logger("PSU")
class PSU:
    """Represents a Power Supply Unit with SCPI command handling."""
    def __init__(self, resource, num_channels=4, name="hmp4040"):
        self.name = name
        logger.name = name
        self.num_channels = num_channels
        if self.name != "hmp4040":
            self.num_channels = 1

        self.resource = resource

        self.connected = False
        
        self.address = resource.resource_name

    def query(self, command):

        if self.name == "k2400":
            if command == "MEAS:VOLT?":
                voltage_response = self.resource.query(command)
                voltage_str = voltage_response.split(",")[0].strip()
                return float(voltage_str)
            if command == "MEAS:CURR?":
                current_response = self.resource.query(command)
                current_str = current_response.split(",")[1].strip()
                return float(current_str)
        response = self.resource.query(command)
        logger.debug(f'querying {command}, got response: {response}')
        if self.name == "hmp4040":
            response = self.resource.read()
        return response

    def write(self, command):
        self.resource.write(command)
        logger.debug(f'reading {self.resource.read()}')
        logger.debug(f'writing {command}')
            