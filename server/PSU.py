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

    def _extract_k2400_measurement(self, command: str, response: str) -> float | None:
        """Extract measurement values from k2400 response (which contains multiple values)."""
        if command == "MEAS:VOLT?":
            # return the first value from the comma-separated response
            voltage_str = response.split(",")[0].strip()
            return float(voltage_str)
        elif command == "MEAS:CURR?":
            # return the second value from the comma-separated response
            current_str = response.split(",")[1].strip()
            return float(current_str)
        return None

    def _convert_to_float(self, response: str) -> float | None:
        """Attempt to convert response string to float."""
        try:
            return float(response)
        except ValueError:
            self.logger.error(f"Response is not a float: {response}")
            return None

    def query(self, command: str) -> str | float:
        """Execute a SCPI query command and return the response.
        
        For k2400, special handling is applied for measurement commands.
        Attempts to convert numeric responses to float.
        """
        response: str = self.resource.query(command)

        # Special handling for k2400 measurements (returns comma-separated values)
        if self.name == "k2400":
            value = self._extract_k2400_measurement(command, response)
            if value is not None:
                return value

        # Try to convert response to float
        numeric_value = self._convert_to_float(response)
        return numeric_value if numeric_value is not None else response

    def write(self, command: str) -> None:
        if self.name == "k2450" and command.startswith("SOUR:VOLT"):
            # special handling for k2450, need to query voltage after setting it to ensure it was set correctly

            self.resource.query(f"{command};:MEAS:VOLT?")
        else:
            self.resource.write(command)