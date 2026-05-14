import zmq


class ZMQClient:
   """ZeroMQ client for sending requests and receiving replies from the server."""
   def __init__(self, address: str = "tcp://10.0.0.2:5555"):
      self.context: zmq.Context = zmq.Context()
      self.socket: zmq.Socket = self.context.socket(zmq.DEALER)
      self.socket.connect(address)

   def send_receive(self, request: dict) -> dict:
      self.socket.send_json(request)

      poller: zmq.Poller = zmq.Poller()
      poller.register(self.socket, zmq.POLLIN)

      while True:
         events = dict(poller.poll(100))
         if events.get(self.socket):
            try:
               return self.socket.recv_json()
            except Exception as exc:
               return {
                  "type": "error",
                  "payload": {"message": f"Failed to receive reply: {exc}"}
               }

   def close(self) -> None:
      self.socket.close(0)
      self.context.term()