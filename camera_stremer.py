#!/usr/bin/env python3
"""
Optimized Camera Stream Server for Low-Latency
Now with QR Code support for easy mobile access!
"""

import cv2
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import socket
import qrcode
from PIL import ImageTk, Image
import tkinter as tk
import threading

class OptimizedStreamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress server logs

    def do_GET(self):
        if self.path == '/stream':
            self.serve_mjpeg_stream()
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_error(404)

    def serve_mjpeg_stream(self):
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()

        cap = cv2.VideoCapture(2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                encode_params = [cv2.IMWRITE_JPEG_QUALITY, 75]
                ret, buffer = cv2.imencode('.jpg', frame, encode_params)

                if ret:
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(buffer.tobytes())
                    self.wfile.write(b'\r\n')

                time.sleep(0.03)
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            cap.release()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def show_qr_code(url):
    qr = qrcode.make(url)
    root = tk.Tk()
    root.title("📱 Scan to View Stream")

    qr_img = ImageTk.PhotoImage(qr)
    label = tk.Label(root, image=qr_img)
    label.pack(padx=10, pady=10)

    url_label = tk.Label(root, text=url, font=("Arial", 14))
    url_label.pack(pady=(0, 10))

    root.mainloop()

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Camera Stream</title>
  <style>
    body { margin: 0; background: #000; display: flex; align-items: center; justify-content: center; height: 100vh; }
    img { max-width: 100%; max-height: 100%; }
    #fsBtn {
      position: absolute; top: 10px; right: 10px;
      padding: 10px; background: rgba(255,255,255,0.6); border: none;
      font-size: 18px; cursor: pointer;
    }
  </style>
  <meta name="author" content="Jayinaksha Vyas">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
  <button id="fsBtn">Enable Fullscreen</button>
  <img id="stream" src="/stream" />
  <script>
    const btn = document.getElementById('fsBtn');
    btn.onclick = () => {
      const img = document.getElementById('stream');
      if (img.requestFullscreen) img.requestFullscreen();
      else if (img.webkitRequestFullscreen) img.webkitRequestFullscreen();
      else if (img.msRequestFullscreen) img.msRequestFullscreen();
    };
  </script>
</body>
</html>
"""

def main():
    local_ip = get_local_ip()
    port = 8000
    stream_url = f"http://{local_ip}:{port}/"

    print("🎥 OPTIMIZED CAMERA STREAM SERVER")
    print("=" * 40)
    print(f"🌐 Stream URL: {stream_url}")
    print("=" * 40)
    print("📱 RECOMMENDED APPS:")
    print("   1. VLC Media Player (best)")
    print("   2. MX Player")
    print("   3. Any browser")
    print("=" * 40)
    print("📷 A QR code window will appear – scan it with your phone.")
    print("🚀 Starting server...")

    threading.Thread(target=show_qr_code, args=(stream_url,), daemon=True).start()

    server = HTTPServer(('0.0.0.0', port), OptimizedStreamHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == '__main__':
    main()
