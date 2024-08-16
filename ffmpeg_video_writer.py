import cv2
from PyQt6.QtCore import QProcess, QByteArray, QTimer

class VideoWriter:
    def __init__(self, ffmpeg_exe, width=640, height=480, fps=30, output_file="output.mp4"):
        self.ffmpeg_exe = ffmpeg_exe
        self.width = width
        self.height = height
        self.fps = fps
        self.output_file = output_file

        # Setup FFmpeg command
        self.ffmpeg_cmd = [
            ffmpeg_exe,
            '-y',  # Overwrite output file if it exists
            '-f', 'rawvideo',  # Input format
            '-pixel_format', 'bgr24',  # Pixel format
            '-video_size', f'{self.width}x{self.height}',  # Frame size
            '-framerate', str(self.fps),  # Frame rate
            '-i', '-',  # Input comes from a pipe
            '-c:v', 'libx264',
            '-crf', '23',
            self.output_file
        ]

        # Initialize QProcess
        self.ffmpeg_process = QProcess()
        self.ffmpeg_process.start(self.ffmpeg_cmd[0], self.ffmpeg_cmd[1:])

    def write_frame(self, frame):
        if self.ffmpeg_process.state() == QProcess.ProcessState.Running:
            # Convert the frame to bytes and write to FFmpeg process
            byte_data = QByteArray(frame.tobytes())
            self.ffmpeg_process.write(byte_data)
        else:
            print("FFmpeg process is not running")

    def close(self):
        # Close the stdin pipe and wait for FFmpeg to finish
        self.ffmpeg_process.closeWriteChannel()
        self.ffmpeg_process.waitForFinished()

# Usage example
if __name__ == "__main__":
    ffmpeg_exe = "ffmpeg"
    width = 640
    height = 480
    fps = 30
    video_writer = VideoWriter(ffmpeg_exe, width, height, fps, "output.mp4")

    # Example of capturing video frames from a webcam and writing them
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    timer = QTimer()
    timer.timeout.connect(lambda: capture_and_write_frame(cap, video_writer))
    timer.start(1000 // fps)  # Adjust the interval based on FPS

    def capture_and_write_frame(cap, video_writer):
        ret, frame = cap.read()
        if ret:
            video_writer.write_frame(frame)

    def stop_recording():
        timer.stop()
        video_writer.close()
        cap.release()

    # Example: Stop recording after 10 seconds
    QTimer.singleShot(10000, stop_recording)
