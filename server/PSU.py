import re
from logger import setup_logger
from .Translate import get_dic_for_PSU

class PSU:
    """Represents a Power Supply Unit with SCPI command handling."""
    def __init__(self, resource, num_channels=4, name="hmp4040"):
        self.name = name
        self.logger = setup_logger(name=name)
        
        self.num_channels = num_channels
        if self.name != "hmp4040":
            self.num_channels = 1

        self.resource = resource

        #self.resource.timeout = 5000  # Set a timeout for resource operations
        
        #self.resource.read_termination = "\r"
        #self.resource.write_termination = "\n"

        self.connected = False
        
        self.address = resource.resource_name

    def query(self, command):

        #command = fr"{command}\r"
        #self.logger.debug(rf"command: {command}")
        if self.name == "k2400":
            if command == "MEAS:VOLT?":
                voltage_response = self.resource.query(command)
                voltage_str = voltage_response.split(",")[0].strip()
                return float(voltage_str)
            if command == "MEAS:CURR?":
                current_response = self.resource.query(command)
                current_str = current_response.split(",")[1].strip() #for lab testing
                #current_str = current_response.split(",")[0].strip()
                return float(current_str)
        if self.name == "hmp4040":
            response = self.resource.query(command)
            # self.resource.write(command)
            # response = self.resource.read(command)
            self.logger.debug(f'querying {command}, got response: {response}')
            
        else:
                response = self.resource.query(command)
                # self.resource.write(command)
                # response = self.resource.read(command)
        return response

    def write(self, command):
        self.logger.debug(f'writing {command}')
        self.resource.write(command)
            