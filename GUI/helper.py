import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt

SI_PREFIX_MAPPING = {
    "": 0, "m": 1, "µ": 2, "mu": 2, "n": 3
}
REVERSE_SI_PREFIX = {v: k for k, v in SI_PREFIX_MAPPING.items()}



def si_prefix(value: float):
    """Return (scaled_value, prefix) for an SI-scaled representation of value."""
    prefixes = {
        -12: 'p',
        -9: 'n',
        -6: 'µ',
        -3: 'm',
        0: '',
        3: 'k',
        6: 'M',
        9: 'G',
        12: 'T'
    }
    if value == 0:
        return 0.0, ''
    exponent = int(math.floor(math.log10(abs(value)) / 3) * 3)
    exponent = max(min(exponent, 12), -12)
    scaled_value = value / (10 ** exponent)
    prefix = prefixes.get(exponent, '')
    return scaled_value, prefix


class StepperOnlyBox(QWidget):
    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self.items = items or []
        self.index = 0

        # Main horizontal layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 1. Selection display (read-only)
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setFixedWidth(30)
        
        # 2. Stepper buttons
        self.up_btn = QPushButton("▲")
        self.down_btn = QPushButton("▼")
        
        # Set small fixed width for buttons
        self.up_btn.setFixedWidth(20)
        self.down_btn.setFixedWidth(20)

        # Set fixed height for the entire widget to match typical combo box height
        self.setFixedHeight(30)

        # Stack buttons vertically
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        btn_layout.addWidget(self.up_btn)
        btn_layout.addWidget(self.down_btn)

        # Assemble layout
        layout.addWidget(self.display)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Connect signals
        self.up_btn.clicked.connect(self.step_down)
        self.down_btn.clicked.connect(self.step_up)

        self.update_display()

    def setItems(self, items):
        self.items = items
        self.index = 0
        self.update_display()

    def currentText(self):
        return self.items[self.index] if self.items else ""

    def currentIndex(self):
        return self.index

    def setCurrentIndex(self, index):
        if 0 <= index < len(self.items):
            self.index = index
            self.update_display()

    def update_display(self):
        if self.items:
            self.display.setText(self.items[self.index])
        else:
            self.display.clear()

        # hide buttons if index is at the boundaries
        self.up_btn.setEnabled(self.index > 0)
        self.down_btn.setEnabled(self.index < len(self.items) - 1)

    def step_up(self):
        if self.index < len(self.items) - 1:
            self.index += 1
            self.update_display()

    def step_down(self):
        if self.index > 0:
            self.index -= 1
            self.update_display()


