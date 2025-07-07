#!/usr/bin/env python3

import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import qrcode
from PIL import ImageTk, Image
import tkinter as tk
import threading
import time

# Load YOLO model
model = YOLO("last.pt")

# RealSense setup
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = pipeline.start(config)

depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
align = rs.align(rs.stream.color)

# Filters
spatial = rs.spatial_filter()
temporal = rs.temporal_filter()
#hole_filling = rs.hole_filling_filter()

TARGET_DISTANCE = 5.85  # meters

class RealSenseStreamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.serve_stream()
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_error(404)

    def serve_stream(self):
        try:
            while True:
                frames = pipeline.wait_for_frames()
                aligned_frames = align.process(frames)

                depth_frame = aligned_frames.get_depth_frame()
                color_frame = aligned_frames.get_color_frame()
                if not depth_frame or not color_frame:
                    continue

                depth_frame = spatial.process(depth_frame)
                depth_frame = temporal.process(depth_frame)
                #depth_frame = hole_filling.process(depth_frame)

                depth_image = np.asanyarray(depth_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())

                color_image = cv2.convertScaleAbs(color_image, alpha=1.5, beta=30)

                height, width = color_image.shape[:2]
                distance_to_display = None

                # Red vertical lines at 10% and 90%
                center_x = width // 2
                offset = int(0.05 * width)  # 10% of width
                left_line_x = center_x - offset
                right_line_x = center_x + offset

                cv2.line(color_image, (left_line_x, 0), (left_line_x, height), (0, 0, 255), 2)
                cv2.line(color_image, (right_line_x, 0), (right_line_x, height), (0, 0, 255), 2)


                results = model.predict(source=color_image, verbose=False)[0]

                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = f"{model.names[cls]} {conf:.2f}"

                    cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(color_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                    # Top-center point
                    top_centre_x = int((x1 + x2) / 2)
                    top_centre_y = int(y1)

                    if 0 <= top_centre_y < depth_image.shape[0] and 0 <= top_centre_x < depth_image.shape[1]:
                        depth_val = depth_image[top_centre_y, top_centre_x]
                        if depth_val == 0:
                            for dy in [-1, 1, -2, 2]:
                                ny = top_centre_y + dy
                                if 0 <= ny < depth_image.shape[0]:
                                    depth_val = depth_image[ny, top_centre_x]
                                    if depth_val != 0:
                                        break

                        if depth_val != 0:
                            depth_m = depth_val * depth_scale
                            distance_to_display = depth_m
                            cv2.putText(color_image, f"{depth_m:.2f} m", (x1, y2 + 20),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            cv2.circle(color_image, (top_centre_x, top_centre_y), 4, (255, 0, 255), -1)

                # Overlay depth + target text on top-left
                overlay_text = f"Target: {TARGET_DISTANCE:.2f} m"
                if distance_to_display is not None:
                    overlay_text = f"Distance: {distance_to_display:.2f} m | " + overlay_text

                cv2.putText(color_image, overlay_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

                # Encode frame for browser
                ret, jpeg = cv2.imencode('.jpg', color_image, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if not ret:
                    continue

                self.wfile.write(b'--frame\r\n')
                self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                self.wfile.write(jpeg.tobytes())
                self.wfile.write(b'\r\n')

                time.sleep(0.03)

        except Exception as e:
            print(f"Stream error: {e}")

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>RealSense Stream</title>
  <style>
    body { margin: 0; background: #000; display: flex; align-items: center; justify-content: center; height: 100vh; }
    img { max-width: 100%; max-height: 100%; }
    #fsBtn {
      position: absolute; top: 10px; right: 10px;
      padding: 10px; background: rgba(255,255,255,0.6); border: none;
      font-size: 18px; cursor: pointer;
    }
  </style>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
  <button id="fsBtn">Enable Fullscreen</button>
  <img id="stream" src="/stream" />
  <script>
    document.getElementById('fsBtn').onclick = () => {
      const img = document.getElementById('stream');
      if (img.requestFullscreen) img.requestFullscreen();
      else if (img.webkitRequestFullscreen) img.webkitRequestFullscreen();
      else if (img.msRequestFullscreen) img.msRequestFullscreen();
    };
  </script>
</body>
</html>
"""

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
    img = ImageTk.PhotoImage(qr)
    label = tk.Label(root, image=img)
    label.pack(padx=10, pady=10)
    tk.Label(root, text=url, font=("Arial", 14)).pack(pady=(0, 10))
    root.mainloop()

def main():
    ip = get_local_ip()
    port = 8000
    url = f"http://{ip}:{port}/"

    print("🎥 RealSense + YOLOv8 Stream Server")
    print(f"🌐 Stream URL: {url}")
    threading.Thread(target=show_qr_code, args=(url,), daemon=True).start()

    server = HTTPServer(('0.0.0.0', port), RealSenseStreamHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        pipeline.stop()

if __name__ == '__main__':
    main()