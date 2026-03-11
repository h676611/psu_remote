from PyQt5 import QtCore
import zmq, threading, time
from logger import setup_logger

logger = setup_logger(name="zmq_client")

class ZmqClient(QtCore.QObject):
    """A ZeroMQ client integrated with PyQt5 for asynchronous communication with the server."""

    reply_received = QtCore.pyqtSignal(int, dict)
    status_update_received = QtCore.pyqtSignal(dict)
    error_received = QtCore.pyqtSignal(dict)

    def __init__(self, address="tcp://localhost:5555", status_address="tcp://localhost:5556"):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(address)
        self._next_id = 0
        self._pending = set()

        # Polling thread for server replies
        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    @QtCore.pyqtSlot(dict)
    def send(self, request: dict):
        request_id = self._next_id
        self._next_id += 1
        request["request_id"] = request_id
        self._pending.add(request_id)

        self.socket.send_json(request)

        logger.info(f"Sending request: {request}")

    def _poll_loop(self):
        poller = zmq.Poller() # lag poller for flere sockets
        poller.register(self.socket, zmq.POLLIN) # følg med DEALER
        while self._running:
            try:
                msg = self.socket.recv_json(flags=zmq.NOBLOCK)
                msg_type = msg.get("type")
                request_id = msg.get("request_id")

                logger.info(f'received: {msg}')

                if msg_type in ("scpi_reply", "system_reply"):
                    if request_id in self._pending:
                        self._pending.remove(request_id)
                        self.reply_received.emit(request_id, msg)
                    else:
                        logger.error(f'received reply with wrong request id')
                elif msg_type == "status_update":
                    self.status_update_received.emit(msg)
                elif msg_type == "error":
                    self.error_received.emit(msg)

            except zmq.Again:
                time.sleep(0.01)

    def stop(self):
        self._running = False
        self._poll_thread.join()
        # lukker begge sockets når gui lukkes
        self.socket.close()
        self.sub_socket.close()
