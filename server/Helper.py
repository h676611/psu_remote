import logger
from server.Translate import get_dic_for_PSU
from .server import k6500Queue, hmp4040Queue, k2400Queue, k2450Queue

logger = logger.setup_logger("Helper")
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
                    if isinstance(args, (list, tuple)) and i < len(args):
                        if cli_command == "set_channel": # if the command is set channel we need to make sure the argument is an integer and not a float since the psu expects an integer for the channel number
                            new_payload[cli_command] = int(args[i])
                        else:
                            new_payload[cli_command] = float(args[i])
                    else:
                        new_payload[cli_command] = float(args)
            else:
                new_payload[command] = args

        logger.debug(f"Seperated aggregated command: {new_payload}")
        return new_payload
        
    def scpi_to_cli(self, scpi_cmd):
        # This function takes a scpi command and turns it back into a cli command by looking for the scpi command in the dic and returning the corresponding cli command
        for cli_command, scpi_command in self.dic.items():
            if scpi_cmd.startswith(scpi_command.split("{")[0]): # we split the scpi command at the "{" to ignore the arguments when comparing
                logger.debug(f'converted command: {cli_command}')
                return cli_command
        raise ValueError(f"Unknown scpi command: {scpi_cmd}")
    
def make_queue(psu, server):
    queue = None
    if psu.name == "k6500":
        queue = k6500Queue(psu=psu, server=server)
    elif psu.name == "hmp4040":
        queue = hmp4040Queue(psu=psu, server=server)
    elif psu.name == "k2400":
        queue = k2400Queue(psu=psu, server=server)
    elif psu.name == "k2450":
        queue = k2450Queue(psu=psu, server=server)
    else:
        raise ValueError(f"Unknown PSU name: {psu.name}")
    return queue