import re
from logger import setup_logger
from .Translate import get_dic_for_PSU
from pyvisa.resources import Resource


class PSU:
    """Represents a Power Supply Unit with SCPI command handling."""
    def __init__(self, resource : Resource, num_channels: int = 1, name: str | None = None):
        self.name: str | None = name
        self.logger = setup_logger(name=name)
        
        self.num_channels: int = num_channels
        if self.name == "hmp4040":
            self.num_channels = 4

        self.resource: Resource = resource

        self.connected: bool = False
        
        self.address: str = resource.resource_name

    def query(self, command: str) -> str:
        self.logger.info(f"Querying command: {command}")

        if self.name == "k2400": # special handling for k2400, returns an array
            if command == "MEAS:VOLT?":
                voltage_response: str = self.resource.query(command)
                voltage_str: str = voltage_response.split(",")[0].strip()
                return float(voltage_str)
            if command == "MEAS:CURR?":
                current_response: str = self.resource.query(command)
                current_str: str = current_response.split(",")[1].strip() #for lab testing
                #current_str = current_response.split(",")[0].strip()
                return float(current_str)
            response: str = self.resource.query(command)

        else:
            response: str = self.resource.query(command)
        self.logger.debug(f"Received response: {response}")
        return response

    def write(self, command: str) -> None:
        if self.name == "k2450" and command.startswith("SOUR:VOLT"):
            #self.resource.write(command)
            self.logger.info(f'writing {command};:MEAS:VOLT?')
            self.resource.query(f"{command};:MEAS:VOLT?")
        else:
            self.logger.info(f'writing {command}')
            self.resource.write(command)
            
    
    def read(self) -> str:
        buffer = self.resource.read()
        self.logger.info(f"reading buffer: {buffer}")
        return buffer
            