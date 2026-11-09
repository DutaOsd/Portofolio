"""8 Ball Pool Aim Assistant - entry point.

Fitur utama:
  * Tangkap layar secara real-time
  * Deteksi otomatis bola pukul (putih) dan bola target (warna)
  * Deteksi lubang meja bilhar
  * Garis panduan aim + bola hantu (ghost ball)
  * Prediksi arah pantulan bola di tali/lubang (cushion bounce)
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import cv2
import numpy as np

from core.capture import ScreenCapture
from core.detector import BallDetector
from core.physics import (
    aim_line,
    predict_path,
    shot_feasibility,
    sub,
    add,
    mul,
    normalize,
    length,
)
from core.overlay import OverlayWindow


CONFIG_PATH = "config.json"


def load_config(path: str = CONFIG_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[!] Config {path} tidak ditemukan, menggunakan default.")
        return {}


def find_best_shot(cue, object_balls, pockets, config):
    """Cari tembakan terbaik: bola target + lubang yang paling mungkin tercelok."""
    best = None
    best_score = -1.0

    ph = config.get("physics", {})
    ball_radius = 15
    max_bounces = ph.get("max_bounces", 3)

    # Build cushion rectangles from pockets? Simplify: use table edges as cushions.
    # For bounce prediction we need table boundary. Estimate from pockets extremes.
    cushions = []
    if pockets:
        xs = [p[0] for p in pockets]
        ys = [p[1] for p in pockets]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        # Four rails (approximate table border)
        cushions = [
            ((minx, miny), (maxx, miny)),  # top
            ((maxx, miny), (maxx, maxy)),  # right
            ((maxx, maxy), (minx, maxy)),  # bottom
            ((minx, maxy), (minx, miny)),  # left
        ]

    for (ox, oy, or_, color) in object_balls:
        target = (ox, oy)
        for pocket in pockets:
            feas = shot_feasibility(cue, target, pocket, ball_radius)
            if not feas["feasible"]:
                continue
            ghost = feas["ghost_ball"]

            # Score: nearer cue-to-ghost is easier; angle straightness matters
            cue_to_ghost = feas["distance_cue_to_ghost"]
            ghost_to_target = length(sub(ghost, target))
            # prefer direct line (fewer bounces)
            score = 1.0 / (cue_to_ghost + 1.0)

            # Predict path from ghost -> target -> pocket with bounces
            direction = normalize(sub(pocket, target))
            path = predict_path(target, direction, cushions, max_bounces=max_bounces)

            shot = {
                "target": target,
                "target_color": color,
                "pocket": pocket,
                "ghost_ball": ghost,
                "score": score,
                "cue_to_ghost": cue_to_ghost,
                "angle_deg": feas["aim_angle_deg"],
                "path": path,
                "feasible": True,
            }

            if score > best_score:
                best_score = score
                best = shot

    return best


def main() -> int:
    config = load_config()

    cap_cfg = config.get("capture", {})
    capture = ScreenCapture(monitor=cap_cfg.get("monitor", 1))
    mono = config.get("detection", {})
    detector = BallDetector(config)

    # Prime frame to get size
    frame = capture.grab()
    h, w = frame[:2]
    overlay = OverlayWindow(w, h, config)

    fps = cap_cfg.get("fps", 30)
    delay_ms = max(1, int(1000 / fps))

    print("[8 Ball Pool Aim Assistant] Berjalan. Tekan 'q' di jendela untuk keluar.")
    overlay.set_status("Deteksi aktif - arahkan layar ke meja bilhar")

    try:
        while overlay.tick():
            frame = capture.grab()
            detections = detector.detect(frame)

            cue = detections.get("cue_ball")
            objects = detections.get("object_balls", [])
            pockets = detections.get("pockets", [])

            prediction = None
            if cue and objects and pockets:
                prediction = find_best_shot(cue, objects, pockets, config)

            # Status text
            if cue:
                n_obj = len(objects)
                n_pock = len(pockets)
                shot_text = ""
                if prediction:
                    shot_text = f"| Target: {prediction['target_color']} -> lubang {prediction['pocket']} | sudut {prediction['angle_deg']:.1f}°"
                overlay.set_status(
                    f"Bola pukul: terdeteksi | Bola target: {n_obj} | Lubang: {n_pock} {shot_text}"
                )
            else:
                overlay.set_status("Bola pukul belum terdeteksi - pastikan bola putih terlihat")

            overlay.update(frame, detections, prediction)

    except KeyboardInterrupt:
        pass
    finally:
        overlay.stop()
        capture.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
