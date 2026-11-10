"""Optional integration smoke; input video supplied explicitly, never bundled."""

from pathlib import Path
import argparse, base64, json, hashlib, cv2, numpy as np, requests

ROOT = Path(__file__).resolve().parents[1]


def run(api, video):
    checks = []

    def call(name, images, model="hybrid", mode="auto", **extra):
        encoded = []
        for image in images:
            h, w = image.shape[:2]
            scale = min(640 / w, 640 / h)
            image = cv2.resize(image, (round(w * scale), round(h * scale)))
            encoded.append(base64.b64encode(cv2.imencode(".jpg", image)[1]).decode())
        r = requests.post(
            api + "/infer",
            json=dict(
                model=model,
                mode=mode,
                frames=encoded,
                timestamps=np.linspace(0, 2, len(images)).tolist(),
                session_id=name,
                **extra,
            ),
            timeout=90,
        )
        r.raise_for_status()
        d = r.json()
        checks.append(
            dict(
                name=name,
                status=r.status_code,
                route=d.get("route"),
                label=d["label"],
                latency_ms=d["latency_ms"],
                candidates=len(d["scores"]),
                age=d.get("age"),
                fall=d.get("fall"),
                drowsiness=d.get("drowsiness"),
            )
        )
        return d

    blank = np.zeros((480, 640, 3), np.uint8)
    d = call(
        "blank",
        [blank],
        age_detection_enabled=True,
        drowsiness_enabled=True,
        fall_detection_enabled=True,
    )
    assert d["route"] == "none" and d["age"]["estimated_age"] is None
    if video:
        cap = cv2.VideoCapture(str(video))
        images = []
        for t in np.linspace(0, 2, 32):
            cap.set(cv2.CAP_PROP_POS_MSEC, float(t * 1000))
            ok, im = cap.read()
            if ok:
                images.append(im)
        cap.release()
        assert len(images) == 32
        d = call(
            "body-buffer", images, mode="body", custom_actions=["playing badminton"]
        )
        assert len(d["scores"]) == 33
        d = call("ann-buffer", images[::2], model="ann")
        assert len(d["scores"]) == 6
    manifest = json.loads(
        (ROOT / "docs/ann-provenance.json").read_text(encoding="utf-8-sig")
    )
    assert all(
        hashlib.sha256(
            (ROOT / "backend/models/ann" / r["file"]).read_bytes()
        ).hexdigest()
        == r["sha256"]
        for r in manifest["files"]
    )
    report = {
        "checks": checks,
        "ann_hashes_unchanged": True,
        "note": "Smoke tests, not an accuracy benchmark. Server latency excludes decode/queue/network.",
    }
    (ROOT / "docs/integration-results.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--api", default="http://127.0.0.1:8765")
    p.add_argument("--video", type=Path)
    a = p.parse_args()
    run(a.api, a.video)
