from pathlib import Path

from PyQt5 import QtWidgets, QtCore
from GUI.GUI_zmq_client import ZmqClient
from GUI.control_row import ControlRow
from logger import setup_logger
import json

logger = setup_logger("MainWindow")

class MainWindow(QtWidgets.QMainWindow):
    """Main application window for PSU control GUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PSU Control GUI")
        self.setGeometry(100, 100, 600, 400)

        # Load config and create ZMQ Client
        config_file = {}
        root_config_path = Path(__file__).resolve().parents[1] / 'config.json'
        package_config_path = Path(__file__).resolve().parents[1] / 'server' / 'psu_config.json'

        for config_path in (root_config_path, package_config_path):
            try:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as file:
                        config_file = json.load(file)
                    break
            except Exception:
                logger.warning("Could not load config file %s, using default settings.", config_path)
                config_file = {}

        zmq_address = config_file.get('zmq', {}).get('client_address', 'tcp://10.0.0.2:5555')
        self.zmq_client: ZmqClient = ZmqClient(address=zmq_address)

        # Load instrument names and display names from config
        devices = config_file.get('devices', {})
        self.instrument_names: list[str] = list(devices.keys())
        self.connection_names: list[str] = [devices[name].get('display_name', name) for name in self.instrument_names]
        self.control_rows: list[ControlRow] = []

        self.server_connected: bool = False

        # Setup GUI
        self.init_ui()

        self.zmq_client.connect_GUI_received.connect(self.handle_connect_GUI_reply)

        self.zmq_client.send({
            "type": "system_request",
            "payload": {
                "connect_GUI": True
            }
        })


        # Connect signals
        for row in self.control_rows:
            row.send_request.connect(self.zmq_client.send)
            self.zmq_client.system_reply_received.connect(row.handle_system_reply)
            self.zmq_client.status_update_received.connect(row.handle_status_update)
            self.zmq_client.error_received.connect(row.handle_error)



    def init_ui(self) -> None:
        central: QtWidgets.QWidget = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(central)

        self.label: QtWidgets.QLabel = QtWidgets.QLabel("PSU Control Panel")
        layout.addWidget(self.label)

        # Connect to server button
        self.connect_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Connect to Server")
        self.connect_button.clicked.connect(self.connect_to_server)
        layout.addWidget(self.connect_button)

        # Refresh button
        self.refresh_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Refresh All")
        self.refresh_button.clicked.connect(self.refresh_all)
        layout.addWidget(self.refresh_button)

        # Server connection status
        self.server_connected_label: QtWidgets.QLabel = QtWidgets.QLabel("Server Disconnected")
        self.server_connected_label.setStyleSheet("color: red")
        layout.addWidget(self.server_connected_label)

        for i, instrument_name in enumerate(self.instrument_names):
            row_name: str | None = self.connection_names[i] if i < len(self.connection_names) else None
            row: ControlRow = ControlRow(instrument_name=instrument_name, row_name=row_name)
            layout.addWidget(row)
            self.control_rows.append(row)


    def refresh_all(self) -> None:
        """Send a refresh request for each connected PSU to update live values."""
        for row in self.control_rows:
            row.send_refresh_request()
    
    @QtCore.pyqtSlot(dict)
    def handle_connect_GUI_reply(self, reply: dict) -> None:
        if reply.get("payload", {}).get("connect_GUI") == "OK":
            logger.info("GUI connection acknowledged by server")
            self.server_connected: bool = True
            self.server_connected_label.setText("Server Connected")
            self.server_connected_label.setStyleSheet("color: green")
            self.refresh_all()
        else:
            logger.warning("Received unexpected system reply: {}".format(reply))
            self.server_connected_label.setText("Server Connection Failed")
            self.server_connected_label.setStyleSheet("color: red")


    def connect_to_server(self) -> None:
        """Manually trigger a connection to the server (for testing purposes)."""
        self.zmq_client.send({
            "type": "system_request",
            "payload": {
                "connect_GUI": True
            }
        })
