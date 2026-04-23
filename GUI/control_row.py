from PyQt5 import QtWidgets, QtCore
from logger import setup_logger

logger = setup_logger("Control row")

class ControlRow(QtWidgets.QWidget):
    """A GUI control row for a single instrument, allowing connection management and SCPI command sending."""
    send_request = QtCore.pyqtSignal(dict)

    def __init__(self, instrument_name: str, row_name: str | None, parent=None):
        super().__init__(parent)
        self.instrument_name: str = instrument_name

        self.connected: bool = True
        self._prev_connected: bool = True

        self.row_name: str | None = row_name
        
        # Main container
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        
        # 1. Create lists to store your widgets so you can access them later
        self.rows: list = [] 
        
        num_rows = 4 if instrument_name == "hmp4040" else 1


        top_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()

        main_layout.addLayout(top_layout)

        self.name_label: QtWidgets.QLabel = QtWidgets.QLabel(self.row_name)
        top_layout.addWidget(self.name_label)

        # connect button
        self.toggle_button: QtWidgets.QPushButton = QtWidgets.QPushButton(self.connected and "Stop" or "Start")
        self.toggle_button.clicked.connect(self.on_toggle)
        top_layout.addWidget(self.toggle_button)

        # Error display
        self.error_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)

        # Header labels
        header_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()

        main_layout.addLayout(header_layout)

        self.channel_label: QtWidgets.QLabel = QtWidgets.QLabel("Channel")
        header_layout.addWidget(self.channel_label)

        self.voltage_label: QtWidgets.QLabel = QtWidgets.QLabel("Voltage [V]")
        header_layout.addWidget(self.voltage_label)

        self.current_label: QtWidgets.QLabel = QtWidgets.QLabel("Current [A]")
        header_layout.addWidget(self.current_label)

        self.output_label: QtWidgets.QLabel = QtWidgets.QLabel("Output")
        header_layout.addWidget(self.output_label)

        self.send_label: QtWidgets.QLabel = QtWidgets.QLabel("Send")
        header_layout.addWidget(self.send_label)

        self.meas_voltage_label: QtWidgets.QLabel = QtWidgets.QLabel("Meas. V")
        header_layout.addWidget(self.meas_voltage_label)

        self.meas_current_label: QtWidgets.QLabel = QtWidgets.QLabel("Meas. A")
        header_layout.addWidget(self.meas_current_label)

        self.meas_output_label: QtWidgets.QLabel = QtWidgets.QLabel("Status")
        header_layout.addWidget(self.meas_output_label)

        for i in range(num_rows):
            row_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
            
            # Create a dictionary to hold this row's widgets
            self.row_widgets: dict[str, QtWidgets.QWidget] = {}

            # Label
            label_text = f"{i+1}" if num_rows > 1 else instrument_name
            self.row_widgets['label'] = QtWidgets.QLabel(label_text)
            row_layout.addWidget(self.row_widgets['label'])

            # Voltage Input
            self.row_widgets['voltage_input'] = QtWidgets.QDoubleSpinBox()
            self.row_widgets['voltage_input'].setSuffix(' V')
            self.row_widgets['voltage_input'].setRange(-100., 100.)
            row_layout.addWidget(self.row_widgets['voltage_input'])

            # Current Input
            self.row_widgets['current_input'] = QtWidgets.QDoubleSpinBox()
            self.row_widgets['current_input'].setSuffix(' A')
            self.row_widgets['current_input'].setRange(-10., 10.)
            row_layout.addWidget(self.row_widgets['current_input'])

            # Output on/off
            self.row_widgets['on_off_channel_toggle'] = QtWidgets.QCheckBox()
            row_layout.addWidget(self.row_widgets["on_off_channel_toggle"])

            # Send Button
            send_btn: QtWidgets.QPushButton = QtWidgets.QPushButton(f"Send")
            
            # 2. Use lambda with a default variable 'row=i' to capture the current index
            send_btn.clicked.connect(
                lambda checked, row=i, toggle=self.row_widgets["on_off_channel_toggle"]:
                    self.on_row_submitted(row, toggle.isChecked())
            )
            row_layout.addWidget(send_btn)

            # Measured value labels (read-only live feedback)
            self.row_widgets['meas_voltage'] = QtWidgets.QLabel("—")
            self.row_widgets['meas_voltage'].setStyleSheet("color: #2196F3; font-weight: bold;")
            row_layout.addWidget(self.row_widgets['meas_voltage'])

            self.row_widgets['meas_current'] = QtWidgets.QLabel("—")
            self.row_widgets['meas_current'].setStyleSheet("color: #2196F3; font-weight: bold;")
            row_layout.addWidget(self.row_widgets['meas_current'])

            self.row_widgets['meas_output'] = QtWidgets.QLabel("—")
            self.row_widgets['meas_output'].setStyleSheet("color: #888; font-weight: bold;")
            row_layout.addWidget(self.row_widgets['meas_output'])

            # Store the dictionary in our list and add layout to screen
            self.rows.append(self.row_widgets)
            main_layout.addLayout(row_layout)


    def on_toggle(self) -> None:
        if not self.connected:
            self.start()
        else:
            self.stop()

    def start(self) -> None:
        self._prev_connected: bool = self.connected
        payload: dict = {
            'connect': True
        }
        request: dict = {
            'name': self.instrument_name,
            'payload': payload
        }
        self.error_label.hide()
        self.send_request.emit(request)
        self.toggle_button.setText("Stop")
        self.connected = True


    def stop(self) -> None:
        self._prev_connected: bool = self.connected
        payload: dict = {
            'disconnect': True
        }
        request: dict = {
            'name': self.instrument_name,
            'payload': payload
        }
        self.error_label.hide()
        self.send_request.emit(request)
        self.toggle_button.setText("Start")
        self.connected = False

    @QtCore.pyqtSlot(dict)
    def handle_system_reply(self, reply: dict) -> None:
        if reply.get("name") != self.instrument_name:
            return

        if reply.get("payload", {}).get("connect_GUI") == "OK":
            # should only be received by the first row, but we check name just in case
            logger.info(f"GUI connection acknowledged by server for {self.instrument_name}")
            return


    # TODO GUI skal bare vise display current og voltage (source)
    @QtCore.pyqtSlot(dict)
    def handle_status_update(self, msg: dict) -> None:
        if msg.get("name") != self.instrument_name:
            return
        logger.info(f'received status update: {msg}')

        status: dict = msg.get("status")

        if not isinstance(status, dict): # bare håndter dict status payloads og ignorerer alt annet
            logger.error(f"Received status update with invalid format: {status}")
            return
        for index, row in enumerate(self.rows): # gå igjennom kanaler
            channel: int = index + 1
            # Server sends channel keys as ints, but JSON may convert to strings
            channel_state: dict | None = status.get(channel)
            if channel_state is None:
                channel_state: dict | None = status.get(str(channel))
            if not isinstance(channel_state, dict): # skip om kanalen ikke har status
                continue
            if "voltage" in channel_state:
                try:
                    row["meas_voltage"].setText(f"{float(channel_state['voltage']):.3f} V")
                    self.rows[index]["voltage_input"].setValue(float(channel_state['voltage']))
                except ValueError:
                    row["meas_voltage"].setText(f"{str(channel_state['voltage']):.3f} V")
                    self.rows[index]["voltage_input"].setValue(str(channel_state['voltage']))
            if "current" in channel_state:
                try:
                    row["meas_current"].setText(f"{float(channel_state['current']):.3f} A")
                    self.rows[index]["current_input"].setValue(float(channel_state['current']))
                except ValueError:
                    row["meas_current"].setText(f"{str(channel_state['current']):.3f} V")
                    self.rows[index]["current_input"].setValue(str(channel_state['current']))
            if "output" in channel_state:
                outp_on = bool(int(float(str(channel_state["output"]))))
                row["meas_output"].setText("ON" if outp_on else "OFF")
                row["meas_output"].setStyleSheet(
                    f"color: {'#00FF08' if outp_on else '#FF1100'}; font-weight: bold;"
                )
                self.rows[index]["on_off_channel_toggle"].setChecked(outp_on)
    
    @QtCore.pyqtSlot(dict)
    def handle_error(self, message: dict) -> None:
        if message.get("name") != self.instrument_name:
            return
        logger.error(f"received error: {message}")
        payload: dict = message.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        error_msg: str = payload.get("message", "Unknown error")
        self.error_label.setText(f"Error: {error_msg}")
        self.error_label.show()
        # self.connected = self._prev_connected
        self.toggle_button.setText("Stop" if self.connected else "Start")

    # 3. The function that handles the logic
    def on_row_submitted(self, row_index: int, output_checked: bool) -> None:
        # Access the specific widgets using the row_index
        target_row = self.rows[row_index]
        v_val: float = target_row['voltage_input'].value()
        i_val: float = target_row['current_input'].value()
        channel: int = row_index + 1

        payload: dict = {
            'set_voltage': v_val,
            'set_current': i_val,
            'set_output': 1 if output_checked else 0
        }

        if self.instrument_name == "hmp4040": 
            payload: dict = {
                'set_channel': channel,
                'set_voltage': v_val,
                'set_current': i_val,
                'set_output': 1 if output_checked else 0
            }
        request: dict = {
            "name": self.instrument_name,
            "payload": payload
        }

        self.send_request.emit(request)

    def send_refresh_request(self) -> None:
        """Send a refresh request to query all live values from the PSU."""
        request: dict = {
            "name": self.instrument_name,
            "payload": {"refresh": True}
        }
        self.send_request.emit(request)
