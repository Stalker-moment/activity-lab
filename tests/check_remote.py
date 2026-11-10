"""Sequential remote smoke tests using synthetic/public images only, no private video."""

from pathlib import Path
import argparse, base64, json, time, uuid
import cv2, numpy as np, requests

ASSETS = {
    "face": "https://storage.googleapis.com/mediapipe-assets/portrait.jpg",
    "hand": "https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/thumbs_up.jpg",
    "body": "https://ultralytics.com/images/bus.jpg",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api", required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    base = args.api.rstrip("/")
    results = []

    def record(name, response, elapsed):
        try:
            d = response.json()
        except ValueError:
            d = {"error": "Non-JSON response"}
        result = {
            "test": name,
            "http_status": response.status_code,
            "roundtrip_ms": round(elapsed * 1000, 1),
        }
        for key in [
            "model",
            "route",
            "raw_route",
            "label",
            "display_label",
            "score",
            "latency_ms",
            "frames_used",
            "warning",
            "drowsiness",
            "fall",
            "age",
        ]:
            if key in d:
                result[key] = d[key]
        result["counts"] = {
            key: len(d.get(key, [])) for key in ["objects", "poses", "faces", "hands"]
        }
        result["score_count"] = len(d.get("scores", {}))
        result["face_landmarks"] = [
            len(x.get("points", [])) for x in d.get("faces", [])
        ]
        result["hand_landmarks"] = [
            len(x.get("points", [])) for x in d.get("hands", [])
        ]
        if response.status_code >= 400:
            result["detail"] = d.get("detail", d)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        results.append(result)
        return d

    def infer(name, image, model="hybrid", mode="auto", frames=1, **extra):
        h, w = image.shape[:2]
        scale = min(640 / w, 640 / h)
        image = cv2.resize(image, (round(w * scale), round(h * scale)))
        encoded = base64.b64encode(
            cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 75])[1]
        ).decode()
        ts = np.linspace(0, 2, frames).tolist() if frames > 1 else [0]
        start = time.perf_counter()
        response = requests.post(
            base + "/infer",
            json=dict(
                model=model,
                mode=mode,
                frames=[encoded] * frames,
                timestamps=ts,
                request_id=int(time.time()),
                session_id=str(uuid.uuid4()),
                **extra,
            ),
            timeout=120,
        )
        return record(name, response, time.perf_counter() - start)

    blank = np.zeros((480, 640, 3), np.uint8)
    infer(
        "blank + optional indicators",
        blank,
        drowsiness_enabled=True,
        fall_detection_enabled=True,
        age_detection_enabled=True,
    )
    for name, url in ASSETS.items():
        r = requests.get(url, timeout=45)
        r.raise_for_status()
        image = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError("Sample image decode failed: " + name)
        if name == "face":
            infer("public portrait / auto face", image, drowsiness_enabled=True)
        elif name == "hand":
            infer("public thumbs-up / manual hand", image, mode="hand")
        else:
            infer("public bus / objects", image, mode="objects")
            infer(
                "public bus / body action pipeline",
                image,
                mode="body",
                frames=32,
                custom_actions=["standing near a bus"],
            )
            infer("ANN output shape on public image", image, model="ann", frames=16)
    start = time.perf_counter()
    r = requests.post(
        base + "/infer",
        json={"model": "hybrid", "frames": ["invalid"], "timestamps": [0]},
        timeout=30,
    )
    record("invalid base64 rejected", r, time.perf_counter() - start)
    cors = []
    for origin in ["http://localhost:3000", "https://untrusted.invalid"]:
        r = requests.options(
            base + "/infer",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=20,
        )
        cors.append(
            {
                "origin": origin,
                "status": r.status_code,
                "allow_origin": r.headers.get("access-control-allow-origin"),
            }
        )
    report = {
        "api": base,
        "asset_sources": ASSETS,
        "results": results,
        "cors": cors,
        "note": "Sequential functional smoke test; repeated still images are not an action/safety accuracy benchmark. No private video sent.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("CORS " + json.dumps(cors), flush=True)


if __name__ == "__main__":
    main()
