import logger
from server import PSU
from server.Translate import get_dic_for_PSU
from .k6500_queue import K6500Queue
from .hmp4040_queue import HMP4040Queue
from .k2400_queue import K2400Queue
from .k2450_queue import K2450Queue
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .server import Server
    from .psu_queue import PSUQueue

logger = logger.setup_logger("Helper")
class Helper:
    """Helper class to convert CLI commands to SCPI commands based on the PSU's command dictionary."""
    def __init__(self, PSU: PSU):
        self.psu = PSU
        self.dic: dict = get_dic_for_PSU(self.psu.name)

    def cli_to_scpi(self, command: str, args: list | tuple | None) -> str:
        base_scpi: str | None = self.dic.get(command)


        if base_scpi is None:
            raise ValueError(f"Unknown command: {command} for PSU {self.psu.name}")

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

            # maybe convert scientific notation...
            scpi_cmd = base_scpi.format(args)
        
        return scpi_cmd
    
def make_queue(psu: PSU, server: "Server") -> "PSUQueue":
    queue: PSUQueue | None = None
    if psu.name == "k6500":
        queue = K6500Queue(psu=psu, server=server)
    elif psu.name == "hmp4040":
        queue = HMP4040Queue(psu=psu, server=server)
    elif psu.name == "k2400":
        queue = K2400Queue(psu=psu, server=server)
    elif psu.name == "k2450":
        queue = K2450Queue(psu=psu, server=server)
    else:
        raise ValueError(f"Unknown PSU name: {psu.name}")
    return queue
