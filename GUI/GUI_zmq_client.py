from PyQt5 import QtCore
import queue
import threading

import zmq
from logger import setup_logger

logger = setup_logger(name="zmq_client")

class ZmqClient(QtCore.QObject):
    """A ZeroMQ client integrated with PyQt5 for asynchronous communication with the server."""

    connect_GUI_received: QtCore.pyqtSignal = QtCore.pyqtSignal(dict)
    system_reply_received: QtCore.pyqtSignal = QtCore.pyqtSignal(dict)
    status_update_received: QtCore.pyqtSignal = QtCore.pyqtSignal(dict)
    error_received: QtCore.pyqtSignal = QtCore.pyqtSignal(dict)

    def __init__(self, address="tcp://10.0.0.2:5555"):
        super().__init__()
        self.address: str = address
        self._running: bool = True
        self._outbound_messages: queue.Queue[dict] = queue.Queue()
        self._io_thread: threading.Thread = threading.Thread(target=self._io_loop, daemon=True)
        self._io_thread.start()

    @QtCore.pyqtSlot(dict)
    def send(self, request: dict) -> None:
        # logger.info(f"Sending request: {request}")
        self._outbound_messages.put(request)

    def _io_loop(self) -> None:
        context: zmq.Context = zmq.Context()
        socket: zmq.Socket = context.socket(zmq.DEALER)
        socket.connect(self.address)

        poller: zmq.Poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

        while self._running:
            while True:
                try:
                    request: dict = self._outbound_messages.get_nowait()
                except queue.Empty:
                    break

                socket.send_json(request)

            events = dict(poller.poll(50))
            if not events.get(socket):
                continue

            try:
                msg: dict = socket.recv_json()
                msg_type: str = msg.get("type")

                # logger.info(f'received: {msg}')

                if msg_type in ("system_reply"):
                    if msg.get("payload", {}).keys() == {"connect_GUI"}:
                        self.connect_GUI_received.emit(msg)
                    else:
                        self.system_reply_received.emit(msg)
                # elif msg_type in ("status_update", "scpi_reply"):
                elif msg_type in ("status_update"):
                    self.status_update_received.emit(msg)
                elif msg_type == "error":
                    self.error_received.emit(msg)

            except zmq.Again:
                continue

        socket.close(0)
        context.term()

    def stop(self) -> None:
        self._running = False
        self._io_thread.join()

