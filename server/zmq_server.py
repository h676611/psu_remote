import queue
import threading
from typing import TYPE_CHECKING

import zmq

from logger import setup_logger

if TYPE_CHECKING:
    from .server import Server

logger = setup_logger("ZmqServer")


class ZmqServer:
    def __init__(self, server: "Server", address: str = "tcp://*:5555") -> None:
        self.server: "Server" = server
        self.context: zmq.Context = zmq.Context()
        self.socket: zmq.Socket = self.context.socket(zmq.ROUTER)
        self.socket.bind(address)
        self._outbound_messages: queue.Queue[tuple[bytes, dict]] = queue.Queue()
        self._stop_event: threading.Event = threading.Event()

    def send_response(self, identity: bytes, response: dict) -> None:
        self._outbound_messages.put((identity, response))

    def send_error(self, identity: bytes, message: str, psu_name: str | None) -> None:
        reply: dict = {
            "type": "error",
            "name": psu_name,
            "payload": {
                "message": message
            }
        }
        self.send_response(identity, reply)

    def stop(self) -> None:
        self._stop_event.set()

    def _flush_outbound_messages(self) -> None:
        while True:
            try:
                identity, response = self._outbound_messages.get_nowait()
            except queue.Empty:
                break

            self.socket.send(identity, zmq.SNDMORE)
            self.socket.send_json(response)

    def run(self) -> None:
        poller: zmq.Poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)

        while not self._stop_event.is_set():
            self._flush_outbound_messages()

            events = dict(poller.poll(50))
            if not events.get(self.socket):
                continue

            identity: bytes = self.socket.recv()
            request: dict = self.socket.recv_json()

            try:
                self.server.handle_request(identity, request)
            except Exception as exc:
                logger.error(f"Couldn't handle request. error: {exc}")
                self.send_error(identity=identity, message=str(exc), psu_name=request.get("name"))

        self._flush_outbound_messages()
        self.socket.close(0)
        self.context.term()