"""Screen capture module using mss.

Captures a region of the screen (default: full primary monitor) and returns
frames as numpy arrays in BGR format (OpenCV convention).
"""

from __future__ import annotations

import mss
import numpy as np


class ScreenCapture:
    """Captures screen frames continuously."""

    def __init__(self, monitor: int = 1) -> None:
        self.monitor_index = monitor
        self.sct = mss.mss()
        self.monitor = self._get_monitor(monitor)

    def _get_monitor(self, index: int) -> dict:
        """Return the monitor dict for the given 1-based index."""
        monitors = self.sct.monitors
        if index < 1 or index >= len(monitors):
            # Fall back to primary monitor
            index = 1
        return monitors[index]

    def grab(self) -> np.ndarray:
        """Capture one frame and return it as a BGR numpy array."""
        screenshot = self.sct.grab(self.monitor)
        frame = np.array(screenshot)
        # mss returns BGRA; drop alpha and convert to BGR for OpenCV
        frame = frame[:, :, :3]
        frame = frame[:, :, ::-1]  # BGRA -> BGR
        return frame

    def get_monitor_info(self) -> dict:
        return {
            "left": self.monitor["left"],
            "top": self.monitor["top"],
            "width": self.monitor["width"],
            "height": self.monitor["height"],
        }

    def close(self) -> None:
        self.sct.close()
