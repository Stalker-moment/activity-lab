"""Experimental single-subject indicators; monotonic observation time, bounded state.
No emergency, diagnostic, or calibrated probability claims.
"""

import time
from collections import OrderedDict


def area(b):
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def iou(a, b):
    overlap = area([max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])])
    return overlap / max(1e-8, area(a) + area(b) - overlap)


class SafetyMonitor:
    def __init__(self, clock=time.monotonic, max_sessions=128):
        self.clock = clock
        self.max_sessions = max_sessions
        self.states = OrderedDict()

    def state(self, kind, session, box):
        now = self.clock()
        key = (kind, session)
        # Blank session never shares temporal state with unrelated clients.
        state = self.states.get(key) if session else None
        if (
            state is None
            or now - state["time"] > 2
            or (box and state.get("box") and iou(box, state["box"]) < 0.15)
        ):
            state = {}
        state.update(time=now, box=box)
        if session:
            self.states[key] = state
            self.states.move_to_end(key)
            while len(self.states) > self.max_sessions:
                self.states.popitem(last=False)
        return state, now

    def drowsiness(self, faces, session, enabled):
        if not enabled:
            self.states.pop(("eyes", session), None)
            return None
        f = max(faces, key=lambda f: area(f["box"]), default=None)
        state, now = self.state("eyes", session, f["box"] if f else None)
        if not f:
            state.clear()
            state.update(time=now, box=None)
            return dict(
                active=True,
                alert=False,
                eye_closure=0,
                yawn_score=0,
                closed_duration=0,
                yawn_duration=0,
                status="Wajah tidak terdeteksi",
            )
        b = f.get("blendshapes", {})
        eye = (b.get("eyeBlinkLeft", 0) + b.get("eyeBlinkRight", 0)) / 2
        jaw = b.get("jawOpen", 0)
        for key, value, threshold in [("closed", eye, 0.6), ("mouth", jaw, 0.5)]:
            if value > threshold:
                state.setdefault(key, now)
            else:
                state.pop(key, None)
        closed = now - state.get("closed", now)
        mouth = now - state.get("mouth", now)
        alert = closed >= 1.4 or mouth >= 1.8
        status = (
            "Mata terpejam lama teramati"
            if closed >= 1.4
            else "Mulut terbuka lama teramati"
            if mouth >= 1.8
            else "Belum ada indikator berkepanjangan"
        )
        return dict(
            active=True,
            alert=alert,
            eye_closure=round(eye, 3),
            yawn_score=round(jaw, 3),
            closed_duration=round(closed, 2),
            yawn_duration=round(mouth, 2),
            status=status,
        )

    def fall(self, poses, session, enabled, image_aspect=1):
        if not enabled:
            self.states.pop(("fall", session), None)
            return None
        p = max(poses, key=lambda p: area(p["box"]), default=None)
        state, now = self.state("fall", session, p["box"] if p else None)
        if not p:
            state.clear()
            state.update(time=now, box=None)
            return dict(
                active=True,
                alert=False,
                aspect_ratio=0,
                downward_velocity=0,
                fallen_duration=0,
                status="Tubuh tidak terdeteksi",
            )
        box = p["box"]
        ratio = (box[2] - box[0]) * image_aspect / max(0.01, box[3] - box[1])
        pts = p.get("points", [])
        hips = [pts[i][1] for i in [11, 12] if len(pts) > i and pts[i][2] > 0.3]
        cy = sum(hips) / len(hips) if hips else (box[1] + box[3]) / 2
        dt = now - state.get("prev_time", now)
        velocity = (cy - state.get("cy", cy)) / dt if 0.05 <= dt <= 1.5 else 0
        if velocity > 0.6:
            state["descent"] = now
        horizontal = ratio > 1.22
        if horizontal:
            state.setdefault("horizontal", now)
        else:
            state.pop("horizontal", None)
        duration = now - state.get("horizontal", now)
        # Lying down without an observed descent is not called a fall.
        potential = horizontal and now - state.get("descent", -100) < 3
        alert = potential and duration >= 0.8
        status = (
            "Potensi jatuh: penurunan lalu postur horizontal"
            if alert
            else "Postur horizontal teramati; jatuh belum terkonfirmasi"
            if horizontal
            else "Belum ada pola jatuh teramati"
        )
        state.update(cy=cy, prev_time=now)
        return dict(
            active=True,
            alert=alert,
            aspect_ratio=round(ratio, 3),
            downward_velocity=round(velocity, 3),
            fallen_duration=round(duration, 2),
            status=status,
        )
