"""Watches the webcam for a face and triggers a proactive greeting."""

import asyncio
import os
import threading
import time

import cv2

from pipecat.frames.frames import LLMRunFrame

from status import set_status

CASCADE_PATH = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml")


class PersonGreeter:
    def __init__(self, task, loop, camera_index=0, absence_secs=5.0, check_interval=0.3, should_greet=None):
        self.task = task
        self.should_greet = should_greet or (lambda: True)
        self.loop = loop
        self.camera_index = camera_index
        self.absence_secs = absence_secs
        self.check_interval = check_interval
        self._stop_event = threading.Event()
        self._face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
        if self._face_cascade.empty():
            raise RuntimeError(f"Couldn't load face cascade from {CASCADE_PATH}")

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print("[greeter] Couldn't open the camera - skipping face-triggered greeting.")
            return

        face_present = False
        became_empty_at = time.monotonic() - self.absence_secs

        while not self._stop_event.is_set():
            ok, frame = cap.read()
            if not ok:
                time.sleep(self.check_interval)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(
                gray, scaleFactor=1.3, minNeighbors=5, minSize=(60, 60)
            )
            now = time.monotonic()

            if len(faces) > 0:
                if not face_present and (now - became_empty_at) >= self.absence_secs and self.should_greet():
                    print("[greeter] Face detected - triggering greeting.")
                    asyncio.run_coroutine_threadsafe(
                        self.task.queue_frame(LLMRunFrame()), self.loop
                    )
                face_present = True
            else:
                if face_present:
                    became_empty_at = now
                face_present = False

            set_status(face_detected=face_present)
            time.sleep(self.check_interval)

        cap.release()
