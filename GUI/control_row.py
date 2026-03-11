import json
import uuid
from PyQt5 import QtWidgets, QtCore
from logger import setup_logger

logger = setup_logger("Control row")

class ControlRow(QtWidgets.QWidget):
    """A GUI control row for a single instrument, allowing connection management and SCPI command sending."""
    send_request = QtCore.pyqtSignal(dict)

    def __init__(self, instrument_name, row_name, parent=None):
        super().__init__(parent)
        self.instrument_name = instrument_name

        self.connected = False
        self._prev_connected = False

        self.row_name = row_name
        
        # Main container
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # 1. Create lists to store your widgets so you can access them later
        self.rows = [] 
        
        num_rows = 4 if instrument_name == "hmp4040" else 1


        top_layout = QtWidgets.QHBoxLayout()

        main_layout.addLayout(top_layout)

        self.name_label = QtWidgets.QLabel(self.row_name)
        top_layout.addWidget(self.name_label)

        # connect button
        self.toggle_button = QtWidgets.QPushButton("Start")
        self.toggle_button.clicked.connect(self.on_toggle)
        top_layout.addWidget(self.toggle_button)

        # Error display
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)

        # Header labels
        header_layout = QtWidgets.QHBoxLayout()

        main_layout.addLayout(header_layout)

        self.channel_label = QtWidgets.QLabel("Channel")
        header_layout.addWidget(self.channel_label)

        self.voltage_label = QtWidgets.QLabel("Voltage [V]")
        header_layout.addWidget(self.voltage_label)

        self.current_label = QtWidgets.QLabel("Current [A]")
        header_layout.addWidget(self.current_label)

        self.output_label = QtWidgets.QLabel("Output")
        header_layout.addWidget(self.output_label)

        self.send_label = QtWidgets.QLabel("Send")
        header_layout.addWidget(self.send_label)

        self.meas_voltage_label = QtWidgets.QLabel("Meas. V")
        header_layout.addWidget(self.meas_voltage_label)

        self.meas_current_label = QtWidgets.QLabel("Meas. A")
        header_layout.addWidget(self.meas_current_label)

        self.meas_output_label = QtWidgets.QLabel("Status")
        header_layout.addWidget(self.meas_output_label)

        for i in range(num_rows):
            row_layout = QtWidgets.QHBoxLayout()

            row_layout_top = QtWidgets.QVBoxLayout()
            
            # Create a dictionary to hold this row's widgets
            row_widgets = {}

            # Label
            label_text = f"{i+1}" if num_rows > 1 else instrument_name
            row_widgets['label'] = QtWidgets.QLabel(label_text)
            row_layout.addWidget(row_widgets['label'])

            # Voltage Input
            row_widgets['voltage_input'] = QtWidgets.QDoubleSpinBox()
            row_widgets['voltage_input'].setSuffix(' V')
            row_widgets['voltage_input'].setRange(-100., 100.)
            row_layout.addWidget(row_widgets['voltage_input'])

            # Current Input
            row_widgets['current_input'] = QtWidgets.QDoubleSpinBox()
            row_widgets['current_input'].setSuffix(' A')
            row_widgets['current_input'].setRange(-10., 10.)
            row_layout.addWidget(row_widgets['current_input'])

            # Output on/off
            row_widgets['on_off_channel_toggle'] = QtWidgets.QCheckBox()
            row_layout.addWidget(row_widgets["on_off_channel_toggle"])

            # Send Button
            send_btn = QtWidgets.QPushButton(f"Send")
            
            # 2. Use lambda with a default variable 'row=i' to capture the current index
            send_btn.clicked.connect(
                lambda checked, row=i, toggle=row_widgets["on_off_channel_toggle"]:
                    self.on_row_submitted(row, toggle.isChecked())
            )
            row_layout.addWidget(send_btn)

            # Measured value labels (read-only live feedback)
            row_widgets['meas_voltage'] = QtWidgets.QLabel("—")
            row_widgets['meas_voltage'].setStyleSheet("color: #2196F3; font-weight: bold;")
            row_layout.addWidget(row_widgets['meas_voltage'])

            row_widgets['meas_current'] = QtWidgets.QLabel("—")
            row_widgets['meas_current'].setStyleSheet("color: #2196F3; font-weight: bold;")
            row_layout.addWidget(row_widgets['meas_current'])

            row_widgets['meas_output'] = QtWidgets.QLabel("—")
            row_widgets['meas_output'].setStyleSheet("color: #888; font-weight: bold;")
            row_layout.addWidget(row_widgets['meas_output'])

            # Store the dictionary in our list and add layout to screen
            self.rows.append(row_widgets)
            main_layout.addLayout(row_layout)


    def on_toggle(self):
        if not self.connected:
            self.start()
        else:
            self.stop()

    def start(self):

        # TODO generate request with function
        self._prev_connected = self.connected
        payload = {
            'connect': True
        }
        request = {
            'name': self.instrument_name,
            'payload': payload
        }
        self.error_label.hide()
        self.send_request.emit(request)
        self.toggle_button.setText("Stop")
        self.connected = True


    def stop(self):

        # TODO generate request with function
        self._prev_connected = self.connected
        payload = {
            'disconnect': True
        }
        request = {
            'name': self.instrument_name,
            'payload': payload
        }
        self.error_label.hide()
        self.send_request.emit(request)
        self.toggle_button.setText("Start")
        self.connected = False

    @QtCore.pyqtSlot(int, dict)
    def handle_reply(self, request_id, reply):
        if reply.get("name") != self.instrument_name:
            return
        #logger.info(f"received reply: {reply}")

        if reply.get("type") == "refresh_reply":
            self.update_from_refresh(reply["payload"])
            return

        # TODO [KAN-19] handle replies

    @QtCore.pyqtSlot(dict)
    def handle_status_update(self, msg):
        if msg.get("name") != self.instrument_name:
            return
        logger.info(f'received status update: {msg}')

        # TODO
        status = msg.get("status")


        if not isinstance(status, dict): # bare håndter dict status payloads og ignorerer alt annet
            logger.error(f"Received status update with invalid format: {status}")
            return
        for index, row in enumerate(self.rows): # gå igjennom kanaler
            channel = index + 1
            # Server sends channel keys as ints, but JSON may convert to strings
            channel_state = status.get(channel)
            if channel_state is None:
                channel_state = status.get(str(channel))
            if not isinstance(channel_state, dict): # skip om kanalen ikke har status
                continue
            if "get_voltage" in channel_state:
                try:
                    row["meas_voltage"].setText(f"{float(channel_state['get_voltage']):.3f} V")
                except (ValueError, TypeError):
                    row["meas_voltage"].setText(str(channel_state["get_voltage"]))
            if "get_current" in channel_state:
                try:
                    row["meas_current"].setText(f"{float(channel_state['get_current']):.3f} A")
                except (ValueError, TypeError):
                    row["meas_current"].setText(str(channel_state["get_current"]))
            if "get_output" in channel_state:
                try:
                    outp_on = bool(int(float(str(channel_state["get_output"]))))
                except (ValueError, TypeError):
                    outp_on = False
                row["meas_output"].setText("ON" if outp_on else "OFF")
                row["meas_output"].setStyleSheet(
                    f"color: {'#4CAF50' if outp_on else '#F44336'}; font-weight: bold;"
                )

    
    @QtCore.pyqtSlot(dict)
    def handle_error(self, message):
        if message.get("name") != self.instrument_name:
            return
        logger.error(f"received error: {message}")
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        error_msg = payload.get("message", "Unknown error")
        self.error_label.setText(f"Error: {error_msg}")
        self.error_label.show()
        self.connected = self._prev_connected
        self.toggle_button.setText("Stop" if self.connected else "Start")

    # 3. The function that handles the logic
    def on_row_submitted(self, row_index, output_checked):
        # Access the specific widgets using the row_index
        target_row = self.rows[row_index]
        v_val = target_row['voltage_input'].value()
        i_val = target_row['current_input'].value()
        channel = row_index + 1
        
        payload = {}
        if self.instrument_name == "hmp4040": 
            payload['set_channel'] = channel

        # TODO [KAN-21] generate request with function
        payload["set_voltage"] = v_val
        payload["set_current"] = i_val
        payload["set_output"] = 1 if output_checked else 0




        request = {
            "name": self.instrument_name,
            "payload": payload
        }

        self.send_request.emit(request)
        

    def send_refresh_request(self):
        """Send a refresh request to query all live values from the PSU."""
        request = {
            "name": self.instrument_name,
            "payload": {"status": True}
        }
        logger.debug(f'Sending refresh request: {request}')
        self.send_request.emit(request)

    def update_from_refresh(self, payload): #Trenger kanskje ikke denne hvis vi håndtrer det i handle_status_update
        """Update measured value labels from a refresh reply."""
        for index, row in enumerate(self.rows):
            channel = index + 1
            channel_state = payload.get(channel) or payload.get(str(channel))
            if not isinstance(channel_state, dict):
                continue

            if "get_voltage" in channel_state:
                try:
                    row["meas_voltage"].setText(f"{float(channel_state['get_voltage']):.3f} V")
                except (ValueError, TypeError):
                    row["meas_voltage"].setText(str(channel_state['get_voltage']))

            if "get_current" in channel_state:
                try:
                    row["meas_current"].setText(f"{float(channel_state['get_current']):.3f} A")
                except (ValueError, TypeError):
                    row["meas_current"].setText(str(channel_state['get_current']))

            if "get_output" in channel_state:
                try:
                    outp_on = bool(int(float(str(channel_state['get_output']))))
                except (ValueError, TypeError):
                    outp_on = False
                row["meas_output"].setText("ON" if outp_on else "OFF")
                row["meas_output"].setStyleSheet(
                    f"color: {'#4CAF50' if outp_on else '#F44336'}; font-weight: bold;"
                )
