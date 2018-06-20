import time
from .base_camera import BaseCamera


class ImgCamera(BaseCamera):
    """An emulated camera implementation that streams a repeated sequence
    of files at a rate of one frame per second"""
    imgs = [open(f + '.jpg', 'rb').read() for f in ['1', '2', '3']]

    @staticmethod
    def frames():
        while True:
            time.sleep(1)
            yield ImgCamera.imgs[int(time.time()) % 3]
