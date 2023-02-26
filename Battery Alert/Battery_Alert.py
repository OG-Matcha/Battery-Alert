import psutil
import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QGridLayout, QWidget, QLineEdit, QDialog, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize, QTimer
from plyer import notification


def resource_path(relative_path):
    # get absolute path to resources
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def send_notification(title: str, message: str, timeout: str) -> None:
    notification.notify(
        title=title,
        message=message,
        timeout=timeout,
        app_icon=resource_path("assets\\Icon.ico")
    )


class BatteryAlertSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Battery Alert Configuration")
        self.setWindowIcon(QIcon(resource_path("assets\\Icon.ico")))
        self.setFixedSize(QSize(600, 300))

        self.central_widget = QWidget(self)
        self.grid_layout = QGridLayout(self.central_widget)

        self.threshold_label = QLabel("Battery Threshold:")
        self.threshold_entry = QLineEdit(self)
        self.duration_label = QLabel("Notification Duration (seconds):")
        self.duration_entry = QLineEdit(self)

        self.grid_layout.addWidget(self.threshold_label, 0, 0, 1, 1)
        self.grid_layout.addWidget(self.threshold_entry, 0, 1, 1, 1)
        self.grid_layout.addWidget(self.duration_label, 1, 0, 1, 1)
        self.grid_layout.addWidget(self.duration_entry, 1, 1, 1, 1)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_config)
        self.grid_layout.addWidget(self.save_button, 2, 0, 1, 2)

        self.read_config()

    def read_config(self) -> None:
        try:
            with open(resource_path("data\\battery_alert_config.txt"), "r") as f:
                data = f.read().strip().split("\n")
                threshold = int(data[0])
                duration = int(data[1])
        except:
            threshold = 20
            duration = 5

        self.threshold_entry.setText(str(threshold))
        self.duration_entry.setText(str(duration))

    def save_config(self) -> None:
        threshold = int(self.threshold_entry.text())
        duration = int(self.duration_entry.text())

        with open(resource_path("data\\battery_alert_config.txt"), "w+") as f:
            f.write(f"{threshold}\n{duration}")

        self.hide()


class BatteryAlertApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Battery Alert")
        self.setWindowIcon(QIcon("assets\\Icon.ico"))
        self.setFixedSize(QSize(600, 400))

        # Create images for the buttons
        self.start_img = QIcon(resource_path("assets\\start_button.png"))
        self.stop_img = QIcon(resource_path("assets\\stop_button.png"))
        self.settings_img = QIcon(resource_path("assets\\setting_button.png"))

        # Create the start/stop button and set the image to the start image
        self.start_stop_button = QPushButton(self)
        self.start_stop_button.setIcon(self.start_img)
        self.start_stop_button.setIconSize(QSize(200, 200))
        self.start_stop_button.setGeometry(
            self.width() // 2 - 100, self.height() // 2 - 100, 200, 200)
        self.start_stop_button.clicked.connect(self.toggle_startup)

        # Create the settings button and set the image to the settings image
        self.settings_button = QPushButton(self)
        self.settings_button.setIcon(self.settings_img)
        self.settings_button.setIconSize(QSize(50, 50))
        self.settings_button.setFixedSize(QSize(50, 50))
        self.settings_button.move(10, 10)
        self.settings_button.clicked.connect(self.open_settings)

        # Create the end program button
        self.end_program_button = QPushButton(self)
        self.end_program_button.setText("End Program")
        self.end_program_button.setFont(QFont("Arial", 12))
        self.end_program_button.setFixedSize(QSize(200, 40))
        self.end_program_button.move(385, 350)
        self.end_program_button.clicked.connect(self.end_program)

        # Create the timer and connect its timeout signal to the check_battery function
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_battery)

        # Create the system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("assets\\Icon.ico")))
        self.tray_icon.activated.connect(self.handle_tray_icon)

        # Create the menu for the system tray icon
        self.tray_menu = QMenu()
        self.open_action = QAction("Open", self)
        self.open_action.triggered.connect(self.show)
        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(self.handle_quit)
        self.tray_menu.addAction(self.open_action)
        self.tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.setToolTip("Battery Alert")

        self.settings_window = None
        self.is_running = False

        # Start program while open the app
        self.toggle_startup()

    def toggle_startup(self):
        if self.is_running:
            self.stop_battery_check()
            self.start_stop_button.setIcon(self.start_img)
        else:
            self.start_battery_check()
            self.start_stop_button.setIcon(self.stop_img)

    def start_battery_check(self):
        self.is_running = True
        self.low_notification_sent = False
        self.full_notification_sent = False
        self.check_battery()

    def stop_battery_check(self):
        self.is_running = False
        self.low_notification_sent = False
        self.full_notification_sent = False

    def check_battery(self):
        # Get battery status and configuration
        try:
            battery = psutil.sensors_battery()

            # Unable to get battery status
            if battery is None:
                send_notification(
                    "Battery Alert", f"Can't get battery status.", 5)
                return

            plugged = battery.power_plugged
            percent = battery.percent
        except Exception as e:
            send_notification("Battery Alert Error", str(e), 5)
            sys.exit(1)

        try:
            with open(resource_path("data\\battery_alert_config.txt"), "r") as f:
                data = f.read().strip().split("\n")
                threshold = int(data[0])
                duration = int(data[1])
        except:
            threshold = 20
            duration = 5

        if plugged:
            self.full_notification_sent = False
        else:
            self.low_notification_sent = False

        # Send notification if battery level is low or full
        if percent <= threshold and not plugged and not self.low_notification_sent:
            send_notification(
                "Battery Alert", f"Battery is at {percent}%, plug in the charger.", duration)
            self.low_notification_sent = True
        elif percent == 100 and plugged and not self.full_notification_sent:
            send_notification(
                "Battery Alert", "Battery is fully charged, unplug the charger.", duration)
            self.full_notification_sent = True

        # Repeat the check after 60 seconds, unless battery check is stopped
        if self.is_running:
            self.timer.start(60000)

    def open_settings(self):
        # Create the settings window if it doesn't exist
        if not self.settings_window:
            self.settings_window = BatteryAlertSettings()
            self.settings_window.exec_()
        else:
            self.settings_window.show()
            self.settings_window.raise_()

    def handle_tray_icon(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show()

    def handle_quit(self):
        self.tray_icon.hide()
        self.close()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.show()

    def end_program(self):
        self.close()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication([])
    window = BatteryAlertApp()
    window.show()
    app.exec_()
