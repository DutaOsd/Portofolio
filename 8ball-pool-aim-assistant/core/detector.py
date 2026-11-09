"""Automatic ball and table detection using OpenCV.

Detects:
  * cue ball (white)
  * object/target balls (colored)
  * table pockets (dark corners / edge regions)

Returns ball positions as (x, y, radius, color_name) tuples.
"""

from __future__ import annotations

import cv2
import numpy as np


class BallDetector:
    def __init__(self, config: dict | None = None) -> None:
        cfg = config or {}
        det = cfg.get("detection", {})
        self.min_radius = det.get("min_ball_radius", 8)
        self.max_radius = det.get("max_ball_radius", 40)
        self.hough_dp = det.get("hough_dp", 1.2)
        self.hough_min_dist = det.get("hough_min_dist", 30)
        self.hough_param1 = det.get("hough_param1", 100)
        self.hough_param2 = det.get("hough_param2", 30)

        # HSV ranges per color (lower, upper)
        self.color_ranges = {
            "white":   (np.array([0, 0, 200]),  np.array([180, 60, 255])),
            "red":     (np.array([0, 100, 100]),  np.array([10, 255, 255])),
            "red2":    (np.array([160, 100, 100]), np.array([180, 255, 255])),
            "blue":    (np.array([100, 100, 100]), np.array([130, 255, 255])),
            "yellow":  (np.array([20, 100, 100]),  np.array([35, 255, 255])),
            "orange":  (np.array([10, 100, 100]),  np.array([20, 255, 255])),
            "purple":  (np.array([130, 100, 100]), np.array([160, 255, 255])),
            "green":   (np.array([45, 100, 100]),  np.array([75, 255, 255])),
            "maroon":  (np.array([0, 100, 100]),   np.array([5, 150, 150])),
            "black":   (np.array([0, 0, 0]),       np.array([180, 60, 60])),
        }

    def detect(self, frame: np.ndarray) -> dict:
        """Run full detection on a frame.

        Returns:
            dict with keys:
              - cue_ball: (x, y, r) or None
              - object_balls: list of (x, y, r, color)
              - pockets: list of (x, y)
              - annotated: frame with drawings
        """
        annotated = frame.copy()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)

        # --- Cue ball (white) ---
        cue_ball = self._detect_color_ball(frame, hsv, "white")

        # If color-based failed, try HoughCircles for white-ish circles
        if cue_ball is None:
            cue_ball = self._detect_hough(gray, white_only=True, frame=frame)

        # --- Object balls (all colors except white) ---
        object_balls = []
        for color_name in ["red", "blue", "yellow", "orange", "purple", "green", "maroon", "black"]:
            balls = self._detect_color_balls(frame, hsv, color_name, multiple=True)
            for b in balls:
                object_balls.append((b[0], b[1], b[2], color_name))

        # Deduplicate overlapping detections
        object_balls = self._dedupe(object_balls)

        # --- Pockets (dark circular regions near table edges) ---
        pockets = self._detect_pockets(gray)

        # --- Draw annotations ---
        if cue_ball:
            x, y, r = cue_ball
            cv2.circle(annotated, (x, y), r, (0, 255, 0), 3)
            cv2.circle(annotated, (x, y), 3, (0, 255, 0), -1)
            cv2.putText(annotated, "CUE", (x - 20, y - r - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        for (x, y, r, color) in object_balls:
            cv2.circle(annotated, (x, y), r, (0, 255, 255), 2)
            cv2.putText(annotated, color.upper(), (x - 20, y - r - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        for (px, py) in pockets:
            cv2.circle(annotated, (px, py), 10, (255, 0, 0), -1)
            cv2.putText(annotated, "P", (px - 8, py - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        return {
            "cue_ball": cue_ball,
            "object_balls": object_balls,
            "pockets": pockets,
            "annotated": annotated,
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _detect_color_ball(self, frame: np.ndarray, hsv: np.ndarray, color: str):
        """Detect a single ball of the given color (largest match)."""
        balls = self._detect_color_balls(frame, hsv, color, multiple=True)
        if not balls:
            return None
        # Return the largest by radius
        return max(balls, key=lambda b: b[2])

    def _detect_color_balls(self, frame, hsv, color, multiple=False):
        ranges = self.color_ranges.get(color)
        if ranges is None:
            return []
        lower, upper = ranges
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        balls = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 50:
                continue
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            if self.min_radius <= radius <= self.max_radius:
                balls.append((int(x), int(y), int(radius)))
        return balls

    def _detect_hough(self, gray, white_only=False, frame=None):
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=self.hough_dp,
            minDist=self.hough_min_dist,
            param1=self.hough_param1,
            param2=self.hough_param2,
            minRadius=self.min_radius,
            maxRadius=self.max_radius,
        )
        if circles is None:
            return None
        circles = np.round(circles[0, :]).astype(int)
        # If white_only, keep only bright ones
        if white_only and frame is not None:
            bright = []
            for (x, y, r) in circles:
                roi = frame[max(0, y - r):y + r, max(0, x - r):x + r]
                if roi.size == 0:
                    continue
                mean_val = roi.mean()
                if mean_val > 170:  # bright => white cue ball
                    bright.append((x, y, r))
            if bright:
                return max(bright, key=lambda b: b[2])
            return None
        return max(circles.tolist(), key=lambda b: b[2])

    def _dedupe(self, balls):
        """Remove overlapping duplicate detections."""
        result = []
        for b in balls:
            x, y, r, color = b
            overlap = False
            for r2 in result:
                x2, y2, r2_, _ = r2
                dist = np.hypot(x - x2, y - y2)
                if dist < (r + r2_) * 0.6:
                    overlap = True
                    # Keep larger
                    if r > r2_:
                        result.remove(r2)
                        result.append(b)
                    break
            if not overlap:
                result.append(b)
        return result

    def _detect_pockets(self, gray):
        """Detect pockets as dark circular blobs near edges."""
        pockets = []
        h, w = gray.shape
        # Threshold dark areas
        _, dark = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY_INV)
        # Focus near edges (pockets sit at table corners/edges)
        edge_mask = np.zeros_like(dark)
        edge_mask[0:120, :] = 255
        edge_mask[h - 120:h, :] = 255
        edge_mask[:, 0:120] = 255
        edge_mask[:, w - 120:w] = 255
        dark = cv2.bitwise_and(dark, dark, mask=edge_mask)

        contours, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 100 < area < 3000:
                (x, y), radius = cv2.minEnclosingCircle(cnt)
                pockets.append((int(x), int(y)))
        return pockets[:6]  # max 6 pockets
