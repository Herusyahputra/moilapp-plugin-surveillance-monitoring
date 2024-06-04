from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer
from .constants import RECORDING_FPS
import numpy as np
import cv2

class ScreenRecorder:
    def __init__(self, frame, fps: float = RECORDING_FPS, filename: str = "output.mp4"):
        self.frame = frame
        self.fps = fps
        self.interval = int(1000 / fps)
        self.timer = QTimer()
        self.timer.timeout.connect(self.capture_frame)
        self.frames = []
        self.filename = filename
        
    def start(self):
        self.timer.start(self.interval)
    
    def stop(self):
        self.timer.stop()
    
    def capture_frame(self):
        qt_pixmap = QPixmap(self.frame.size())
        self.frame.render(qt_pixmap)
        q_img = qt_pixmap.toImage()
        temp_shape = (q_img.height(), q_img.bytesPerLine() * 8 // q_img.depth())
        temp_shape += (4,)
        ptr = q_img.bits()
        ptr.setsize(q_img.bytesPerLine() * q_img.height())
        result = np.array(ptr, dtype=np.uint8).reshape(temp_shape)[..., :3]
        self.frames.append(result)
        
    def save_video(self):
        if not self.frames:
            print("No frames captured.")
            return
        height, width, layers = self.frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(self.filename, fourcc, self.fps, (width, height))
        
        for frame in self.frames:
            video.write(frame)
        
        video.release()
