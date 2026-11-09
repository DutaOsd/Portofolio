"""Physics: aim line, ghost ball, and cushion-bounce prediction."""

from __future__ import annotations

import math
from typing import Optional


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(v, s):
    return (v[0] * s, v[1] * s)


def length(v):
    return math.hypot(v[0], v[1])


def normalize(v):
    l = length(v)
    if l == 0:
        return (0.0, 0.0)
    return (v[0] / l, v[1] / l)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def reflect(velocity, normal):
    """Reflect a velocity vector off a surface with given unit normal."""
    n = normalize(normal)
    d = dot(velocity, n)
    return (velocity[0] - 2 * d * n[0], velocity[1] - 2 * d * n[1])


def aim_line(cue_ball, target_ball, length_px=250):
    """Direction from cue ball to target ball, extended forward.

    Returns (start, end) points for drawing the aim line.
    """
    direction = normalize(sub(target_ball, cue_ball))
    end = add(cue_ball, mul(direction, length_px))
    return cue_ball, end


def ghost_ball(cue_ball, target_ball, pocket, ball_radius=15):
    """Compute the ideal cue-ball position (ghost ball) to pot target into pocket.

    The ghost ball sits on the line from pocket -> target, one ball-diameter
    behind the target ball (from the pocket's perspective). The cue ball must
    travel toward the ghost ball so that contact sends the target into the pocket.
    """
    to_target = sub(pocket, target_ball)
    d = normalize(to_target)
    # Ghost ball is behind target, opposite the pocket direction
    ghost = add(target_ball, mul(d, -2 * ball_radius))
    return ghost


def line_circle_intersection(p1, p2, center, radius):
    """Check if segment p1->p2 intersects a circle. Returns t in [0,1] or None."""
    x1, y1 = p1
    x2, y2 = p2
    cx, cy = center
    dx = x2 - x1
    dy = y2 - y1
    fx = x1 - cx
    fy = y1 - cy

    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - radius * radius
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    disc = math.sqrt(disc)
    t1 = (-b - disc) / (2 * a)
    t2 = (-b + disc) / (2 * a)
    for t in (t1, t2):
        if 0 <= t <= 1:
            return t
    return None


def predict_path(start, velocity, cushions, max_bounces=3, ball_radius=15):
    """Predict ball path with cushion reflections.

    cushions: list of segments ((x1,y1),(x2,y2)) representing table rails.
    Returns list of points including bounce points.
    """
    path = [start]
    pos = start
    vel = normalize(velocity)
    step = 40  # pixels per simulation step
    max_steps = 2000

    for _ in range(max_bounces + 1):
        # Cast forward a long ray to find nearest cushion hit
        ray_end = add(pos, mul(vel, 3000))
        nearest_t = None
        nearest_cushion = None
        nearest_normal = None

        for c in cushions:
            c1, c2 = c
            # segment-segment intersection between ray and cushion
            hit = segment_intersection(pos, ray_end, c1, c2)
            if hit is not None:
                t = distance(pos, hit) / 3000.0
                if nearest_t is None or t < nearest_t:
                    nearest_t = t
                    nearest_cushion = c
                    # cushion normal (perpendicular)
                    cx, cy = sub(c2, c1)
                    cn = normalize((-cy, cx))
                    nearest_normal = cn

        if nearest_t is None or nearest_t > 1.0:
            # No more cushion; extend to end
            path.append(ray_end)
            break

        hit_point = add(pos, mul(vel, nearest_t * 3000))
        path.append(hit_point)
        pos = hit_point
        vel = reflect(vel, nearest_normal)

    return path


def segment_intersection(p1, p2, p3, p4):
    """Intersection point of two segments, or None."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-6:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def shot_feasibility(cue_ball, target_ball, pocket, ball_radius=15):
    """Evaluate if potting target into pocket is feasible.

    Returns a dict with:
      - feasible: bool
      - ghost_ball: (x, y)
      - aim_angle_deg: float
      - distance_cue_to_ghost: float
      - note: str
    """
    ghost = ghost_ball(cue_ball, target_ball, pocket, ball_radius)
    d = distance(cue_ball, ghost)
    direction = sub(ghost, cue_ball)
    angle = math.degrees(math.atan2(direction[1], direction[0]))

    # Feasible if cue ball isn't inside target ball and path not blocked trivially
    feasible = d > ball_radius

    return {
        "feasible": feasible,
        "ghost_ball": ghost,
        "aim_angle_deg": angle,
        "distance_cue_to_ghost": d,
        "note": "Berhasil dihitung" if feasible else "Cue terlalu dekat dengan target",
    }
