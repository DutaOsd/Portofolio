"""Real-time overlay window.

Coba gunakan tkinter (jendela selalu di atas). Jika tkinter tidak tersedia
(mis. environment headless tanpa X11), fallback ke mode headless yang hanya
mencetak deteksi ke console sehingga program tetap bisa dijalankan & diuji.
"""

from __future__ import annotations

import cv2
import numpy as np


class _TkOverlay:
    def __init__(self, width, height, config):
        import tkinter as tk
        from tkinter import ttk
        from PIL import Image, ImageTk

        cfg = config or {}
        ov = cfg.get("overlay", {})
        self.title = ov.get("window_title", "8 Ball Pool Aim Assistant")
        self.always_on_top = ov.get("always_on_top", True)
        self.opacity = ov.get("opacity", 0.85)
        self.line_color = tuple(ov.get("line_color", [0, 255, 0]))
        self.line_thickness = ov.get("line_thickness", 3)
        self.predicted_color = tuple(ov.get("predicted_path_color", [0, 255, 255]))
        self.pocket_color = tuple(ov.get("pocket_color", [255, 0, 0]))

        self.width = width
        self.height = height
        self._tk = tk
        self._ImageTk = ImageTk
        self._Image = Image

        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.attributes("-topmost", self.always_on_top)
        self.root.attributes("-alpha", self.opacity)
        self.root.geometry(f"{width}x{height}+0+0")
        self.root.overrideredirect(False)

        self.canvas = tk.Canvas(
            self.root, width=width, height=height,
            highlightthickness=0, bg="black"
        )
        self.canvas.pack()

        self.panel = ttk.Frame(self.root)
        self.panel.pack(side="bottom", fill="x")
        self.status_var = tk.StringVar(value="Siapkan layar game...")
        ttk.Label(self.panel, textvariable=self.status_var).pack(side="left", padx=5)

        self._photo = None
        self._running = True
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

    def set_status(self, text):
        self.status_var.set(text)

    def update(self, frame_bgr, detections, prediction=None):
        canvas = frame_bgr.copy()
        cue = detections.get("cue_ball")
        objects = detections.get("object_balls", [])
        pockets = detections.get("pockets", [])

        for (px, py) in pockets:
            cv2.circle(canvas, (px, py), 12, self.pocket_color, -1)
            cv2.putText(canvas, "LUBANG", (px - 24, py - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.pocket_color, 1)

        if cue:
            cx, cy, cr = cue
            cv2.circle(canvas, (cx, cy), cr, self.line_color, 3)
            cv2.circle(canvas, (cx, cy), 4, self.line_color, -1)
            cv2.putText(canvas, "BOLA PUKUL", (cx - 45, cy - cr - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.line_color, 2)

        if objects and cue:
            cx, cy, _ = cue
            for (ox, oy, or_, color) in objects:
                cv2.circle(canvas, (ox, oy), or_, self.predicted_color, 2)
                cv2.circle(canvas, (ox, oy), 3, self.predicted_color, -1)
                cv2.putText(canvas, color.upper(), (ox - 20, oy - or_ - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.predicted_color, 2)
                cv2.line(canvas, (cx, cy), (ox, oy), self.line_color, self.line_thickness)

                best = prediction.get("best_shot") if prediction else None
                if best and best.get("target") == (ox, oy):
                    pocket = best.get("pocket")
                    ghost = best.get("ghost_ball")
                    if ghost:
                        gx, gy = int(ghost[0]), int(ghost[1])
                        cv2.circle(canvas, (gx, gy), or_, (255, 255, 0), 2)
                        cv2.line(canvas, (cx, cy), (gx, gy), (255, 255, 0), 2)
                    if pocket:
                        px, py = int(pocket[0]), int(pocket[1])
                        cv2.line(canvas, (ox, oy), (px, py), self.predicted_color, 2)
                        path = best.get("path")
                        if path and len(path) > 2:
                            pts = [(int(p[0]), int(p[1])) for p in path]
                            for i in range(len(pts) - 1):
                                cv2.line(canvas, pts[i], pts[i + 1], self.predicted_color, 2)
                        cv2.putText(canvas, "TARGET KEDORONG", (ox, oy - or_ - 28),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.predicted_color, 2)

        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        img = self._Image.fromarray(rgb)
        self._photo = self._ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor="nw", image=self._photo)

    def tick(self):
        if not self._running:
            return False
        try:
            self.root.update()
            return True
        except self._tk.TclError:
            self._running = False
            return False

    def stop(self):
        self._running = False
        try:
            self.root.destroy()
        except self._tk.TclError:
            pass


class _HeadlessOverlay:
    """Fallback tanpa GUI: cetak deteksi ke console."""

    def __init__(self, width, height, config):
        self.width = width
        self.height = height
        self._running = True
        print("[overlay] Mode headless aktif (tkinter tidak tersedia).")

    def set_status(self, text):
        print(f"[status] {text}")

    def update(self, frame_bgr, detections, prediction=None):
        cue = detections.get("cue_ball")
        objects = detections.get("object_balls", [])
        pockets = detections.get("pockets", [])
        line = f"deteksi: cue={cue is not None} target={len(objects)} lubang={len(pockets)}"
        if prediction:
            b = prediction["best_shot"]
            line += f" | best: {b['target_color']} -> lubang {b['pocket']} sudut {b['angle_deg']:.1f} deg"
        print("\r" + line + "   ", end="", flush=True)

    def tick(self):
        # Headless: biarkan dipanggil terus; pengatur keluar dari main.
        return self._running

    def stop(self):
        self._running = False
        print()  # newline


def OverlayWindow(width, height, config=None):
    """Factory: coba tkinter, kalau gagal pakai headless."""
    try:
        return _TkOverlay(width, height, config)
    except Exception as e:
        print(f"[overlay] tkinter tidak dapat digunakan ({e}), gunakan headless.")
        return _HeadlessOverlay(width, height, config)
