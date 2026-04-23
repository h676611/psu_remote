from .zmq_client import ZMQClient
import ordered_argparse
from collections import OrderedDict
from .helper import process_payload


def run_cli(parser_class: type, psu_name: str, inargs=None) -> dict:
    parser: ordered_argparse.ArgumentParser = parser_class()
    args: ordered_argparse.OrderedNamespace = parser.parse_args(inargs, namespace=ordered_argparse.OrderedNamespace())

    payload: OrderedDict = OrderedDict(
        (k, v) for k, v in args.ordered()
        if v is not None and v is not False
    )

    request: dict = {
        "name": psu_name,
        #"payload": process_payload(payload)
        "payload": payload
    }

    print(request)

    zmq_client: ZMQClient = ZMQClient()
    try:
        reply: dict = zmq_client.send_receive(request)
    except KeyboardInterrupt:
        reply = {
            "type": "error",
            "payload": {"message": "Interrupted while waiting for server reply"}
        }
    finally:
        zmq_client.close()
    print(reply)

    return reply
