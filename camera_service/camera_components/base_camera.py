import time
import threading
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from threading import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """Basically, each thread representing a client will handle one frame at a time. When there is a
    frame handling in that thread, the Thread will be set. And can only process one frame at a time"""
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # Not in mean no client
            # We need to add a new client, add it to the events
            # Each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available"""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # If the client's event is not set, then set it
                # Update the timestamp of the new event
                event[0].set()  # Set the threading.Event()
                event[1] = now
            else:
                # If the client's event is already set, it means the client did not process a previous frame.
                # If the event stays set for more than 5 seconds, then assume the client is gone and remove it.
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed"""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    thread = None  # To read frames from camera
    frame = None  # Current frame is stored here
    last_access = 0  # time of last client access to the camera
    event = CameraEvent()

    def __init__(self):
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()

            # Start background frame thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    def get_frame(self):
        """Return the current camera frame"""
        BaseCamera.last_access = time.time()

        # wait for the current camera thread
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        return BaseCamera.frame

    @staticmethod
    def frames():
        """Generator that returns frames from the camera"""
        raise NotImplementedError("Must be implemented")

    @classmethod
    def _thread(cls):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseCamera.frame = frame
            BaseCamera.event.set()  # Send signal to clients
            time.sleep(0)

            # if there hasn't been any clients asking for frames in
            # the last 10 seconds, then stop the thread
            if time.time() - BaseCamera.last_access > 10:
                frames_iterator.close()
                print('Stopping camera thread due to inactivity')
                break
        BaseCamera.thread = None

