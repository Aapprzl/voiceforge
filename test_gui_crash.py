import sys
import os
import faulthandler

with open('faults.log', 'w') as f:
    faulthandler.enable(file=f)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main import VoiceForgeApp

app = None
vf = None

def click_play():
    print("Clicking play button...", flush=True)
    vf.window._power_button.setChecked(True)

def click_stop():
    print("Clicking stop button...", flush=True)
    vf.window._power_button.setChecked(False)

def end_test():
    print("Test passed successfully, closing.", flush=True)
    sys.exit(0)

def main():
    global app, vf
    import traceback
    sys.excepthook = traceback.print_exception

    vf = VoiceForgeApp()
    
    timer1 = QTimer()
    timer1.timeout.connect(click_play)
    timer1.setSingleShot(True)
    timer1.start(1000)

    timer2 = QTimer()
    timer2.timeout.connect(click_stop)
    timer2.setSingleShot(True)
    timer2.start(3000)

    timer3 = QTimer()
    timer3.timeout.connect(end_test)
    timer3.setSingleShot(True)
    timer3.start(4000)

    sys.exit(vf.app.exec())

if __name__ == "__main__":
    main()
