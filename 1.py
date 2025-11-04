from flask import Flask, jsonify
import platform
import psutil
import os
import socket

app = Flask(__name__)

@app.route('/system_info')
def system_info():
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        "ram_total": psutil.virtual_memory().total,
        "ram_available": psutil.virtual_memory().available,
        "disk_total": psutil.disk_usage('/').total,
        "disk_used": psutil.disk_usage('/').used,
        "disk_free": psutil.disk_usage('/').free,
        "boot_time": psutil.boot_time(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "user": os.getlogin(),
        "battery": psutil.sensors_battery()._asdict() if psutil.sensors_battery() else None,
        "network_interfaces": list(psutil.net_if_addrs().keys()),
        "network_stats": {k: v._asdict() for k, v in psutil.net_io_counters(pernic=True).items()},
        "uptime_seconds": psutil.boot_time(),
        # ... 15+ başka veri ekleyebilirsin
    }
    return jsonify(info)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
