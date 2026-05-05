from PyQt5 import QtWidgets, QtCore
from GUI.helper import StepperOnlyBox, si_prefix, REVERSE_SI_PREFIX, SI_PREFIX_MAPPING

from logger import setup_logger

logger = setup_logger("Control row")

INSTRUMENT_CONFIG = {
    "hmp4040": {
        "num_channels": 4,
        "include_channel_in_payload": True,
        "fields": ["voltage", "current", "output"]
    },
    "k2400": {
        "num_channels": 1,
        "include_channel_in_payload": False,
        "fields": ["voltage", "current", "output"]
    },
    "k2450": {
        "num_channels": 1,
        "include_channel_in_payload": False,
        "fields": ["voltage", "current", "output"]
    },
    "k6500": {
        "num_channels": 1,
        "include_channel_in_payload": False,
        "fields": []
    }
}


class FieldHandler:
    def __init__(self, field_name: str, suffix: str):
        self.field_name = field_name
        self.suffix = suffix
        self.display_key = f"disp_{field_name}"
        self.input_key = f"{field_name}_input"
        self.prefix_key = f"SI_prefix_{field_name}"
    
    def parse_and_update(self, row: dict, value: str | float, si_prefix_fn):
        try:
            numeric_value = float(value)
            scaled, prefix = si_prefix_fn(numeric_value)
            
            # Update display
            row[self.display_key].setText(f"{scaled:.3f} {prefix} {self.suffix}".strip())
            
            # Update prefix selector
            row[self.prefix_key].setCurrentIndex(SI_PREFIX_MAPPING.get(prefix, 0))
            
            # Update input spinbox
            row[self.input_key].setValue(scaled)
        except (ValueError, TypeError) as e:
            logger.error(f"Error {e} parsing {self.field_name} value: {value}")
            row[self.display_key].setText(str(value))



class ControlRow(QtWidgets.QWidget):
    """A GUI control row for a single instrument, allowing connection management and SCPI command sending."""
    send_request = QtCore.pyqtSignal(dict)

    def __init__(self, instrument_name: str, row_name: str | None, parent=None):
        super().__init__(parent)
        self.instrument_name = instrument_name
        self.config = INSTRUMENT_CONFIG[instrument_name]

        self.connected: bool = True
        self._prev_connected: bool = True

        self.row_name: str | None = row_name
        
        # Main container
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        
        # 1. Create lists to store your widgets so you can access them later
        self.rows: list = [] 

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

        self.voltage_label: QtWidgets.QLabel = QtWidgets.QLabel("Voltage")
        header_layout.addWidget(self.voltage_label)

        self.si_prefix_voltage_label: QtWidgets.QLabel = QtWidgets.QLabel("SI")
        header_layout.addWidget(self.si_prefix_voltage_label)

        self.current_label: QtWidgets.QLabel = QtWidgets.QLabel("Current")
        header_layout.addWidget(self.current_label)

        self.si_prefix_current_label: QtWidgets.QLabel = QtWidgets.QLabel("SI")
        header_layout.addWidget(self.si_prefix_current_label)

        self.output_label: QtWidgets.QLabel = QtWidgets.QLabel("Output")
        header_layout.addWidget(self.output_label)

        self.send_label: QtWidgets.QLabel = QtWidgets.QLabel("Send")
        header_layout.addWidget(self.send_label)

        self.display_voltage_label: QtWidgets.QLabel = QtWidgets.QLabel("Disp. V")
        header_layout.addWidget(self.display_voltage_label)

        self.display_current_label: QtWidgets.QLabel = QtWidgets.QLabel("Disp. A")
        header_layout.addWidget(self.display_current_label)

        self.meas_output_label: QtWidgets.QLabel = QtWidgets.QLabel("Output")
        header_layout.addWidget(self.meas_output_label)

        num_rows = self.config["num_channels"]
        for i in range(num_rows):
            self._create_control_row(i, num_rows)

    def _create_control_row(self, row_index: int, total_rows: int) -> None:
        """Create a single control row with voltage, current, and output widgets."""
        main_layout = self.layout()
        row_layout = QtWidgets.QHBoxLayout()
        
        # Create a dictionary to hold this row's widgets
        row_widgets: dict[str, QtWidgets.QWidget] = {}

        # Label
        label_text = f"{row_index + 1}" if total_rows > 1 else self.instrument_name
        row_widgets['label'] = QtWidgets.QLabel(label_text)
        row_layout.addWidget(row_widgets['label'])

        # Voltage Input
        row_widgets['voltage_input'] = QtWidgets.QDoubleSpinBox()
        row_widgets['voltage_input'].setSuffix(' V')
        row_widgets['voltage_input'].setRange(-100., 100.)
        row_layout.addWidget(row_widgets['voltage_input'])

        # SI prefix for voltage
        row_widgets['SI_prefix_voltage'] = StepperOnlyBox()
        row_widgets['SI_prefix_voltage'].setItems(['', 'm', 'mu', 'n'])
        row_layout.addWidget(row_widgets['SI_prefix_voltage'])

        # Current Input
        row_widgets['current_input'] = QtWidgets.QDoubleSpinBox()
        row_widgets['current_input'].setSuffix(' A')
        row_widgets['current_input'].setRange(-10., 10.)
        row_layout.addWidget(row_widgets['current_input'])

        # SI prefix for current
        row_widgets['SI_prefix_current'] = StepperOnlyBox()
        row_widgets['SI_prefix_current'].setItems(['', 'm', 'mu', 'n'])
        row_layout.addWidget(row_widgets['SI_prefix_current'])

        # Output on/off
        row_widgets['on_off_channel_toggle'] = QtWidgets.QCheckBox()
        row_layout.addWidget(row_widgets["on_off_channel_toggle"])

        # Send Button
        send_btn: QtWidgets.QPushButton = QtWidgets.QPushButton(f"Send")
        send_btn.clicked.connect(
            lambda checked, row=row_index, toggle=row_widgets["on_off_channel_toggle"]:
                self.on_row_submitted(row, toggle.isChecked())
        )
        row_layout.addWidget(send_btn)

        # Measured value labels (read-only live feedback)
        row_widgets['disp_voltage'] = QtWidgets.QLabel("—")
        row_widgets['disp_voltage'].setStyleSheet("color: #2196F3; font-weight: bold;")
        row_layout.addWidget(row_widgets['disp_voltage'])

        row_widgets['disp_current'] = QtWidgets.QLabel("—")
        row_widgets['disp_current'].setStyleSheet("color: #2196F3; font-weight: bold;")
        row_layout.addWidget(row_widgets['disp_current'])

        row_widgets['meas_output'] = QtWidgets.QLabel("—")
        row_widgets['meas_output'].setStyleSheet("color: #888; font-weight: bold;")
        row_layout.addWidget(row_widgets['meas_output'])

        # Store the dictionary in our list and add layout to screen
        self.rows.append(row_widgets)
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
        
        if reply.get("payload", {}).get("disconnect") == "OK":
            # logger.info(f"Disconnect acknowledged by server for {self.instrument_name}")

            self.connected = False
            self.toggle_button.setText("Start")
            # logger.info(f"Connection stopped for {self.instrument_name}")

            return
        
        if reply.get("payload", {}).get("connect") == "OK":
            # logger.info(f"Connect acknowledged by server for {self.instrument_name}")

            self.connected = True
            self.toggle_button.setText("Stop")
            # logger.info(f"Connection started for {self.instrument_name}")

            return

        if reply.get("payload", {}).get("connect_GUI") == "OK":
            # should only be received by the first row, but we check name just in case
            # logger.info(f"GUI connection acknowledged by server for {self.instrument_name}")
            return


    @QtCore.pyqtSlot(dict)
    def handle_status_update(self, msg: dict) -> None:
        """Update display and control widgets based on instrument status."""
        if msg.get("name") != self.instrument_name:
            return
        
        logger.info(f'received status update: {msg}')
        status: dict = msg.get("status")
        if not isinstance(status, dict):
            logger.error(f"Received status update with invalid format: {status}")
            return

        voltage_handler = FieldHandler("voltage", "V")
        current_handler = FieldHandler("current", "A")

        for index, row in enumerate(self.rows):
            channel = index + 1
            # Server sends channel keys as ints, but JSON may convert to strings
            channel_state = status.get(channel) or status.get(str(channel))
            
            if not isinstance(channel_state, dict):
                continue
            
            # Update voltage if present
            if "voltage" in channel_state:
                voltage_handler.parse_and_update(row, channel_state['voltage'], si_prefix)
            
            # Update current if present
            if "current" in channel_state:
                current_handler.parse_and_update(row, channel_state['current'], si_prefix)
            
            # Update output state
            if "output" in channel_state:
                outp_on = bool(channel_state["output"])
                row["meas_output"].setText("ON" if outp_on else "OFF")
                row["meas_output"].setStyleSheet(
                    f"color: {'#00FF08' if outp_on else '#FF1100'}; font-weight: bold;"
                )
                row["on_off_channel_toggle"].setChecked(outp_on)
    
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

    def on_row_submitted(self, row_index: int, output_checked: bool) -> None:
        """Send control values for a specific row to the server."""
        target_row = self.rows[row_index]
        payload: dict = {}
        # Add channel number if needed (based on instrument config)
        if self.config["include_channel_in_payload"]:
            payload['set_channel'] = row_index + 1
        
        payload.update({
            'set_voltage': f"{target_row['voltage_input'].value()}{target_row['SI_prefix_voltage'].currentText()}V",
            'set_current': f"{target_row['current_input'].value()}{target_row['SI_prefix_current'].currentText()}A",
            'set_output': 1 if output_checked else 0
        })
        
        request = {"name": self.instrument_name, "payload": payload}
        logger.info(f"Sending request: {request}")
        self.send_request.emit(request)



    def send_refresh_request(self) -> None:
        """Send a refresh request to query all live values from the PSU."""
        request: dict = {
            "name": self.instrument_name,
            "payload": {"refresh": True}
        }
        self.send_request.emit(request)




