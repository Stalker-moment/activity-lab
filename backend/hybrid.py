"""Pretrained perception and geometric routing. No ANN checkpoint changes."""

import time
from safety import SafetyMonitor
from xclip_cache import CachedXClip
from collections import OrderedDict
from pathlib import Path
import numpy as np
import torch
import mediapipe as mp
from mediapipe.tasks.python import vision
from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
BODY_ACTIONS = [
    ("walking", "Berjalan", "walking"),
    ("jogging", "Jogging", "jogging slowly"),
    ("running", "Berlari", "running fast"),
    ("boxing", "Boxing", "shadow boxing and throwing punches"),
    ("clapping", "Bertepuk tangan", "clapping hands"),
    ("waving", "Melambaikan tangan", "waving a hand to greet someone"),
    ("standing", "Berdiri", "standing still"),
    ("sitting", "Duduk", "sitting on a chair"),
    ("lying", "Berbaring", "lying down"),
    ("dancing", "Menari", "dancing"),
    ("jumping", "Melompat", "jumping up and down"),
    ("jumping_jacks", "Jumping jacks", "doing jumping jacks"),
    ("squats", "Squat", "doing squats"),
    ("pushups", "Push-up", "doing push ups on the floor"),
    ("situps", "Sit-up", "doing sit ups"),
    ("lunges", "Lunges", "doing lunges"),
    ("stretching", "Peregangan", "stretching arms and legs"),
    ("yoga", "Yoga", "practicing yoga"),
    ("lifting", "Mengangkat beban", "lifting dumbbells"),
    ("cycling", "Bersepeda", "riding a bicycle"),
    ("drinking", "Minum", "drinking from a cup"),
    ("eating", "Makan", "eating food"),
    ("reading", "Membaca", "reading a book"),
    ("typing", "Mengetik", "typing on a keyboard"),
    ("phone", "Menggunakan ponsel", "using a mobile phone"),
    ("guitar", "Bermain gitar", "playing a guitar"),
    ("throwing", "Melempar", "throwing a ball"),
    ("catching", "Menangkap", "catching a ball"),
    ("kicking", "Menendang", "kicking a ball"),
    ("bending", "Membungkuk", "bending forward"),
    ("pointing", "Menunjuk", "pointing at something"),
    ("waving_both", "Mengangkat kedua tangan", "raising both arms above the head"),
]
GESTURES = {
    "Closed_Fist": "Kepalan tangan",
    "Open_Palm": "Telapak terbuka",
    "Pointing_Up": "Menunjuk ke atas",
    "Thumb_Down": "Jempol ke bawah",
    "Thumb_Up": "Jempol ke atas",
    "Victory": "Victory / peace",
    "ILoveYou": "Isyarat I love you",
    "None": "Gestur belum dikenal",
}
POSE_LINKS = [
    [0, 1],
    [0, 2],
    [1, 3],
    [2, 4],
    [5, 6],
    [5, 7],
    [7, 9],
    [6, 8],
    [8, 10],
    [5, 11],
    [6, 12],
    [11, 12],
    [11, 13],
    [13, 15],
    [12, 14],
    [14, 16],
]
HAND_LINKS = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 4],
    [0, 5],
    [5, 6],
    [6, 7],
    [7, 8],
    [5, 9],
    [9, 10],
    [10, 11],
    [11, 12],
    [9, 13],
    [13, 14],
    [14, 15],
    [15, 16],
    [13, 17],
    [0, 17],
    [17, 18],
    [18, 19],
    [19, 20],
]


def box_of(points):
    p = np.asarray(points, dtype=float)[:, :2]
    if not np.isfinite(p).all():
        raise ValueError("Landmark tidak valid")
    return np.clip(
        [p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max()], 0, 1
    ).tolist()


def area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def choose_context(poses, faces, hands):
    """Pure routing function, tested without needing a physical camera."""
    full = any(p["full_body"] for p in poses)
    face = max(faces, key=lambda x: area(x["box"]), default=None)
    hand = max(hands, key=lambda x: area(x["box"]), default=None)
    fa = area(face["box"]) if face else 0.0
    ha = area(hand["box"]) if hand else 0.0
    face_height = (face["box"][3] - face["box"][1]) if face else 0.0
    if hand and ha > 0.09 and ha > fa * 1.35:
        return "hand", "Tangan mendominasi frame", fa, ha, full
    if full:
        return "body", "Bahu, pinggul, lutut, dan kaki terlihat", fa, ha, full
    if face and (face_height > 0.18 or fa > 0.025):
        return (
            "face",
            "Wajah terlihat jelas; tubuh lengkap tidak terlihat",
            fa,
            ha,
            full,
        )
    if hand:
        return (
            "hand",
            "Landmark tangan terlihat; tubuh lengkap tidak terlihat",
            fa,
            ha,
            full,
        )
    if face:
        return "face", "Wajah terdeteksi; analisis tubuh tidak memadai", fa, ha, full
    if poses:
        return (
            "body",
            "Pose parsial; aksi kaki mungkin tidak dapat dinilai",
            fa,
            ha,
            full,
        )
    return (
        "objects",
        "Tidak ada tubuh, wajah, atau tangan yang cukup jelas",
        fa,
        ha,
        full,
    )


class HybridAnalyzer:
    def __init__(self, xclip, device=None, model_root=None):
        root = (Path(model_root) if model_root else HERE / "models") / "hybrid"
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.yolo_dev = 0 if (self.device == "cuda" or self.device == 0) else "cpu"
        self.detector = YOLO(str(root / "yolo11n.pt"))
        self.pose = YOLO(str(root / "yolo11n-pose.pt"))
        self.face = vision.FaceLandmarker.create_from_options(
            vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(
                    model_asset_path=str(root / "face_landmarker.task")
                ),
                running_mode=vision.RunningMode.IMAGE,
                num_faces=2,
                output_face_blendshapes=True,
            )
        )
        self.gesture = vision.GestureRecognizer.create_from_options(
            vision.GestureRecognizerOptions(
                base_options=mp.tasks.BaseOptions(
                    model_asset_path=str(root / "gesture_recognizer.task")
                ),
                running_mode=vision.RunningMode.IMAGE,
                num_hands=4,
            )
        )
        self.xclip = xclip
        self.sessions = OrderedDict()
        self.drowsiness_sessions = OrderedDict()
        self.fall_sessions = OrderedDict()
        self.age_sessions = OrderedDict()
        self.cached_prompts = None
        self.cached_text_embeds = None
        self.action_scorer = CachedXClip(xclip) if xclip else None
        self.safety = SafetyMonitor()

    def perception(self, image):
        h, w = image.shape[:2]
        bgr = np.ascontiguousarray(image[..., ::-1])
        detected = self.detector.predict(
            bgr, imgsz=640, conf=0.3, device=self.yolo_dev, verbose=False
        )[0]
        objects = []
        for row in detected.boxes.data.detach().cpu().numpy():
            x1, y1, x2, y2, score, cls = row
            objects.append(
                {
                    "label": detected.names[int(cls)],
                    "score": float(score),
                    "box": np.clip([x1 / w, y1 / h, x2 / w, y2 / h], 0, 1).tolist(),
                }
            )
        pose = self.pose.predict(
            bgr, imgsz=640, conf=0.35, device=self.yolo_dev, verbose=False
        )[0]
        poses = []
        if pose.keypoints is not None and pose.keypoints.conf is not None:
            xy = pose.keypoints.xyn.detach().cpu().numpy()
            conf = pose.keypoints.conf.detach().cpu().numpy()
            boxes = pose.boxes.xyxyn.detach().cpu().numpy()
            for points, c, box in zip(xy, conf, boxes):
                complete = bool(
                    min(c[5], c[6], c[11], c[12], c[15], c[16]) >= 0.45
                    and max(c[13], c[14]) >= 0.45
                    and max(points[15, 1], points[16, 1]) < 0.995
                )
                poses.append(
                    {
                        "points": np.c_[points, c].tolist(),
                        "box": box.tolist(),
                        "full_body": complete,
                    }
                )
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image)
        )
        face_result = self.face.detect(mp_image)
        faces = []
        for i, landmarks in enumerate(face_result.face_landmarks):
            points = [[float(p.x), float(p.y)] for p in landmarks]
            blends = {
                b.category_name: float(b.score) for b in face_result.face_blendshapes[i]
            }
            faces.append(
                {"points": points, "box": box_of(points), "blendshapes": blends}
            )
        gesture_result = self.gesture.recognize(mp_image)
        hands = []
        for i, landmarks in enumerate(gesture_result.hand_landmarks):
            points = [[float(p.x), float(p.y)] for p in landmarks]
            g = gesture_result.gestures[i][0] if gesture_result.gestures[i] else None
            handed = (
                gesture_result.handedness[i][0].category_name
                if gesture_result.handedness[i]
                else "Unknown"
            )
            hands.append(
                {
                    "points": points,
                    "box": box_of(points),
                    "gesture": g.category_name if g else "None",
                    "score": float(g.score) if g else 0.0,
                    "handedness": handed,
                }
            )
        return objects, poses, faces, hands

    def stable_route(self, session, route, manual):
        now = time.monotonic()
        if not session or manual != "auto":
            return route
        previous = self.sessions.get(session)
        if previous is None or now - previous["time"] > 10:
            state = {"route": route, "pending": route, "count": 0, "time": now}
        else:
            state = previous
            state["time"] = now
            if route == state["route"]:
                state["pending"] = route
                state["count"] = 0
            else:
                state["count"] = state["count"] + 1 if state["pending"] == route else 1
                state["pending"] = route
                if state["count"] >= 2:
                    state["route"] = route
                    state["count"] = 0
        self.sessions[session] = state
        self.sessions.move_to_end(session)
        while len(self.sessions) > 128:
            self.sessions.popitem(last=False)
        return state["route"]

    def analyze(
        self,
        images,
        timestamps,
        session="",
        manual="auto",
        custom_actions=None,
        drowsiness_enabled=False,
        fall_detection_enabled=False,
        age_detection_enabled=False,
    ):
        objects, poses, faces, hands = self.perception(images[-1])
        raw, reason, fa, ha, full = choose_context(poses, faces, hands)
        route = raw if manual == "auto" else manual
        route = self.stable_route(session, route, manual)
        if manual == "auto" and route == "face" and not faces:
            route = raw
        if manual == "auto" and route == "hand" and not hands:
            route = raw
        if manual != "auto":
            reason = f"Mode manual: {manual}"
        scores = {}
        labels = {}
        label = "not_detected"
        display = "Belum ada target"
        score = 0.0
        count = 1
        kind = "detection"
        warning = None
        if route == "body" and not poses:
            display = "Tubuh belum terdeteksi"
            warning = "Posisikan tubuh di area kamera untuk analisis aksi."
        elif route == "body" and (
            len(images) < 8 or timestamps[-1] - timestamps[0] < 1.6
        ):
            label = "collecting_action"
            display = "Tubuh terdeteksi · kumpulkan gerakan"
            warning = "Analisis aksi membutuhkan sekitar dua detik video."
        elif route == "body" and self.xclip is not None:
            actions = list(BODY_ACTIONS)
            for i, text in enumerate((custom_actions or [])[:20]):
                text = text.strip()
                if text:
                    actions.append(
                        (
                            f"custom_{i}",
                            text,
                            text
                            if text.lower().startswith(("a ", "the "))
                            else f"a person {text}",
                        )
                    )
            prompts = [
                f"A video of a person {a[2]}."
                if not a[0].startswith("custom_")
                else a[2]
                for a in actions
            ]
            count = self.xclip["model"].config.vision_config.num_frames
            indices = np.abs(
                timestamps[:, None]
                - np.linspace(timestamps[-1] - 2, timestamps[-1], count)
            ).argmin(axis=0)
            p = self.action_scorer.probabilities(prompts, [images[i] for i in indices])
            scores = {a[0]: float(v) for a, v in zip(actions, p)}
            labels = {a[0]: a[1] for a in actions}
            kind = "similarity"
            label = actions[int(p.argmax())][0]
            display = labels[label]
            score = float(p.max())
            if not full:
                warning = "Tubuh hanya terlihat sebagian; aksi di luar area kamera tidak dapat dipastikan."
        elif route == "face" and faces:
            f = max(faces, key=lambda x: area(x["box"]))
            b = f["blendshapes"]
            scores = {
                "smile": (b.get("mouthSmileLeft", 0) + b.get("mouthSmileRight", 0)) / 2,
                "jaw_open": b.get("jawOpen", 0),
                "eyes_closed": (b.get("eyeBlinkLeft", 0) + b.get("eyeBlinkRight", 0))
                / 2,
                "brow_raise": b.get("browInnerUp", 0),
                "mouth_pucker": b.get("mouthPucker", 0),
                "brow_lower": (b.get("browDownLeft", 0) + b.get("browDownRight", 0))
                / 2,
            }
            labels = {
                "smile": "Senyum",
                "jaw_open": "Mulut terbuka",
                "eyes_closed": "Mata menutup / berkedip",
                "brow_raise": "Alis terangkat",
                "mouth_pucker": "Bibir mengerucut",
                "brow_lower": "Alis menurun",
            }
            label = max(scores, key=scores.get)
            score = scores[label]
            display = labels[label]
            if score < 0.3:
                label = "neutral_face"
                display = "Wajah rileks"
                score = max(0.0, 1 - max(scores.values()))
            kind = "blendshape"
            warning = "Indikator gerakan wajah, bukan pembacaan emosi atau kondisi psikologis."
        elif route == "hand" and hands:
            hand = max(hands, key=lambda x: area(x["box"]))
            label = hand["gesture"]
            display = GESTURES.get(label, label)
            score = hand["score"]
            scores = {h["gesture"]: h["score"] for h in hands}
            labels = {key: GESTURES.get(key, key) for key in scores}
            kind = "gesture"
            if label == "None":
                warning = "Tangan terlacak, tetapi gestur tidak termasuk kategori bawaan yang dikenali."
        elif route == "objects" and objects:
            route = "objects"
            for o in objects:
                scores[o["label"]] = max(scores.get(o["label"], 0), o["score"])
            labels = {key: key.replace("_", " ") for key in scores}
            label = max(scores, key=scores.get)
            display = labels[label]
            score = scores[label]
        elif route == "body" and self.xclip is None:
            display = "Model aksi belum tersedia"
            warning = (
                "YOLO Pose tersedia; pasang checkpoint X-CLIP untuk klasifikasi aksi."
            )
        else:
            route = "none"
            reason = "Arahkan kamera ke tubuh, wajah, tangan, atau objek yang didukung."
        drowsiness = self.safety.drowsiness(faces, session, drowsiness_enabled)
        fall = self.safety.fall(
            poses,
            session,
            fall_detection_enabled,
            images[-1].shape[1] / images[-1].shape[0],
        )
        age = (
            {
                "active": False,
                "available": False,
                "detected": False,
                "estimated_age": None,
                "age_range": "—",
                "bracket": "Belum tersedia",
                "confidence": None,
                "status": "Model usia terlatih belum tersedia; tidak ada estimasi yang dibuat.",
            }
            if age_detection_enabled
            else None
        )
        res = {
            "route": route,
            "raw_route": raw,
            "label": label,
            "display_label": display,
            "score": float(score),
            "scores": scores,
            "score_labels": labels,
            "score_kind": kind,
            "frames_used": count,
            "uncertain": bool(score < (0.18 if kind == "similarity" else 0.35)),
            "objects": objects,
            "poses": poses,
            "faces": faces,
            "hands": hands,
            "routing": {
                "reason": reason,
                "full_body": full,
                "face_area": round(fa, 4),
                "hand_area": round(ha, 4),
                "stabilized": route != raw and manual == "auto",
            },
            "warning": warning,
            "capabilities": {
                "object_classes": 80,
                "body_candidates": len(BODY_ACTIONS) + len(custom_actions or []),
                "hand_gestures": 7,
                "face_blendshapes": 52,
                "drowsiness_detection": True,
                "fall_detection": True,
                "age_detection": False,
            },
            "note": "Kandidat aksi terbuka lewat deskripsi, bukan pengenalan semua aktivitas secara universal.",
        }
        if drowsiness is not None:
            res["drowsiness"] = drowsiness
        if fall is not None:
            res["fall"] = fall
        if age is not None:
            res["age"] = age
        return res
