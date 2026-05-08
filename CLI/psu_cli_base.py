import json

from .zmq_client import ZMQClient
import ordered_argparse
from collections import OrderedDict
from .helper import process_payload


def run_cli(parser_class: type, psu_name: str, inargs=None) -> dict | None:
    parser: ordered_argparse.ArgumentParser = parser_class()
    args: ordered_argparse.OrderedNamespace = parser.parse_args(inargs, namespace=ordered_argparse.OrderedNamespace())

    payload: OrderedDict = OrderedDict(
        (k, v) for k, v in args.ordered()
        if v is not None and v is not False
    )
    # remove key for verbose flag if it exists
    verbose = payload.pop("verbose", False)


    request: dict = {
        "name": psu_name,
        "payload": payload
    }

    # relative import of config file to get zmq address
    try:
        with open('config.json', 'r') as file:
            config_file = json.load(file)
    except FileNotFoundError:
        pass


    address = config_file.get('zmq', {}).get('client_address', 'tcp://10.0.0.2:5555')
    zmq_client: ZMQClient = ZMQClient(address=address)
    try:
        reply: dict = zmq_client.send_receive(request)
    except KeyboardInterrupt:
        reply = {
            "type": "error",
            "payload": {"message": "Interrupted while waiting for server reply"}
        }
    finally:
        zmq_client.close()


    value = None
    set_cmd = False
    for command, response in reply.get("payload", {}).items():
        if command.startswith("get"):
            try:
                value = float(response)
            except (ValueError, TypeError):
                value = response
        else:
            value = response
        if command.startswith("set"):
            set_cmd = True


    if verbose:
        name = request.get("name", "unknown")
        payload = request.get("payload", {})
        cmd = payload.keys()
        for cmd in payload.keys():
            print(f'{name}: {cmd} -> {value}')

    if set_cmd:
        return None

    return value
