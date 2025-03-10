# Nspeed
NSpeed a speed testing tool for windows
Documentation: 3D Net Speed Tester (Qt6)

Overview

This Python script is a network speed testing application built using PyQt6 for the graphical user interface and speedtest for measuring internet speed. The application provides real-time results for ping, download speed, upload speed, IP address, and DNS server.

Features

GUI-based network speed test

Real-time updates of speed test results

3D visual effects for a modern look

Displays Ping, Download, Upload, IP Address, and DNS Server

Error handling for network issues

Uses threading to avoid UI freezing


Installation

Ensure you have the required dependencies installed:

pip install PyQt6 speedtest

How It Works

1. Initialization

The script starts by checking for PyQt6. If not installed, it prompts the user and exits.

try:
    import PyQt6
except ModuleNotFoundError:
    print("Error: PyQt6 is not installed. Please install it using 'pip install PyQt6'")
    sys.exit(1)

2. SpeedTestWorker (Background Thread)

A QThread subclass runs the speed test in a separate thread to prevent UI freezing.

It initializes speedtest.Speedtest()

Finds the best server

Measures ping, download speed, upload speed

Retrieves the system's IP address and DNS server

Emits the results back to the main thread


class SpeedTestWorker(QThread):
    result_signal = pyqtSignal(dict)

    def run(self):
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            ping = st.results.ping
            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000
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

3. GUI (NetSpeedTester)

The main GUI (NetSpeedTester) consists of:

A title label

Labels for ping, download, upload, IP, and DNS

A Start Speed Test button


UI Styling

The application applies a dark theme with 3D effects, including:

Drop shadows for labels

Gradient colors

Rounded corners


self.label_title.setStyleSheet("color: #00E676; padding: 10px;")
label.setStyleSheet("color: white; background: #1E1E1E; padding: 10px; border-radius: 15px;")

4. Speed Test Execution

When the Start Speed Test button is clicked:

It disables itself to prevent multiple tests running simultaneously

A SpeedTestWorker instance starts the test

Results are displayed in real-time


def start_speed_test(self):
    self.start_button.setText("Testing... 🔄")
    self.start_button.setEnabled(False)

    self.worker = SpeedTestWorker()
    self.worker.result_signal.connect(self.display_results)
    self.worker.start()

5. Displaying Results

Once the test is complete, results are displayed:

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

6. Application Execution

The main application window is initialized and launched using:

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetSpeedTester()
    window.show()
    sys.exit(app.exec())

Running the Application

Execute the script:

python main.py

