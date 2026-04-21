import zmq
class ZMQClient:
   def __init__(self, address="tcp://localhost:5555"):
      self.context = zmq.Context()
      self.socket = self.context.socket(zmq.DEALER)
      self.socket.connect(address)

   def send_receive(self, request):
      self.socket.send_json(request)
      reply = self.socket.recv_json()
      return reply