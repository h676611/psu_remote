import os
import re
import sys
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.psu_queue import PSUQueue


class FakeResource:
	def __init__(self, resource_name):
		self.resource_name = resource_name


class FakePSU:
	"""Thread-safe PSU simulation that records write order and emulates state."""

	def __init__(self, resource_name="SIM::HMP4040"):
		self.name = "hmp4040"
		self.address = resource_name
		self.resource = FakeResource(resource_name)

		self._lock = threading.Lock()
		self._active_channel = 1
		self._channels = {
			1: {"voltage": 0.0, "current": 0.0, "output": "0"},
			2: {"voltage": 0.0, "current": 0.0, "output": "0"},
			3: {"voltage": 0.0, "current": 0.0, "output": "0"},
			4: {"voltage": 0.0, "current": 0.0, "output": "0"},
		}
		self.write_log = []

	def write(self, command):
		with self._lock:
			self.write_log.append(command)

			channel_match = re.match(r"^INST OUT(\d+)$", command)
			if channel_match:
				self._active_channel = int(channel_match.group(1))
				return

			voltage_match = re.match(r"^VOLT ([+-]?(?:\d+(?:\.\d*)?|\.\d+))$", command)
			if voltage_match:
				voltage = float(voltage_match.group(1))
				self._channels[self._active_channel]["voltage"] = voltage
				return

			current_match = re.match(r"^CURR ([+-]?(?:\d+(?:\.\d*)?|\.\d+))$", command)
			if current_match:
				current = float(current_match.group(1))
				self._channels[self._active_channel]["current"] = current
				return

			output_match = re.match(r"^OUTP (\d+)$", command)
			if output_match:
				self._channels[self._active_channel]["output"] = output_match.group(1)

	def query(self, command):
		with self._lock:
			channel = self._channels[self._active_channel]
			if command == "MEAS:VOLT?":
				return f"{channel['voltage']:.2f}"
			if command == "MEAS:CURR?":
				return f"{channel['current']:.2f}"
			if command == "OUTP?":
				return channel["output"]
			return "OK"


class FakeServer:
	def __init__(self):
		self._lock = threading.Lock()
		self.replies = []

	def send_response(self, identity, response):
		with self._lock:
			self.replies.append((identity, response))


def _wait_for_replies(server, expected_count, timeout_s=5.0):
	deadline = time.time() + timeout_s
	while time.time() < deadline:
		with server._lock:
			if len(server.replies) >= expected_count:
				return
		time.sleep(0.01)
	raise TimeoutError(
		f"Timed out waiting for replies. Expected {expected_count}, got {len(server.replies)}"
	)


def test_hmp4040_concurrent_set_channel_set_voltage_are_atomic():
	"""
	Simulate many concurrent clients. Each client sends one payload with:
	set_channel + set_voltage.

	The queue worker must process each payload atomically, so in the global write log
	each request appears as adjacent commands:
	INST OUTx immediately followed by VOLT y.
	"""

	fake_psu = FakePSU(resource_name="ASRL5::INSTR")
	fake_server = FakeServer()
	psu_queue = PSUQueue(psu=fake_psu, server=fake_server)

	requests = []
	request_count = 24
	for idx in range(request_count):
		channel = (idx % 4) + 1
		voltage = round(1.0 + (idx * 0.37), 2)
		request_id = f"req-{idx}"
		requests.append((f"client-{idx % 6}".encode(), channel, voltage, request_id))

	start_barrier = threading.Barrier(len(requests))

	def producer(identity, channel, voltage, request_id):
		start_barrier.wait()
		payload = {
			"set_channel": channel,
			"set_voltage": voltage,
		}
		psu_queue.add_command(identity, payload, request_id=request_id)

	producer_threads = []
	for identity, channel, voltage, request_id in requests:
		thread = threading.Thread(
			target=producer,
			args=(identity, channel, voltage, request_id),
			daemon=True,
		)
		producer_threads.append(thread)
		thread.start()

	for thread in producer_threads:
		thread.join(timeout=2.0)
		assert not thread.is_alive(), "Producer thread did not finish"

	_wait_for_replies(fake_server, request_count, timeout_s=8.0)

	write_log = fake_psu.write_log
	expected_write_count = request_count * 2
	assert len(write_log) == expected_write_count, (
		f"Expected {expected_write_count} writes, got {len(write_log)}"
	)

	expected_pairs = {
		(f"INST OUT{channel}", f"VOLT {voltage}")
		for _, channel, voltage, _ in requests
	}

	seen_pairs = []
	for i in range(0, len(write_log), 2):
		pair = (write_log[i], write_log[i + 1])
		seen_pairs.append(pair)

		assert re.match(r"^INST OUT\d+$", pair[0]), f"First command must set channel, got: {pair[0]}"
		assert re.match(r"^VOLT [+-]?(?:\d+(?:\.\d*)?|\.\d+)$", pair[1]), (
			f"Second command must set voltage, got: {pair[1]}"
		)

	assert set(seen_pairs) == expected_pairs, (
		"Detected intermixing or missing command pairs. "
		f"Expected pairs: {expected_pairs}. Seen pairs: {set(seen_pairs)}"
	)

	request_ids = {request_id for _, _, _, request_id in requests}
	reply_request_ids = {reply["request_id"] for _, reply in fake_server.replies}
	assert reply_request_ids == request_ids, "Not all requests produced replies"


if __name__ == "__main__":
	test_hmp4040_concurrent_set_channel_set_voltage_are_atomic()
	print("Concurrent HMP4040 simulation test passed")

