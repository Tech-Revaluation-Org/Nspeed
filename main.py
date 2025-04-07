import sys
import time
import socket
import psutil
import platform
import subprocess
from ping3 import ping
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDial, QFrame
)
from PyQt6.QtCore import QTimer, Qt, QPoint
import requests

# Helper Functions (unchanged from original)
def get_dns_servers():
    """Retrieve DNS servers based on the operating system."""
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("ipconfig /all", shell=True, text=True)
            lines = output.splitlines()
            dns_servers = []
            capture = False
            for line in lines:
                if "DNS Servers" in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        dns = parts[1].strip()
                        if dns:
                            dns_servers.append(dns)
                        capture = True
                elif capture and line.startswith("   ") and dns_servers:
                    dns = line.strip()
                    dns_servers.append(dns)
                else:
                    capture = False
            return ", ".join(dns_servers) if dns_servers else "N/A"
        except Exception:
            return "N/A"
    else:
        try:
            with open("/etc/resolv.conf", "r") as f:
                dns = [line.split()[1] for line in f if line.startswith("nameserver")]
            return ", ".join(dns) if dns else "N/A"
        except Exception:
            return "N/A"

def get_gateway():
    """Retrieve the default gateway using system commands."""
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output("route print", shell=True, text=True)
            lines = output.splitlines()
            gateway = None
            for line in lines:
                if "0.0.0.0" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        gateway = parts[1]
                        break
            return gateway if gateway else "N/A"
        else:
            output = subprocess.check_output("ip route show default", shell=True, text=True)
            parts = output.split()
            if "via" in parts:
                idx = parts.index("via") + 1
                if idx < len(parts):
                    return parts[idx]
            return "N/A"
    except Exception:
        return "N/A"

def get_local_ip():
    """Determine the primary local IP address."""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip.startswith("127."):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            finally:
                s.close()
        return ip
    except Exception:
        return "N/A"

def get_public_ip():
    """Fetch the public IP using an external service."""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        return response.json().get("ip", "N/A")
    except Exception:
        return "N/A"

# Main Widget Class
class NetMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Network Monitor")
        self.setGeometry(100, 100, 500, 450)  # Initial position and size
        self.drag_position = QPoint()  # For dragging the widget

        self.init_ui()
        self.init_data()
        self.init_timers()

    def init_ui(self):
        """Initialize the user interface with a beautiful design."""
        # Make the widget frameless and always on top, with a transparent background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Main frame for semi-transparent background and rounded corners
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 100);  /* Semi-transparent black */
                border-radius: 10px;
            }
        """)
        self.main_frame_layout = QVBoxLayout()
        self.main_frame.setLayout(self.main_frame_layout)
        self.main_layout.addWidget(self.main_frame)

        # Top bar with header and close button
        top_bar = QHBoxLayout()
        header = QLabel("Live Network Monitor")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        top_bar.addWidget(header)
        top_bar.addStretch()  # Push close button to the right
        close_btn = QPushButton("X")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background-color: red; color: white; border-radius: 10px;")
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        self.main_frame_layout.addLayout(top_bar)

        # Info frame for network statistics
        self.info_frame = QFrame()
        self.info_layout = QVBoxLayout()
        self.info_frame.setLayout(self.info_layout)

        self.download_label = QLabel("Download Speed: 0.00 KB/s")
        self.upload_label = QLabel("Upload Speed: 0.00 KB/s")
        self.ping_label = QLabel("Ping: -- ms")
        self.dns_label = QLabel("DNS Servers: Loading...")
        self.gateway_label = QLabel("Default Gateway: Loading...")
        self.local_ip_label = QLabel("Local IP: Loading...")
        self.public_ip_label = QLabel("Public IP: Loading...")

        for label in [
            self.download_label, self.upload_label, self.ping_label,
            self.dns_label, self.gateway_label, self.local_ip_label, self.public_ip_label
        ]:
            label.setStyleSheet("font-size: 14px; color: white; margin: 5px;")
            self.info_layout.addWidget(label)

        self.main_frame_layout.addWidget(self.info_frame)

        # Gauge frame (hidden by default)
        self.gauge_frame = QFrame()
        self.gauge_frame.setVisible(False)
        self.gauge_layout = QHBoxLayout()
        self.gauge_frame.setLayout(self.gauge_layout)

        # Download gauge
        self.dial_download = QDial()
        self.dial_download.setNotchesVisible(True)
        self.dial_download.setEnabled(False)
        self.dial_download.setMinimum(0)
        self.dial_download.setMaximum(5000)  # Max 5000 KB/s
        self.dial_download.setStyleSheet("QDial { background-color: #e0f7fa; }")
        self.dial_download_label = QLabel("Download")
        self.dial_download_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dial_download_label.setStyleSheet("color: white;")
        dl_layout = QVBoxLayout()
        dl_layout.addWidget(self.dial_download)
        dl_layout.addWidget(self.dial_download_label)
        self.gauge_layout.addLayout(dl_layout)

        # Upload gauge
        self.dial_upload = QDial()
        self.dial_upload.setNotchesVisible(True)
        self.dial_upload.setEnabled(False)
        self.dial_upload.setMinimum(0)
        self.dial_upload.setMaximum(5000)  # Max 5000 KB/s
        self.dial_upload.setStyleSheet("QDial { background-color: #fff9c4; }")
        self.dial_upload_label = QLabel("Upload")
        self.dial_upload_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dial_upload_label.setStyleSheet("color: white;")
        ul_layout = QVBoxLayout()
        ul_layout.addWidget(self.dial_upload)
        ul_layout.addWidget(self.dial_upload_label)
        self.gauge_layout.addLayout(ul_layout)

        self.main_frame_layout.addWidget(self.gauge_frame)

        # Toggle button for gauges
        self.toggle_btn = QPushButton("Show Live Gauges")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; padding: 10px; border: 2px solid #2196F3;
                border-radius: 5px; background-color: #BBDEFB; color: black;
            }
            QPushButton:hover {
                background-color: #90CAF9;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_gauge_view)
        self.main_frame_layout.addWidget(self.toggle_btn)

    def init_data(self):
        """Initialize network data for speed calculations."""
        io_counters = psutil.net_io_counters()
        self.last_bytes_sent = io_counters.bytes_sent
        self.last_bytes_recv = io_counters.bytes_recv
        self.last_time = time.time()

    def init_timers(self):
        """Set up timers for live updates."""
        # Update speeds and ping every second
        self.timer_speed = QTimer()
        self.timer_speed.timeout.connect(self.update_stats)
        self.timer_speed.start(1000)

        # Update network info every 60 seconds
        self.timer_info = QTimer()
        self.timer_info.timeout.connect(self.update_network_info)
        self.timer_info.start(60000)

        # Initial network info update
        self.update_network_info()

    def toggle_gauge_view(self):
        """Toggle visibility of the gauge frame."""
        visible = not self.gauge_frame.isVisible()
        self.gauge_frame.setVisible(visible)
        self.toggle_btn.setText("Hide Live Gauges" if visible else "Show Live Gauges")

    def update_stats(self):
        """Update live network statistics."""
        current_time = time.time()
        io_counters = psutil.net_io_counters()
        now_sent = io_counters.bytes_sent
        now_recv = io_counters.bytes_recv

        time_diff = current_time - self.last_time
        if time_diff == 0:
            return

        download_speed = (now_recv - self.last_bytes_recv) / time_diff / 1024  # KB/s
        upload_speed = (now_sent - self.last_bytes_sent) / time_diff / 1024    # KB/s

        self.download_label.setText(f"Download Speed: {download_speed:.2f} KB/s")
        self.upload_label.setText(f"Upload Speed: {upload_speed:.2f} KB/s")

        self.last_bytes_sent = now_sent
        self.last_bytes_recv = now_recv
        self.last_time = current_time

        latency = ping("8.8.8.8", timeout=1)
        self.ping_label.setText(f"Ping: {latency * 1000:.2f} ms" if latency else "Ping: timeout")

        if self.gauge_frame.isVisible():
            self.dial_download.setValue(min(int(download_speed), self.dial_download.maximum()))
            self.dial_upload.setValue(min(int(upload_speed), self.dial_upload.maximum()))

    def update_network_info(self):
        """Update static network information."""
        self.dns_label.setText(f"DNS Servers: {get_dns_servers()}")
        self.gateway_label.setText(f"Default Gateway: {get_gateway()}")
        self.local_ip_label.setText(f"Local IP: {get_local_ip()}")
        self.public_ip_label.setText(f"Public IP: {get_public_ip()}")

    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse movement for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

# Run the Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetMonitor()
    window.show()
    sys.exit(app.exec())
