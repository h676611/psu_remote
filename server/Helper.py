
from server.Translate import get_dic_for_PSU


class Helper:
    def __init__(self, PSU):
        self.psu = PSU
        self.dic = get_dic_for_PSU(self.psu.name)
    
    def cli_to_scpi(self, command, args):
        base_scpi = self.dic.get(command)


        if base_scpi is None:
            raise ValueError(f"Unknown command: {command}")

        # No arguments
        if args is None or args == '':
            scpi_cmd = base_scpi
            # logger.debug(f'converted command: {scpi_cmd}')
            return scpi_cmd
        # ardument is list or tuple
        elif isinstance(args, (list, tuple)):
            scpi_cmd = base_scpi.format(*args)
        # argument is single value
        elif isinstance(args, (int, float, str)):
            scpi_cmd = base_scpi.format(args)
        
        return scpi_cmd
    
        
    def seperate_aggregated_commands(self, payload):
        # This function takes a payload with aggregated commands and seperates them into individual commands
        # We will turn the cli command into the scpi command, check for a ";" seperate the commands and then turn them back into cli commands and add them to the queue
        new_payload = {}
        for command, args in payload.items():
            scpi_cmd = self.cli_to_scpi(command, args)
            if ";" in scpi_cmd:
                scpi_commands = scpi_cmd.split(";")
                for i in range(len(scpi_commands)):
                    cli_command = self.scpi_to_cli(scpi_commands[i])
                    new_payload[cli_command] = float(args[i])
                payload.clear()
                payload.update(new_payload)
        
    def scpi_to_cli(self, scpi_cmd):
        # This function takes a scpi command and turns it back into a cli command by looking for the scpi command in the dic and returning the corresponding cli command
        for cli_command, scpi_command in self.dic.items():
            if scpi_cmd.startswith(scpi_command.split("{")[0]): # we split the scpi command at the "{" to ignore the arguments when comparing
                return cli_command
        raise ValueError(f"Unknown scpi command: {scpi_cmd}")