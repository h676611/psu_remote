import queue
import threading

import zmq


class ZMQClient:
   def __init__(self, address: str = "tcp://localhost:5555"):
      self.context: zmq.Context = zmq.Context()
      self.socket: zmq.Socket = self.context.socket(zmq.DEALER)
      self.socket.connect(address)
      self._stop_event: threading.Event = threading.Event()

   def _wait_for_reply(self, reply_queue: queue.Queue) -> None:
      while not self._stop_event.is_set():
         try:
            reply_queue.put(self.socket.recv_json(flags=zmq.NOBLOCK))
            return
         except zmq.Again:
            self._stop_event.wait(0.05)
         except Exception as exc:
            reply_queue.put({
               "type": "error",
               "payload": {"message": f"Failed to receive reply: {exc}"}
            })
            return

   def send_receive(self, request: dict) -> dict:
      self._stop_event.clear()
      reply_queue: queue.Queue = queue.Queue(maxsize=1)
      wait_thread = threading.Thread(
         target=self._wait_for_reply,
         args=(reply_queue,),
         daemon=True,
      )
      wait_thread.start()
      self.socket.send_json(request)

      try:
         while wait_thread.is_alive():
            wait_thread.join(0.1)
      except KeyboardInterrupt:
         self._stop_event.set()
         raise

      if not reply_queue.empty():
         return reply_queue.get()

      return {
         "type": "error",
         "payload": {"message": "Stopped before receiving reply"}
      }

   def close(self) -> None:
      self._stop_event.set()
      self.socket.close(0)
      self.context.term()