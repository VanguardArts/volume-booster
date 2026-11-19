#!/usr/bin/env python3
"""
Generate screenshots of Volume Booster's UI for the README.

Renders the real widgets (slider window + tray menu) to PNG via Qt offscreen
rendering. Not a mock-up — these are the actual widgets, grabbed to images.

Output:
  screenshots/slider-100.png   (slider at normal level)
  screenshots/slider-160.png   (slider boosted, orange)
  screenshots/tray-menu.png    (right-click context menu)
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "2")  # 2x for crisp screenshots

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PyQt6.QtWidgets import QApplication, QMenu  # noqa: E402
from PyQt6.QtCore import QPoint  # noqa: E402

from volume_booster import SliderWindow, PRESETS, RESET_PCT  # noqa: E402

OUT = os.path.join(ROOT, "screenshots")
os.makedirs(OUT, exist_ok=True)

app = QApplication(sys.argv)
app.setStyle("Fusion")


def grab(widget, name):
    widget.show()
    app.processEvents()
    app.processEvents()
    path = os.path.join(OUT, name)
    widget.grab().save(path)
    widget.hide()
    print("wrote", path)


# --- slider window, normal level --------------------------------------------
win = SliderWindow(lambda v: None, lambda: None)
win.set_level(100, False)
grab(win, "slider-100.png")

# --- slider window, boosted (orange) ----------------------------------------
win.set_level(160, False)
grab(win, "slider-160.png")

# --- tray context menu -------------------------------------------------------
menu = QMenu()
menu.addAction("Open Booster")
menu.addSeparator()
quick = menu.addMenu("Quick Boost")
for pct in PRESETS:
    quick.addAction(f"{pct}%")
menu.addSeparator()
menu.addAction(f"Reset to {RESET_PCT}%")
menu.addSeparator()
autostart = menu.addAction("Launch at startup")
autostart.setCheckable(True)
autostart.setChecked(True)
menu.addSeparator()
menu.addAction("Quit")
grab(menu, "tray-menu.png")
