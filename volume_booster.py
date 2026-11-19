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

from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPainterPath, QPen, QPolygon, QPolygonF
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
    """Draw the app icon (orange speaker + waves + green boost badge).

    Mirrors packaging/volume-booster.svg. The glyph greys out when muted; a
    small badge shows the percentage (or MUTE) whenever the level isn't 100%.
    """
    size = 128
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)

    if muted:
        body = QColor("#9aa0a6")   # grey
        plus = QColor("#8a8f96")
    else:
        body = QColor("#F28C28")   # orange
        plus = QColor("#19B77A")   # green
    cross_color = QColor("#ffffff")

    s = size / 512.0  # geometry authored on a 512 canvas (matches the SVG)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # speaker body
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(body)
    sp = QPainterPath()
    sp.moveTo(76 * s, 202 * s)
    sp.lineTo(151 * s, 202 * s)
    sp.lineTo(247 * s, 126 * s)
    sp.cubicTo(260 * s, 116 * s, 280 * s, 125 * s, 280 * s, 143 * s)
    sp.lineTo(280 * s, 369 * s)
    sp.cubicTo(280 * s, 387 * s, 260 * s, 396 * s, 247 * s, 386 * s)
    sp.lineTo(151 * s, 310 * s)
    sp.lineTo(76 * s, 310 * s)
    sp.cubicTo(63 * s, 310 * s, 52 * s, 299 * s, 52 * s, 286 * s)
    sp.lineTo(52 * s, 226 * s)
    sp.cubicTo(52 * s, 213 * s, 63 * s, 202 * s, 76 * s, 202 * s)
    sp.closeSubpath()
    p.drawPath(sp)

    # sound waves
    wave = QPen(body, 25.0 * s)
    wave.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(wave)
    p.setBrush(Qt.BrushStyle.NoBrush)
    w1 = QPainterPath()
    w1.moveTo(322 * s, 190 * s)
    w1.cubicTo(344 * s, 208 * s, 356 * s, 231 * s, 356 * s, 256 * s)
    w1.cubicTo(356 * s, 281 * s, 344 * s, 304 * s, 322 * s, 322 * s)
    p.drawPath(w1)
    w2 = QPainterPath()
    w2.moveTo(369 * s, 137 * s)
    w2.cubicTo(405 * s, 168 * s, 426 * s, 210 * s, 426 * s, 256 * s)
    w2.cubicTo(426 * s, 302 * s, 405 * s, 344 * s, 369 * s, 375 * s)
    p.drawPath(w2)

    # boost badge (green circle + white plus)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(plus)
    p.drawEllipse(QPointF(386 * s, 116 * s), 65 * s, 65 * s)
    cross_pen = QPen(cross_color, 17.0 * s)
    cross_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(cross_pen)
    p.drawLine(QPointF(386 * s, 80 * s), QPointF(386 * s, 152 * s))
    p.drawLine(QPointF(350 * s, 116 * s), QPointF(422 * s, 116 * s))
    p.end()

    # percentage / mute badge
    if pct != RESET_PCT or muted:
        h = int(size * 0.22)
        r = int(size * 0.04)
        badge = QFont()
        badge.setPixelSize(int(size * 0.15))
        badge.setBold(True)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 200))
        p.drawRoundedRect(0, size - h, size, h, r, r)
        p.setPen(QColor("#ffffff"))
        p.setFont(badge)
        label = "MUTE" if muted else f"{pct}%"
        p.drawText(0, size - h, size, h, Qt.AlignmentFlag.AlignCenter, label)
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
