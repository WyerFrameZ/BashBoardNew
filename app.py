from flask import Flask, jsonify, render_template
import psutil
import time
import threading

app = Flask(__name__)


last_bytes_sent = psutil.net_io_counters().bytes_sent
last_bytes_recv = psutil.net_io_counters().bytes_recv
last_time = time.time()
network_stats = {"download": 0.0, "upload": 0.0}

def update_network_stats():
    global last_bytes_sent, last_bytes_recv, last_time, network_stats

    while True:
        time.sleep(1)
        current_time = time.time()
        counters = psutil.net_io_counters()
        elapsed = current_time - last_time

        download_speed = (counters.bytes_recv - last_bytes_recv) * 8 / 1_000_000 / elapsed
        upload_speed = (counters.bytes_sent - last_bytes_sent) * 8 / 1_000_000 / elapsed

        last_bytes_recv = counters.bytes_recv
        last_bytes_sent = counters.bytes_sent
        last_time = current_time

        network_stats["download"] = round(download_speed, 2)
        network_stats["upload"] = round(upload_speed, 2)

def get_system_stats():
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/').percent
    return {
        'cpu': cpu,
        'ram': memory.percent,
        'disk': disk
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
    network_thread = threading.Thread(target=update_network_stats, daemon=True)
    network_thread.start()
    app.run(debug=True)
