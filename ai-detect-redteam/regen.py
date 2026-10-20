#!/usr/bin/env python3
"""Diffusion regeneration attack on invisible image watermarks (hackathon red-team).

Watermarks like SynthID / OpenAI's signal are embedded in the fine pixel structure
and are built to survive JPEG, noise, resize and colour tweaks — so the camera
simulation in camerafy.py does NOT remove them. The reliable attack is to let an
open-source diffusion model *repaint* that pixel structure (img2img at low strength):
composition and face stay, but the exact pixels carrying the mark are drawn anew.

Runs on Apple Silicon (MPS), NVIDIA (CUDA) or CPU. Tuned defaults for an M1 Pro.

Typical flow for the hackathon:
    python3 regen.py samples/sample_synthid.png out/regen.png --strength 0.4
    python3 camerafy.py out/regen.png out/final.jpg          # keep detector #1 low too

Sweep strengths to find the lowest one that still reads 0% on hivedetect:
    python3 regen.py samples/sample_synthid.png out/ --sweep

Whole folder:
    python3 regen.py photos/ photos_out/ --strength 0.4
"""
import argparse
import os

import torch
from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}

try:  # allow .heic input straight from an iPhone
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass


def pick_device():
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def load_vae(device):
    """~320 MB standalone VAE. Encode->decode lossily rebuilds the pixels, which
    erases fragile watermarks. Far lighter than a full diffusion model."""
    from diffusers import AutoencoderKL
    dtype = torch.float16 if device == "cuda" else torch.float32
    vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse", torch_dtype=dtype).to(device)
    vae.eval()
    return vae


def vae_roundtrip(vae, img, device):
    import numpy as np
    a = torch.from_numpy(np.asarray(img, np.float32) / 127.5 - 1.0)
    a = a.permute(2, 0, 1).unsqueeze(0).to(device, vae.dtype)
    with torch.no_grad():
        lat = vae.encode(a).latent_dist.mean
        out = vae.decode(lat).sample
    out = ((out.squeeze(0).permute(1, 2, 0).float().cpu().numpy() + 1.0) * 127.5).clip(0, 255)
    return Image.fromarray(out.astype("uint8"))


def load_pipe(model, device):
    from diffusers import AutoPipelineForImage2Image
    # fp16 on CUDA; fp32 on MPS/CPU (MPS fp16 can produce NaNs in the SDXL VAE)
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = AutoPipelineForImage2Image.from_pretrained(model, torch_dtype=dtype)
    pipe = pipe.to(device)
    pipe.set_progress_bar_config(disable=True)
    try:
        pipe.safety_checker = None  # don't blank real portraits
    except Exception:
        pass
    return pipe


def to_mult8(im, max_side):
    w, h = im.size
    s = min(max_side / max(w, h), 1.0)
    w, h = max(8, round(w * s / 8) * 8), max(8, round(h * s / 8) * 8)
    return im.resize((w, h), Image.LANCZOS)


def regen(pipe, img, strength, steps, guidance, prompt, neg, seed, is_turbo):
    gen = None if seed is None else torch.Generator(device="cpu").manual_seed(seed)
    # diffusers runs int(steps*strength) denoising steps; keep at least 2 effective
    eff = max(steps, int(-(-2 // max(strength, 1e-3))))
    kw = dict(image=img, strength=strength, num_inference_steps=eff,
              guidance_scale=guidance, generator=gen)
    if is_turbo:
        kw["guidance_scale"] = 0.0
    out = pipe(prompt=prompt, negative_prompt=(None if is_turbo else neg), **kw)
    return out.images[0]


def iter_inputs(path):
    if os.path.isdir(path):
        for root, _, names in os.walk(path):
            for n in sorted(names):
                if os.path.splitext(n)[1].lower() in IMAGE_EXTS:
                    yield os.path.join(root, n), os.path.relpath(os.path.join(root, n), path)
    else:
        yield path, os.path.basename(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="image file or folder")
    ap.add_argument("output", help="output file (single) or folder")
    ap.add_argument("--model", default="stabilityai/sdxl-turbo",
                    help="HF model id. Turbo = fast (default). For a stronger scrub use a "
                         "non-turbo SDXL, e.g. stabilityai/stable-diffusion-xl-base-1.0")
    ap.add_argument("--strength", type=float, default=0.4,
                    help="0.3-0.5 removes the mark while keeping the face; higher = safer "
                         "removal but more drift")
    ap.add_argument("--steps", type=int, default=6)
    ap.add_argument("--guidance", type=float, default=2.0, help="ignored for turbo models")
    ap.add_argument("--prompt", default="a candid photo of a person, natural lighting, detailed skin")
    ap.add_argument("--negative", default="cartoon, painting, cgi, blurry, deformed, extra fingers")
    ap.add_argument("--max-side", type=int, default=1024, help="longest side fed to the model")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--sweep", action="store_true",
                    help="write strengths 0.25/0.35/0.45/0.55 side by side")
    ap.add_argument("--vae-only", action="store_true",
                    help="light mode: ~320 MB VAE round-trip instead of a full diffusion model")
    args = ap.parse_args()

    device = pick_device()
    if args.vae_only:
        print(f"device={device}  mode=vae-only (~320 MB)")
        vae = load_vae(device)
        for src, rel in iter_inputs(args.input):
            base = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            small = to_mult8(base, args.max_side)
            res = vae_roundtrip(vae, small, device).resize(base.size, Image.LANCZOS)
            out = args.output if not os.path.isdir(args.input) else \
                os.path.join(args.output, os.path.splitext(rel)[0] + ".png")
            if os.path.dirname(out):
                os.makedirs(os.path.dirname(out), exist_ok=True)
            res.save(out)
            print(f"[ok] {src} -> {out}")
        return

    is_turbo = "turbo" in args.model.lower()
    print(f"device={device}  model={args.model}  turbo={is_turbo}")
    pipe = load_pipe(args.model, device)

    strengths = [0.25, 0.35, 0.45, 0.55] if args.sweep else [args.strength]
    single_file = not os.path.isdir(args.input) and not args.sweep

    for src, rel in iter_inputs(args.input):
        base = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        orig_size = base.size
        small = to_mult8(base, args.max_side)
        for s in strengths:
            try:
                res = regen(pipe, small, s, args.steps, args.guidance,
                            args.prompt, args.negative, args.seed, is_turbo)
            except Exception as e:
                print(f"[fail] {src} @ {s}: {e}")
                continue
            res = res.resize(orig_size, Image.LANCZOS)
            if single_file:
                out = args.output
            else:
                stem, _ = os.path.splitext(rel)
                suffix = f"_s{int(s*100)}" if args.sweep else ""
                out = os.path.join(args.output, stem + suffix + ".png")
            if os.path.dirname(out):
                os.makedirs(os.path.dirname(out), exist_ok=True)
            res.save(out)
            print(f"[ok] {src} @ strength {s} -> {out}")


if __name__ == "__main__":
    main()
