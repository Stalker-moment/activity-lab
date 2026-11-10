"""Cache only text encoder output; preserve X-CLIP video-conditioned prompts.
Matches Transformers 4.57.3 XCLIPModel.forward, excluding loss/diagnostics.
"""

from collections import OrderedDict
import torch


class CachedXClip:
    def __init__(self, bundle, max_entries=4):
        self.bundle = bundle
        self.cache = OrderedDict()
        self.max_entries = max_entries

    @torch.inference_mode()
    def logits(self, prompts, images):
        model = self.bundle["model"]
        processor = self.bundle["processor"]
        dev = next(model.parameters()).device
        dtype = next(model.parameters()).dtype
        key = tuple(prompts)
        if key not in self.cache:
            text = processor(text=list(prompts), padding=True, return_tensors="pt")
            text = {k: v.to(dev) for k, v in text.items()}
            # Keep unnormalized projected text: prompt generator needs original scale.
            self.cache[key] = model.get_text_features(**text).detach()
        self.cache.move_to_end(key)
        while len(self.cache) > self.max_entries:
            self.cache.popitem(last=False)
        values = processor(images=images, return_tensors="pt")["pixel_values"].to(
            dev, dtype=dtype
        )
        batch, frames, channels, height, width = values.shape
        vision = model.vision_model(
            pixel_values=values.reshape(-1, channels, height, width), return_dict=True
        )
        projected = model.visual_projection(vision.pooler_output).view(
            batch, frames, -1
        )
        video = model.mit(projected, return_dict=True).pooler_output
        visual = (
            model.prompts_visual_layernorm(vision.last_hidden_state[:, 1:, :])
            @ model.prompts_visual_projection
        )
        visual = visual.view(batch, frames, -1, video.shape[-1]).mean(dim=1)
        text = self.cache[key].unsqueeze(0).expand(batch, -1, -1)
        text = text + model.prompts_generator(text, visual)
        video = video / video.norm(p=2, dim=-1, keepdim=True)
        text = text / text.norm(p=2, dim=-1, keepdim=True)
        return torch.einsum("bd,bkd->bk", video, model.logit_scale.exp() * text)

    def probabilities(self, prompts, images):
        return self.logits(prompts, images)[0].float().softmax(-1).cpu().numpy()
