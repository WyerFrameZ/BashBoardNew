from flask import Flask, jsonify, render_template
import psutil
import time
import threading
import platform
import datetime


app = Flask(__name__)

# Statystyki sieciowe
last_bytes_sent = psutil.net_io_counters().bytes_sent
last_bytes_recv = psutil.net_io_counters().bytes_recv
last_network_time = time.time()
network_stats = {"download": 0.0, "upload": 0.0}

# Statystyki dysku
last_read = psutil.disk_io_counters().read_bytes
last_write = psutil.disk_io_counters().write_bytes
last_disk_time = time.time()
disk_stats = {"read": 0.0, "write": 0.0}

def update_disk_stats():
    global last_read, last_write, last_disk_time, disk_stats

    while True:
        time.sleep(1)
        current_time = time.time()
        disk_counters = psutil.disk_io_counters()
        
        # Oblicz prędkość odczytu i zapisu
        read_speed = (disk_counters.read_bytes - last_read) / (1024 * 1024)  # w MB/s
        write_speed = (disk_counters.write_bytes - last_write) / (1024 * 1024)  # w MB/s

        last_read = disk_counters.read_bytes
        last_write = disk_counters.write_bytes
        last_disk_time = current_time

        # Aktualizuj statystyki
        disk_stats["read"] = round(read_speed, 2)
        disk_stats["write"] = round(write_speed, 2)

def update_network_stats():
    global last_bytes_sent, last_bytes_recv, last_network_time, network_stats

    while True:
        time.sleep(1)
        current_time = time.time()
        counters = psutil.net_io_counters()
        elapsed = current_time - last_network_time

        download_speed = (counters.bytes_recv - last_bytes_recv) * 8 / 1_000_000 / elapsed
        upload_speed = (counters.bytes_sent - last_bytes_sent) * 8 / 1_000_000 / elapsed

        last_bytes_recv = counters.bytes_recv
        last_bytes_sent = counters.bytes_sent
        last_network_time = current_time

        network_stats["download"] = round(download_speed, 2)
        network_stats["upload"] = round(upload_speed, 2)

def get_system_stats():
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/').percent
    uptime = str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))

    return {
        'cpu': cpu,
        'ram': memory.percent,
        'disk': disk,
        'disk_write': disk_stats["write"],
        'disk_read': disk_stats["read"],
        'network_download': network_stats["download"],
        'network_upload': network_stats["upload"],
        'uptime': uptime,
        'platform': platform.system(),
        'platform_release': platform.release(),
        'processor': platform.processor(),
        'cpu_cores': psutil.cpu_count(logical=False),
        'cpu_threads': psutil.cpu_count(),
        'cpu_freq': round(psutil.cpu_freq().current, 2) if psutil.cpu_freq() else None,
    }


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    stats = get_system_stats()
    stats['network_download'] = network_stats["download"]
    stats['network_upload'] = network_stats["upload"]
    
    return jsonify(stats)

if __name__ == '__main__':
    # Uruchomienie wątku do aktualizacji statystyk sieciowych
    network_thread = threading.Thread(target=update_network_stats, daemon=True)
    network_thread.start()

    # Uruchomienie wątku do aktualizacji statystyk dysku
    disk_thread = threading.Thread(target=update_disk_stats, daemon=True)
    disk_thread.start()

    app.run(host='0.0.0.0', port=5000, debug=True)

