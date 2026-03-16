from PyQt5 import QtWidgets, QtCore
from GUI.GUI_zmq_client import ZmqClient
from GUI.control_row import ControlRow
from logger import setup_logger
logger = setup_logger("MainWindow")

class MainWindow(QtWidgets.QMainWindow):
    """Main application window for PSU control GUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PSU Control GUI")
        self.setGeometry(100, 100, 600, 400)

        self.instrument_names = ["hmp4040", "k2400", "k2450", "k6500"]
        self.connection_names = ["LV Connection", "HV Connection Setup 1", "HV Connection Setup 2", "DMM Connection"]
        self.control_rows = []

        # ZMQ Client
        self.zmq_client = ZmqClient()
        self.zmq_thread = QtCore.QThread()
        self.zmq_client.moveToThread(self.zmq_thread)
        self.zmq_thread.start()

        # Setup GUI
        self.init_ui()

        # Connect signals
        for row in self.control_rows:
            row.send_request.connect(self.zmq_client.send)
            self.zmq_client.reply_received.connect(row.handle_reply)
            self.zmq_client.status_update_received.connect(row.handle_status_update)
            self.zmq_client.error_received.connect(row.handle_error)



    def init_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        self.label = QtWidgets.QLabel("PSU Control Panel")
        layout.addWidget(self.label)

        # Refresh button
        self.refresh_button = QtWidgets.QPushButton("Refresh All")
        self.refresh_button.clicked.connect(self.refresh_all)
        layout.addWidget(self.refresh_button)

        for i, instrument_name in enumerate(self.instrument_names):
            row_name = self.connection_names[i] if i < len(self.connection_names) else None
            row = ControlRow(instrument_name=instrument_name, row_name=row_name)
            layout.addWidget(row)
            self.control_rows.append(row)

    def refresh_all(self):
        """Send a refresh request for each connected PSU to update live values."""
        for row in self.control_rows:
            logger.debug(f'Sending refresh request for {row.instrument_name}')
            row.send_refresh_request()
