import asyncio
import sys
import threading
from dataclasses import dataclass
from enum import Enum

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel


class Lifecycle(Enum):
    Start = ("Loading...", False)
    Running = ("Status: Running", True)
    Stopping = ("Status: Stopping", True)
    Stopped = ("Status: Stopped", False)
    Exit = ("Exit...", False)
    Exited = ("Exit Complete", False)

    def __init__(self, description, is_running):
        self.description = description
        self.is_running = is_running


class ControlPanel(QWidget):
    TAG = "ControlPanel"

    def __init__(self, lifecycle):
        super().__init__()

        self.lifecycle = lifecycle
        self.state = None

        self.setWindowTitle("Onedicle Discord Bot")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.status_label = QLabel("Status: Ready", self)
        layout.addWidget(self.status_label)

        self.start_button = QPushButton("Start", self)
        self.stop_button = QPushButton("Stop", self)
        self.exit_button = QPushButton("Exit", self)

        self.start_button.clicked.connect(self.start_action)
        self.stop_button.clicked.connect(self.stop_action)
        self.exit_button.clicked.connect(self.exit_action)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.exit_button)

        self.setLayout(layout)
        self.update_state(Lifecycle.Stopped)

    def update_state(self, state):
        if self.state == state:
            return
        self.state = state
        print(f"state = {state} | {self.state.description}")
        self.status_label.setText(self.state.description)
        if state == Lifecycle.Stopping:
            self.lifecycle.pause(lambda: self.update_state(Lifecycle.Stopped))

        elif state == Lifecycle.Start:
            self.lifecycle.start(lambda: self.update_state(Lifecycle.Running))

        elif state == Lifecycle.Exit:
            self.lifecycle.end(lambda: self.update_state(Lifecycle.Exited))

        elif state == Lifecycle.Exited:
            QApplication.instance().quit()

        self.start_button.setEnabled(self.state == Lifecycle.Stopped)
        self.stop_button.setEnabled(self.state == Lifecycle.Running)

    def start_action(self):
        print(f"[{self.TAG}] start_action")
        if self.state == Lifecycle.Stopped:
            self.update_state(Lifecycle.Start)
        else:
            print(f"[{self.TAG}] start_action (ignored): {self.state}")

    def stop_action(self):
        print(f"[{self.TAG}] stop_action")
        if self.state == Lifecycle.Running:
            self.update_state(Lifecycle.Stopping)
        else:
            print(f"[{self.TAG}] stop_action (ignored): {self.state}")

    def exit_action(self):
        print(f"[{self.TAG}] exit_action")
        if self.state.is_running:
            self.stop_action()

        self.update_state(Lifecycle.Exit)


    @dataclass
    class LifecycleListener:
        on_start: callable
        on_pause: callable
        on_end: callable

        def start(self, done):
            if self.on_start:
                self.on_start(done)
            else:
                done()

        def pause(self, done):
            if self.on_pause:
                self.on_pause(done)
            else:
                done()

        def end(self, done):
            if self.on_end:
                self.on_end(done)
            else:
                done()


def delay_func(sec, func):
    timer = threading.Timer(sec, func)
    timer.start()


async def async_main():
    import asyncio
    from qasync import QEventLoop
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = ControlPanel(lifecycle=ControlPanel.LifecycleListener(
        on_start=lambda done: delay_func(3, done),
        on_pause=lambda done: delay_func(1, done),
        on_end=None,
    ))
    window.show()

    sys.exit(app.exec_())


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
