"""Tiny shared status store, written by greeter.py and agent.py, read by the
browser-based light indicator via polling."""

import json
import os
import threading

STATUS_PATH = os.path.join(os.path.dirname(__file__), "status.json")
_lock = threading.Lock()


def set_status(**kwargs):
    with _lock:
        try:
            with open(STATUS_PATH, "r") as f:
                current = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            current = {"face_detected": False, "talking": False}
        current.update(kwargs)
        with open(STATUS_PATH, "w") as f:
            json.dump(current, f)


set_status()
