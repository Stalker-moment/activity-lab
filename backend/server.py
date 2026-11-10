import os

os.environ["KERAS_BACKEND"] = "torch"
if os.getenv("DEVICE") == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import asyncio, base64, io, json, threading, time, logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
import cv2, numpy as np, torch
from runtime import BodyLimitMiddleware, AdmissionGate
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
MODEL_ROOT = Path(os.getenv("MODEL_DIR", str(HERE / "models"))).resolve()
GATE = AdmissionGate(int(os.getenv("MAX_INFLIGHT", "2")))
DISABLE_MODELS = os.getenv("DISABLE_MODEL_LOADING", "0") == "1"
PROJECT = HERE.parents[1]
CLASSES = ["boxing", "handclapping", "handwaving", "jogging", "running", "walking"]
PROMPTS = [
    "A video of a person boxing and punching with their fists.",
    "A video of a person clapping their hands together.",
    "A video of a person waving their arms and hands.",
    "A video of a person jogging slowly at a relaxed pace.",
    "A video of a person running fast or sprinting.",
    "A video of a person walking at a normal pace.",
]
STATUS = {
    "ann": {"state": "loading"},
    "xclip": {"state": "loading"},
    "hybrid": {"state": "loading"},
}
MODELS = {}
GPU_LOCK = threading.Lock()
LOGGER = logging.getLogger("activity")
DEVICE = os.getenv("DEVICE", "auto")
if DEVICE == "auto":
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
if DEVICE not in ("cpu", "cuda"):
    raise RuntimeError("DEVICE must be auto, cpu or cuda")


def sync_gpu():
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def load_models():
    num_threads = os.cpu_count() or 6
    torch.set_num_threads(min(8, max(2, num_threads)))
    try:
        import keras

        with GPU_LOCK:
            ann_folder = MODEL_ROOT / "ann"
            cfg = json.loads((ann_folder / "pipeline_config.json").read_text())
            if cfg["selected_model"] != "ann":
                raise RuntimeError("Checkpoint baseline bukan ANN.")
            encoder = keras.applications.MobileNetV2(
                input_shape=(160, 160, 3),
                include_top=False,
                weights=str(
                    ann_folder
                    / "mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_160_no_top.h5"
                ),
                pooling="avg",
            )
            encoder.trainable = False
            head = keras.models.load_model(ann_folder / "activity_model.keras")
            with torch.inference_mode():
                warm = keras.applications.mobilenet_v2.preprocess_input(
                    np.zeros((16, 160, 160, 3), dtype="float32")
                )
                f = keras.ops.convert_to_numpy(encoder(warm, training=False))
                head(f[None], training=False)
            MODELS["ann"] = {
                "encoder": encoder,
                "head": head,
                "config": cfg,
                "keras": keras,
            }
        STATUS["ann"] = {
            "state": "ready",
            "name": "MobileNetV2 + ANN",
            "frames": 16,
            "device": DEVICE,
            "training": "Classifier dilatih pada KTH; backbone pralatih.",
        }
    except Exception as e:
        LOGGER.exception("ANN load failed")
        STATUS["ann"] = {"state": "error", "message": str(e)}
    try:
        from transformers import XCLIPProcessor, XCLIPModel

        folder = MODEL_ROOT / "xclip"
        with GPU_LOCK:
            processor = XCLIPProcessor.from_pretrained(folder, local_files_only=True)
            model = XCLIPModel.from_pretrained(
                folder, local_files_only=True, use_safetensors=True
            ).eval()
            if DEVICE == "cuda":
                model = model.cuda().half()
            else:
                model = model.to("cpu")
            for p in model.parameters():
                p.requires_grad = False
            with torch.inference_mode():
                warm = processor(
                    text=PROMPTS,
                    images=[np.zeros((224, 224, 3), dtype="uint8")]
                    * model.config.vision_config.num_frames,
                    return_tensors="pt",
                    padding=True,
                )
                target_dtype = torch.float16 if DEVICE == "cuda" else torch.float32
                warm = {
                    k: v.to(
                        DEVICE,
                        dtype=target_dtype if torch.is_floating_point(v) else v.dtype,
                    )
                    for k, v in warm.items()
                }
                model(**warm)
            MODELS["xclip"] = {"processor": processor, "model": model, "device": DEVICE}
        STATUS["xclip"] = {
            "state": "ready",
            "name": "Microsoft X-CLIP zero-shot",
            "frames": model.config.vision_config.num_frames,
            "device": DEVICE,
            "training": "Bobot pralatih asli; tanpa training pada data proyek.",
        }
    except Exception as e:
        LOGGER.exception("XCLIP load failed")
        STATUS["xclip"] = {"state": "error", "message": str(e)}
    try:
        from hybrid import HybridAnalyzer

        with GPU_LOCK:
            MODELS["hybrid"] = HybridAnalyzer(
                MODELS.get("xclip"), device=DEVICE, model_root=MODEL_ROOT
            )
        STATUS["hybrid"] = {
            "state": "ready",
            "name": "YOLO + MediaPipe + X-CLIP",
            "frames": 32,
            "device": DEVICE,
            "training": "Semua komponen pralatih; tidak ada training tambahan.",
            "body_action_available": "xclip" in MODELS,
        }
    except Exception as e:
        LOGGER.exception("Hybrid load failed")
        STATUS["hybrid"] = {"state": "error", "message": str(e)}


@asynccontextmanager
async def lifespan(app):
    task = (
        asyncio.create_task(asyncio.to_thread(load_models))
        if not DISABLE_MODELS
        else None
    )
    yield
    if task and not task.done():
        task.cancel()


app = FastAPI(title="Activity Lab inference", version="2.0.0", lifespan=lifespan)
origins = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if o.strip()
]
if "*" in origins:
    raise RuntimeError("Use explicit ALLOWED_ORIGINS, not a wildcard.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.add_middleware(BodyLimitMiddleware, max_bytes=6_000_000)


@app.get("/ready")
def ready():
    from fastapi.responses import JSONResponse

    available = (
        STATUS["hybrid"]["state"] == "ready" and STATUS["ann"]["state"] == "ready"
    )
    return JSONResponse(
        {"ready": available, "models": STATUS}, status_code=200 if available else 503
    )


@app.get("/health")
def health():
    gpu_name = (
        torch.cuda.get_device_name(0)
        if torch.cuda.is_available()
        else f"CPU ({os.cpu_count() or 6} threads)"
    )
    return {
        "ok": True,
        "models": STATUS,
        "gpu": gpu_name,
        "device": DEVICE,
        "classes": CLASSES,
        "window_seconds": 2.0,
        "video_saved": False,
        "hybrid_capabilities": {
            "object_classes": 80,
            "face_landmarks": 478,
            "hand_landmarks": 21,
            "built_in_hand_gestures": 7,
            "face_blendshapes": 52,
            "custom_body_actions": True,
            "drowsiness_detection": True,
            "fall_detection": True,
            "age_detection": False,
        },
    }


class Clip(BaseModel):
    model: Literal["ann", "xclip", "hybrid"]
    frames: list[str] = Field(min_length=1, max_length=40)
    timestamps: list[float] = Field(min_length=1, max_length=40)
    request_id: int = 0
    session_id: str = Field(default="", max_length=64)
    mode: Literal["auto", "body", "face", "hand", "objects"] = "auto"
    custom_actions: list[str] = Field(default_factory=list, max_length=20)
    drowsiness_enabled: bool = False
    fall_detection_enabled: bool = False
    age_detection_enabled: bool = False


def decode(clip):
    if len(clip.frames) != len(clip.timestamps):
        raise ValueError("Jumlah timestamp tidak sesuai.")
    ts = np.array(clip.timestamps)
    if not np.isfinite(ts).all() or (np.diff(ts) <= 0).any():
        raise ValueError("Timestamp harus meningkat.")
    if clip.model != "hybrid" and (len(ts) < 8 or ts[-1] - ts[0] < 1.6):
        raise ValueError("Klip membutuhkan sekitar dua detik data.")
    if ts[-1] - ts[0] > 3.0:
        raise ValueError("Jendela terlalu panjang.")
    if any(len(a) > 120 for a in clip.custom_actions):
        raise ValueError("Deskripsi aksi terlalu panjang.")
    images = []
    for value in clip.frames:
        if len(value) > 180_000:
            raise ValueError("Frame terlalu besar.")
        raw = base64.b64decode(value.split(",")[-1], validate=True)
        with Image.open(io.BytesIO(raw)) as image:
            if image.width > 1024 or image.height > 1024:
                raise ValueError("Resolusi frame terlalu besar.")
            images.append(np.array(image.convert("RGB")))
    return images, ts


def predict(clip):
    images, ts = decode(clip)
    with GPU_LOCK, torch.inference_mode():
        sync_gpu()
        start = time.perf_counter()
        bundle = MODELS[clip.model]
        if clip.model == "hybrid":
            result = bundle.analyze(
                images,
                ts,
                session=clip.session_id,
                manual=clip.mode,
                custom_actions=clip.custom_actions,
                drowsiness_enabled=clip.drowsiness_enabled,
                fall_detection_enabled=clip.fall_detection_enabled,
                age_detection_enabled=clip.age_detection_enabled,
            )
            sync_gpu()
            result.update(
                {
                    "model": "hybrid",
                    "request_id": clip.request_id,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 1),
                    "clip_seconds": round(float(ts[-1] - ts[0]), 2),
                }
            )
            return result
        count = (
            16
            if clip.model == "ann"
            else bundle["model"].config.vision_config.num_frames
        )
        indices = np.abs(ts[:, None] - np.linspace(ts[-1] - 2.0, ts[-1], count)).argmin(
            axis=0
        )
        selected = [images[i] for i in indices]
        if clip.model == "ann":
            keras = bundle["keras"]
            frames = []
            for image in selected:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                frames.append(
                    cv2.resize(
                        cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB),
                        (160, 160),
                        interpolation=cv2.INTER_AREA,
                    )
                )
            x = keras.applications.mobilenet_v2.preprocess_input(
                np.stack(frames).astype("float32")
            )
            f = keras.ops.convert_to_numpy(bundle["encoder"](x, training=False))
            p = keras.ops.convert_to_numpy(bundle["head"](f[None], training=False))[0]
        else:
            inputs = bundle["processor"](
                text=PROMPTS, images=selected, return_tensors="pt", padding=True
            )
            if "pixel_values" not in inputs:
                raise ValueError("X-CLIP tidak menerima tensor frame.")
            dev = bundle.get("device", DEVICE)
            target_dtype = torch.float16 if dev == "cuda" else torch.float32
            inputs = {
                k: v.to(
                    device=dev,
                    dtype=target_dtype if torch.is_floating_point(v) else v.dtype,
                )
                for k, v in inputs.items()
            }
            output = bundle["model"](**inputs)
            p = output.logits_per_video[0].float().softmax(-1).cpu().numpy()
        sync_gpu()
        latency = (time.perf_counter() - start) * 1000
    if p.shape != (6,) or not np.isfinite(p).all():
        raise ValueError("Hasil model tidak valid.")
    winner = int(p.argmax())
    return {
        "model": clip.model,
        "request_id": clip.request_id,
        "label": CLASSES[winner],
        "score": float(p[winner]),
        "scores": {name: float(v) for name, v in zip(CLASSES, p)},
        "latency_ms": round(latency, 1),
        "clip_seconds": round(float(ts[-1] - ts[0]), 2),
        "frames_used": count,
        "uncertain": bool(p[winner] < 0.45),
        "note": "Skor relatif antar kandidat, bukan kepastian terkalibrasi.",
    }


@app.post("/infer")
async def infer(clip: Clip):
    if STATUS[clip.model]["state"] != "ready":
        raise HTTPException(
            503,
            "Model belum siap: " + STATUS[clip.model].get("message", "sedang dimuat"),
        )
    if not GATE.acquire():
        raise HTTPException(
            429,
            "Server sedang sibuk; coba lagi setelah permintaan aktif selesai.",
            headers={"Retry-After": "1"},
        )

    def work():
        try:
            return predict(clip)
        finally:
            GATE.release()

    try:
        # Shield: cancellation must not free admission while its thread still runs.
        return await asyncio.shield(asyncio.create_task(asyncio.to_thread(work)))
    except (ValueError, UnidentifiedImageError) as e:
        raise HTTPException(422, str(e))
    except Exception:
        LOGGER.exception("Inference failed")
        raise HTTPException(500, "Inferensi gagal. Periksa log backend.")
