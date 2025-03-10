import sys
import speedtest
import socket
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont, QPalette, QColor, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QThread, pyqtSignal

try:
    import PyQt6
except ModuleNotFoundError:
    print("Error: PyQt6 is not installed. Please install it using 'pip install PyQt6'")
    sys.exit(1)

class SpeedTestWorker(QThread):
    result_signal = pyqtSignal(dict)
    
    def run(self):
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            ping = st.results.ping
            download = st.download() / 1_000_000  # Convert to Mbps
            upload = st.upload() / 1_000_000  # Convert to Mbps
            ip_address = socket.gethostbyname(socket.gethostname())
            dns_servers = socket.getaddrinfo(socket.gethostname(), None)
            dns_server = dns_servers[0][4][0] if dns_servers else "Unknown"
            
            self.result_signal.emit({
                "ping": ping,
                "download": download,
                "upload": upload,
                "ip": ip_address,
                "dns": dns_server
            })
        except Exception as e:
            self.result_signal.emit({"error": str(e)})

class NetSpeedTester(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("3D Net Speed Tester - Qt6")
        self.setGeometry(200, 200, 450, 500)
        
        # Apply 3D gradient style
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#121212"))
        self.setPalette(palette)
        
        self.layout = QVBoxLayout()
        
        self.label_title = QLabel("🚀 Network Speed Test", self)
        self.label_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_title.setStyleSheet("color: #00E676; padding: 10px;")
        self.layout.addWidget(self.label_title)
        
        self.labels = {}
        
        for key in ["Ping", "Download", "Upload", "IP", "DNS"]:
            label = QLabel(f"{key}: --", self)
            label.setFont(QFont("Arial", 14))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: white; background: #1E1E1E; padding: 10px; border-radius: 15px;")
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(10)
            effect.setOffset(3, 3)
            label.setGraphicsEffect(effect)
            self.layout.addWidget(label)
            self.labels[key] = label
        
        self.start_button = QPushButton("Start Speed Test", self)
        self.start_button.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.start_button.setStyleSheet("background: #00A8E8; color: white; padding: 15px; border-radius: 20px;")
        self.start_button.clicked.connect(self.start_speed_test)
        
        self.layout.addWidget(self.start_button)
        self.setLayout(self.layout)
    
    def start_speed_test(self):
        self.start_button.setText("Testing... 🔄")
        self.start_button.setEnabled(False)
        
        self.worker = SpeedTestWorker()
        self.worker.result_signal.connect(self.display_results)
        self.worker.start()
    
    def display_results(self, results):
        if "error" in results:
            self.label_title.setText("❌ Error: " + results["error"])
        else:
            self.labels["Ping"].setText(f"Ping: {results['ping']:.2f} ms")
            self.labels["Download"].setText(f"Download: {results['download']:.2f} Mbps")
            self.labels["Upload"].setText(f"Upload: {results['upload']:.2f} Mbps")
            self.labels["IP"].setText(f"IP: {results['ip']}")
            self.labels["DNS"].setText(f"DNS: {results['dns']}")
            
        self.start_button.setText("Start Speed Test")
        self.start_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetSpeedTester()
    window.show()
    sys.exit(app.exec())
