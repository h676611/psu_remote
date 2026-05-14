import json
from pathlib import Path

from .zmq_client import ZMQClient
import ordered_argparse
from collections import OrderedDict
from .helper import process_reply


def run_cli(parser_class: type, psu_name: str, inargs=None) -> None:
    """Runs the CLI for a given PSU model using the specified parser class."""
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

    # load config file relative to this module (not current working dir)
    config_file = {}
    try:
        config_path = Path(__file__).resolve().parents[1] / 'config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as file:
                config_file = json.load(file)
    except Exception:
        config_file = {}

    # fallback default address when config or key is missing
    address = config_file.get('zmq_address', 'tcp://10.0.0.2:5555')
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

    cmd, value = process_reply(reply)

    if verbose:
        print(f'{psu_name}: {cmd} -> {value}')
    else:
        if not cmd.startswith("set"):
            print(value)

