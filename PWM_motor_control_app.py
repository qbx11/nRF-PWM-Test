#!/usr/bin/env python3
"""
UART (115200 baud, ASCII, newline-terminated):
  D:<0-100>\n      — duty cycle (%)
  F:<100-20000>\n  — częstotliwość PWM (Hz)
  E:<0|1>\n        — enable / disable silnika
"""

import sys
import serial
import serial.tools.list_ports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QSpinBox, QComboBox,
    QPushButton, QGroupBox, QStatusBar,
    QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MotorController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.duty = 50
        self.freq = 5000
        self.enabled = False
        self.supply_voltage = 5.0  # Zasilanie 5V

        self.setWindowTitle("PWM tester")
        self.setMinimumWidth(550)

        self._build_ui()
        self._refresh_ports()

    # ──────────────────────────────────────────── UI build ──────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        # Port selection
        port_group = QGroupBox("")
        port_row = QHBoxLayout(port_group)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(220)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(90)
        self.refresh_btn.clicked.connect(self._refresh_ports)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFixedWidth(90)
        self.connect_btn.clicked.connect(self._toggle_connection)

        port_row.addWidget(QLabel("Port:"))
        port_row.addWidget(self.port_combo, 1)
        port_row.addWidget(self.refresh_btn)
        port_row.addWidget(self.connect_btn)
        root.addWidget(port_group)

        # On / Off toggle
        self.toggle_btn = QPushButton(" MOTOR OFF")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setMinimumHeight(54)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        self.toggle_btn.setFont(font)
        self.toggle_btn.setEnabled(False)
        self.toggle_btn.clicked.connect(self._on_toggle)
        self._apply_toggle_style(False)
        root.addWidget(self.toggle_btn)

        # Duty cycle slider & limits
        duty_group = QGroupBox("Duty Cycle")
        duty_layout = QVBoxLayout(duty_group)

        duty_top_row = QHBoxLayout()
        self.limit_checkbox = QCheckBox("Max 3V")
        self.limit_checkbox.setChecked(False)
        self.limit_checkbox.toggled.connect(self._on_limit_toggled)
        duty_top_row.addWidget(self.limit_checkbox)
        duty_top_row.addStretch()

        duty_row = QHBoxLayout()
        self.duty_slider = QSlider(Qt.Horizontal)
        self.duty_slider.setRange(0, 100)
        self.duty_slider.setValue(self.duty)
        self.duty_slider.setEnabled(False)

        self.duty_spin = QSpinBox()
        self.duty_spin.setRange(0, 100)
        self.duty_spin.setValue(self.duty)
        self.duty_spin.setSuffix(" %")
        self.duty_spin.setEnabled(False)

        self.voltage_label = QLabel()
        self._update_voltage_display()

        self.duty_slider.valueChanged.connect(self._on_duty_slider)
        self.duty_spin.valueChanged.connect(self._on_duty_spin)

        # KULOODPORNY KONTENER PRAWEJ STRONY (Szerokość na sztywno: 150px)
        duty_right_container = QWidget()
        duty_right_layout = QHBoxLayout(duty_right_container)
        duty_right_layout.setContentsMargins(0, 0, 0, 0)
        duty_right_layout.addWidget(self.duty_spin)
        duty_right_layout.addWidget(self.voltage_label)
        duty_right_container.setFixedWidth(150)

        duty_row.addWidget(self.duty_slider, 1)
        duty_row.addWidget(duty_right_container)

        duty_layout.addLayout(duty_top_row)
        duty_layout.addLayout(duty_row)
        root.addWidget(duty_group)

        # Frequency slider
        freq_group = QGroupBox("PWM frequency")
        freq_row = QHBoxLayout(freq_group)

        self.freq_slider = QSlider(Qt.Horizontal)
        self.freq_slider.setRange(0, 20000)
        self.freq_slider.setValue(self.freq)
        self.freq_slider.setEnabled(False)

        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(0, 20000)
        self.freq_spin.setValue(self.freq)
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.setSingleStep(5)
        self.freq_spin.setEnabled(False)

        self.freq_slider.valueChanged.connect(self._on_freq_slider)
        self.freq_spin.valueChanged.connect(self._on_freq_spin)

        # KULOODPORNY KONTENER PRAWEJ STRONY (Szerokość na sztywno: 150px)
        freq_right_container = QWidget()
        freq_right_layout = QHBoxLayout(freq_right_container)
        freq_right_layout.setContentsMargins(0, 0, 0, 0)
        freq_right_layout.addWidget(self.freq_spin)
        freq_right_container.setFixedWidth(150)

        freq_row.addWidget(self.freq_slider, 1)
        freq_row.addWidget(freq_right_container)
        root.addWidget(freq_group)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.hide()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Nie połączono.")

    def _apply_toggle_style(self, on: bool):
        base = (
            "QPushButton {{ background-color: {bg}; color: white; border-radius: 6px; }}"
            "QPushButton:hover {{ background-color: {hover}; }}"
            "QPushButton:disabled {{ background-color: #999; color: #ddd; }}"
        )
        if on:
            self.toggle_btn.setText(" MOTOR ON")
            self.toggle_btn.setStyleSheet(
                base.format(bg="#27ae60", hover="#1e8449")
            )
        else:
            self.toggle_btn.setText(" MOTOR OFF")
            self.toggle_btn.setStyleSheet(
                base.format(bg="#c0392b", hover="#922b21")
            )

    # ──────────────────────────────────────────── Serial ────────

    def _refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for p in sorted(ports, key=lambda x: x.device):
            self.port_combo.addItem(
                f"{p.device}  —  {p.description}", userData=p.device
            )
        if not ports:
            self.port_combo.addItem("Brak dostępnych portów")

    def _toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_combo.currentData()
        if not port:
            self.status_bar.showMessage("Wybierz poprawny port.")
            return
        try:
            self.serial_port = serial.Serial(port, baudrate=115200, timeout=1)
            self.connect_btn.setText("Rozłącz")
            self.status_bar.showMessage(f"✓  Połączono: {port}  @  115200 baud")
            self._set_controls_enabled(True)
            self._send(f"D:{self.duty}")
            self._send(f"F:{self.freq}")
            self._send("E:0")
        except serial.SerialException as e:
            self.status_bar.showMessage(f"✗  Błąd połączenia: {e}")

    def _disconnect(self):
        if self.serial_port:
            try:
                self._send("E:0")
            except Exception:
                pass
            self.serial_port.close()
            self.serial_port = None
        self.connect_btn.setText("Połącz")
        self.status_bar.showMessage("Rozłączono.")
        self._set_controls_enabled(False)
        self.enabled = False
        self.toggle_btn.setChecked(False)
        self._apply_toggle_style(False)

    def _set_controls_enabled(self, state: bool):
        self.toggle_btn.setEnabled(state)
        self.duty_slider.setEnabled(state)
        self.duty_spin.setEnabled(state)
        self.freq_slider.setEnabled(state)
        self.freq_spin.setEnabled(state)
        # Checkbox zostawiamy zawsze aktywny, żeby można było przełączyć w dowolnej chwili

    def _send(self, cmd: str):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(f"{cmd}\n".encode("ascii"))
            except serial.SerialException as e:
                self.status_bar.showMessage(f"Błąd wysyłania: {e}")

    # ──────────────────────────────────────────── Slots ─────────

    def _on_limit_toggled(self, checked: bool):
        max_val = 60 if checked else 100

        # Zmiana maksimum automatycznie przytnie aktualną wartość w UI,
        # jeśli przekracza nowe maksimum.
        self.duty_slider.setMaximum(max_val)
        self.duty_spin.setMaximum(max_val)

    def _update_voltage_display(self):
        voltage = (self.duty / 100.0) * self.supply_voltage
        self.voltage_label.setText(f"({voltage:.2f} V)")

    def _on_toggle(self, checked: bool):
        self.enabled = checked
        self._apply_toggle_style(checked)
        self._send(f"E:{1 if checked else 0}")
        self._update_status()

    def _on_duty_slider(self, value: int):
        self.duty_spin.blockSignals(True)
        self.duty_spin.setValue(value)
        self.duty_spin.blockSignals(False)
        self.duty = value
        self._update_voltage_display()
        self._send(f"D:{value}")
        self._update_status()

    def _on_duty_spin(self, value: int):
        self.duty_slider.blockSignals(True)
        self.duty_slider.setValue(value)
        self.duty_slider.blockSignals(False)
        self.duty = value
        self._update_voltage_display()
        self._send(f"D:{value}")
        self._update_status()

    def _on_freq_slider(self, value: int):
        self.freq_spin.blockSignals(True)
        self.freq_spin.setValue(value)
        self.freq_spin.blockSignals(False)
        self.freq = value
        self._send(f"F:{value}")
        self._update_status()

    def _on_freq_spin(self, value: int):
        self.freq_slider.blockSignals(True)
        self.freq_slider.setValue(value)
        self.freq_slider.blockSignals(False)
        self.freq = value
        self._send(f"F:{value}")
        self._update_status()

    def _update_status(self):
        state = "ON ✓" if self.enabled else "OFF"
        voltage = (self.duty / 100.0) * self.supply_voltage
        self.status_bar.showMessage(
            f"Motor: {state}  |  Duty: {self.duty}% ({voltage:.2f}V)  |  Freq: {self.freq} Hz"
        )

    def closeEvent(self, event):
        self._disconnect()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorController()
    window.show()
    sys.exit(app.exec())