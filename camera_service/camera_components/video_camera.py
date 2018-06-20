import cv2
from .base_camera import BaseCamera


class VideoCamera(BaseCamera):
    cap = cv2.VideoCapture('video.mp4')

    @staticmethod
    def frames():
        while VideoCamera.cap.isOpened():
            ret, frame = VideoCamera.cap.read()
            yield cv2.imencode('.jpg', frame)[1].tobytes()
