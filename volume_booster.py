#!/usr/bin/env python3
"""
Volume Booster — a system-tray app to push audio above 100%.

PipeWire/PulseAudio apply digital gain above 100% on the default sink, so a
quiet YouTube video can be made much louder even when every other volume
slider (player + desktop) is already maxed out.

Dependencies: PyQt6, pactl (part of PulseAudio/PipeWire).

Controls:
  * Left-click the tray icon -> open a small floating window with a 0–200% slider.
  * Right-click the tray icon -> quick presets (100/125/150/200%) + Reset + Quit.
  * The tray icon always shows the current level, highlighted when boosted.
"""

import re
import subprocess
import sys

from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPainterPath, QPen, QPolygon
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QLabel,
    QPushButton,
    QStyle,
)

# How far above 100% we allow. PipeWire happily goes to ~300%, but 200% is a
# safe, clean-sounding ceiling for most content. Raise it if you really need to.
MAX_PCT = 200
RESET_PCT = 100
PRESETS = [100, 125, 150, 175, 200]


# --------------------------------------------------------------------------- #
#  Audio backend (thin wrapper over pactl)
# --------------------------------------------------------------------------- #
class Audio:
    @staticmethod
    def get_volume() -> int:
        """Return the default sink volume as an integer percentage (average of L/R)."""
        try:
            out = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True, check=True, timeout=3,
            ).stdout
        except Exception:
            return RESET_PCT

        pcts = [int(m) for m in re.findall(r"(\d+)%", out)]
        if not pcts:
            return RESET_PCT
        return round(sum(pcts) / len(pcts))

    @staticmethod
    def set_volume(pct: int) -> None:
        pct = max(0, min(MAX_PCT, pct))
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"],
            capture_output=True, text=True, timeout=3,
        )

    @staticmethod
    def get_mute() -> bool:
        try:
            out = subprocess.run(
                ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                capture_output=True, text=True, check=True, timeout=3,
            ).stdout
            return "yes" in out.lower()
        except Exception:
            return False

    @staticmethod
    def set_mute(mute: bool) -> None:
        val = "1" if mute else "0"
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", val],
            capture_output=True, text=True, timeout=3,
        )


# --------------------------------------------------------------------------- #
#  Tray icon drawing
# --------------------------------------------------------------------------- #
def make_icon(pct: int, muted: bool) -> QIcon:
    size = 64
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Speaker body + cone
    body = QColor("#e6e6e6")
    if muted:
        body = QColor("#888888")
    elif pct > RESET_PCT:
        body = QColor("#ff9d3c")  # orange = boosted
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(body)

    # cone (triangle)
    cone = QPolygon([
        QPoint(16, 26), QPoint(26, 26), QPoint(26, 38), QPoint(16, 38),
    ])
    p.drawPolygon(cone)
    # body (rounded square)
    p.drawRoundedRect(26, 30, 8, 4 + 8, 2, 2)  # small tweeter-ish block

    # sound waves
    wave = QPen(body, 3)
    wave.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(wave)
    if not muted:
        p.drawArc(28, 18, 18, 28, -60 * 16, 120 * 16)
        if pct > RESET_PCT:
            p.drawArc(33, 12, 20, 40, -50 * 16, 100 * 16)
        if pct > 150:
            p.drawArc(38, 6, 20, 52, -45 * 16, 90 * 16)

    p.end()

    # Badge with the percentage
    if pct != RESET_PCT or muted:
        badge_font = QFont("Sans", 8)
        badge_font.setBold(True)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(0, 44, size, 20, 4, 4)
        p.setPen(QColor("#ffffff"))
        p.setFont(badge_font)
        label = "MUTE" if muted else f"{pct}%"
        p.drawText(0, 44, size, 20, Qt.AlignmentFlag.AlignCenter, label)
        p.end()

    return QIcon(pm)


# --------------------------------------------------------------------------- #
#  Floating slider window
# --------------------------------------------------------------------------- #
class SliderWindow(QWidget):
    def __init__(self, on_change, on_reset, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.on_change = on_change
        self.on_reset = on_reset
        self.setWindowTitle("Volume Booster")

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, MAX_PCT)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(5)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(25)
        self.slider.valueChanged.connect(self._on_slider)

        self.label = QLabel("100%")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = self.label.font()
        f.setPointSize(14)
        f.setBold(True)
        self.label.setFont(f)

        self.reset_btn = QPushButton("Reset to 100%")
        self.reset_btn.clicked.connect(self.on_reset)

        lay = QVBoxLayout(self)
        lay.addWidget(self.label)
        lay.addWidget(self.slider)

        row = QHBoxLayout()
        self.pct_minus = QPushButton("−")
        self.pct_plus = QPushButton("+")
        self.pct_minus.setFixedWidth(32)
        self.pct_plus.setFixedWidth(32)
        self.pct_minus.clicked.connect(lambda: self.slider.setValue(self.slider.value() - 1))
        self.pct_plus.clicked.connect(lambda: self.slider.setValue(self.slider.value() + 1))
        row.addWidget(self.pct_minus)
        row.addWidget(self.reset_btn)
        row.addWidget(self.pct_plus)

        lay.addLayout(row)
        self.setFixedWidth(320)

    def _on_slider(self, value: int):
        self.label.setText(f"{value}%")
        if value >= RESET_PCT:
            self.label.setStyleSheet("color: #e07b1a;")
        else:
            self.label.setStyleSheet("color: palette(window-text);")
        self.on_change(value)

    def set_level(self, pct: int, muted: bool):
        # Avoid feedback loop while user is dragging.
        if not self.slider.isSliderDown():
            self.slider.blockSignals(True)
            self.slider.setValue(pct)
            self.slider.blockSignals(False)
            self.label.setText(f"{pct}%")
            self.label.setStyleSheet(
                "color: #e07b1a;" if pct > RESET_PCT else "color: palette(window-text);"
            )

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide()
        elif e.key() in (Qt.Key.Key_Up, Qt.Key.Key_Right):
            self.slider.setValue(self.slider.value() + 1)
        elif e.key() in (Qt.Key.Key_Down, Qt.Key.Key_Left):
            self.slider.setValue(self.slider.value() - 1)
        else:
            super().keyPressEvent(e)

    def closeEvent(self, e):
        # Hide instead of closing so we can re-open instantly.
        self.hide()
        e.ignore()


# --------------------------------------------------------------------------- #
#  Main tray app
# --------------------------------------------------------------------------- #
class VolumeBooster(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        self.setApplicationName("Volume Booster")

        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("No system tray available on this desktop.", file=sys.stderr)
            sys.exit(1)

        self.audio = Audio()
        self.current_pct = self.audio.get_volume()
        self.current_mute = self.audio.get_mute()

        self.window = SliderWindow(self._apply_slider, self._reset, None)

        self.tray = QSystemTrayIcon(make_icon(self.current_pct, self.current_mute))
        self.tray.setToolTip(f"Volume Booster — {self.current_pct}%")
        self.tray.setContextMenu(self._build_menu())
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

        # Poll so external changes (media keys, other apps) stay reflected.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(500)
        self._poll()

    # ----- UI ------------------------------------------------------------- #
    def _build_menu(self) -> QMenu:
        menu = QMenu()

        open_action = menu.addAction("Open Booster")
        open_action.triggered.connect(self._toggle_window)

        menu.addSeparator()

        preset_menu = menu.addMenu("Quick Boost")
        for pct in PRESETS:
            a = preset_menu.addAction(f"{pct}%")
            a.triggered.connect(lambda _=False, p=pct: self._apply_slider(p))

        menu.addSeparator()

        reset_action = menu.addAction(f"Reset to {RESET_PCT}%")
        reset_action.triggered.connect(self._reset)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit)

        return menu

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_window()

    def _toggle_window(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.set_level(self.current_pct, self.current_mute)
            self.window.adjustSize()
            self._center_on_screen()
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

    def _center_on_screen(self):
        screen = self.tray.geometry().center()
        geo = self.window.frameGeometry()
        geo.moveCenter(screen)
        self.window.move(geo.topLeft())

    # ----- actions ---------------------------------------------------------- #
    def _apply_slider(self, pct: int):
        self.audio.set_mute(False)
        self.current_mute = False
        self.audio.set_volume(pct)
        self.current_pct = pct
        self._refresh()

    def _reset(self):
        self._apply_slider(RESET_PCT)

    # ----- sync ------------------------------------------------------------- #
    def _poll(self):
        if self.window.slider.isSliderDown():
            return  # user is dragging; don't fight them
        pct = self.audio.get_volume()
        mute = self.audio.get_mute()
        if pct != self.current_pct or mute != self.current_mute:
            self.current_pct = pct
            self.current_mute = mute
            self._refresh()

    def _refresh(self):
        self.tray.setIcon(make_icon(self.current_pct, self.current_mute))
        self.tray.setToolTip(
            f"Volume Booster — {'MUTED' if self.current_mute else f'{self.current_pct}%'}"
        )
        self.window.set_level(self.current_pct, self.current_mute)


def main():
    app = VolumeBooster(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
