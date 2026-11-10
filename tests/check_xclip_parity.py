"""Parity test against the original full pretrained X-CLIP forward pass."""

from pathlib import Path
import sys, json, numpy as np, torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from transformers import XCLIPModel, XCLIPProcessor
from xclip_cache import CachedXClip

root = Path(__file__).resolve().parents[1]
folder = root / "backend/models/xclip"
device = "cuda" if torch.cuda.is_available() else "cpu"
model = XCLIPModel.from_pretrained(folder, local_files_only=True).eval().to(device)
if device == "cuda":
    model.half()
processor = XCLIPProcessor.from_pretrained(folder, local_files_only=True)
images = [
    np.random.default_rng(i).integers(0, 255, (224, 224, 3), dtype=np.uint8)
    for i in range(32)
]
prompts = ["A person walking.", "A person waving.", "A person sitting."]
cache = CachedXClip({"model": model, "processor": processor})
with torch.inference_mode():
    data = processor(text=prompts, images=images, return_tensors="pt", padding=True)
    data = {
        k: v.to(
            device,
            dtype=next(model.parameters()).dtype
            if torch.is_floating_point(v)
            else v.dtype,
        )
        for k, v in data.items()
    }
    original = model(**data).logits_per_video
    cold = cache.logits(prompts, images)
    warm = cache.logits(prompts, images)
    torch.testing.assert_close(
        original, cold, atol=0.04 if device == "cuda" else 1e-4, rtol=0.003
    )
    torch.testing.assert_close(cold, warm, atol=0, rtol=0)
    report = {
        "device": device,
        "max_logit_error": float((original - cold).abs().max()),
        "cache_entries": len(cache.cache),
        "passed": True,
    }
    (root / "docs/xclip-parity.json").write_text(json.dumps(report, indent=2))
    print(report)
