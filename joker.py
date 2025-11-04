from flask import Flask, Response, request, abort, send_from_directory
import mss
import io
from PIL import Image
import time
import threading

app = Flask(__name__)

# Basit token ile koruma (gerçek kullanımda daha sağlam auth kullan)
WEBHOOK_TOKEN = "super-secret-token"

# Ayarlar
FPS = 5  # mobil ve bant genişliği için düşük tutmak genelde iyi
WIDTH = None  # None = tam çözünürlük, istersen ölçekle

capture_running = True  # akışı hep açık tutabiliriz; webhook tek foto da alabilir

def capture_frame():
    """Tek bir JPEG frame döndürür (bytes)."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # birinci monitör (çoğu durumda tek monitör)
        img = sct.grab(monitor)
        img_pil = Image.frombytes("RGB", img.size, img.rgb)
        if WIDTH:
            # oranlı yeniden boyutlandır
            wpercent = (WIDTH / float(img_pil.size[0]))
            hsize = int((float(img_pil.size[1]) * float(wpercent)))
            img_pil = img_pil.resize((WIDTH, hsize), Image.LANCZOS)
        buf = io.BytesIO()
        img_pil.save(buf, format='JPEG', quality=70)  # kalite + bant
        return buf.getvalue()

def mjpeg_generator():
    """MJPEG multipart generator"""
    interval = 1.0 / FPS
    while True:
        frame = capture_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n\r\n' + frame + b'\r\n')
        time.sleep(interval)

@app.route('/stream')
def stream():
    return Response(mjpeg_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/screenshot')
def screenshot():
    # Tek seferlik jpeg döndür
    frame = capture_frame()
    return Response(frame, mimetype='image/jpeg')

@app.route('/webhook', methods=['POST'])
def webhook():
    # Basit doğrulama: header veya body içinde token bekliyoruz
    token = request.headers.get('X-Webhook-Token') or request.values.get('token')
    if token != WEBHOOK_TOKEN:
        abort(401)

    action = request.json.get('action') if request.is_json else request.values.get('action', 'screenshot')
    if action == 'screenshot':
        # geri jpeg döndür
        frame = capture_frame()
        return Response(frame, mimetype='image/jpeg')
    elif action == 'status':
        return {"status": "ok"}
    else:
        return {"error": "unknown action"}, 400

# Statik html dosyası sunmak istersen:
@app.route('/')
def index():
    return send_from_directory('.', 'mobile_view.html')

if __name__ == '__main__':
    # Herkes bağlanmasın diye defaultu 127.0.0.1 yap; ağ üzerinde kullanılacaksa 0.0.0.0
    app.run(host='0.0.0.0', port=5000, threaded=True)
