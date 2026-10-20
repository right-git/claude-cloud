#!/usr/bin/env python3
"""Re-render an image through a simulated camera pipeline (red-team test for AI-image detectors).

AI-image classifiers (Hive, etc.) mostly key on pixel-level statistics left by the
generator: periodic upsampling artifacts in the high-frequency spectrum, overly clean
noise-free flat areas, and the absence of camera ISP traces (Bayer demosaicing
correlations, signal-dependent sensor noise, lens optics, camera JPEG).
Stripping C2PA/EXIF alone does nothing for a pixel classifier, so this script
attacks the pixel statistics instead:

  1. drop all metadata (C2PA / EXIF / XMP)
  2. sub-pixel rotate + crop + resample   -> breaks the generator's upsampling grid
  3. spectral cleanup: cut periodic peaks in the high-frequency FFT band
  4. lens: chromatic aberration, slight softness, vignetting
  5. Bayer RGGB mosaic + demosaic          -> real-camera CFA interpolation traces
  6. sensor noise: Poisson-Gaussian (signal dependent) + PRNU fixed pattern
  7. ISP: tone curve, mild unsharp mask
  8. JPEG 4:2:0 at camera-like quality

Usage:
  python3 camerafy.py in.jpg out.jpg                # default preset: light
  python3 camerafy.py photos/ photos_out/           # whole folder (-r for subfolders)
  python3 camerafy.py in.jpg outdir/ --sweep     # writes every preset, for A/B testing
"""
import argparse
import io
import os

import numpy as np
from PIL import Image, ImageFilter, ImageOps

PRESETS = {
    "light":  dict(rot=0.4, crop=0.01, scale=0.97, fft=0.5, ca=0.0006, blur=0.35, vign=0.05,
                   bayer=True, iso=0.004, read=1.2, prnu=0.004, sharpen=60, q=92),
    "medium": dict(rot=0.8, crop=0.02, scale=0.92, fft=0.7, ca=0.0010, blur=0.5, vign=0.08,
                   bayer=True, iso=0.008, read=2.0, prnu=0.006, sharpen=80, q=88),
    "strong": dict(rot=1.2, crop=0.03, scale=0.85, fft=0.85, ca=0.0015, blur=0.7, vign=0.10,
                   bayer=True, iso=0.014, read=3.0, prnu=0.008, sharpen=100, q=85),
    "heavy":  dict(rot=1.5, crop=0.04, scale=0.75, fft=0.9, ca=0.0020, blur=0.9, vign=0.12,
                   bayer=True, iso=0.022, read=4.0, prnu=0.010, sharpen=110, q=82),
    # watermark scrub: strong local warp + heavy spectral/sensor rework, no ML download
    "scrub":  dict(rot=0.8, crop=0.02, scale=0.88, fft=0.9, ca=0.0012, blur=0.5, vign=0.06,
                   bayer=True, iso=0.012, read=2.5, prnu=0.008, sharpen=85, q=90,
                   warp=2.2, warp_smooth=10),
}


def geometric(img, rot, crop, scale, rng):
    w, h = img.size
    angle = rng.uniform(-rot, rot)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False)
    # crop away rotated borders + a random offset so the 8x8/16x16 grids no longer align
    c = crop + abs(np.sin(np.radians(angle))) * 0.6
    dx, dy = int(w * c), int(h * c)
    ox, oy = rng.integers(0, 4), rng.integers(0, 4)
    img = img.crop((dx + ox, dy + oy, w - dx + ox - 4, h - dy + oy - 4))
    nw, nh = int(img.width * scale), int(img.height * scale)
    return img.resize((nw, nh), Image.LANCZOS)


def suppress_spectral_peaks(a, strength):
    """Damp isolated periodic peaks in the high-frequency band (generator upsampling fingerprint)."""
    out = np.empty_like(a)
    h, w = a.shape[:2]
    yy, xx = np.meshgrid(np.arange(h) - h // 2, np.arange(w) - w // 2, indexing="ij")
    r = np.sqrt((yy / (h / 2)) ** 2 + (xx / (w / 2)) ** 2)
    hf = r > 0.25
    for ch in range(3):
        F = np.fft.fftshift(np.fft.fft2(a[..., ch]))
        mag = np.abs(F)
        # local median-ish background via box blur of log magnitude
        logm = np.log1p(mag)
        k = 9
        pad = np.pad(logm, k // 2, mode="reflect")
        cs = pad.cumsum(0).cumsum(1)
        cs = np.pad(cs, ((1, 0), (1, 0)))
        bg = (cs[k:, k:] - cs[:-k, k:] - cs[k:, :-k] + cs[:-k, :-k]) / (k * k)
        peak = (logm - bg) > 1.2
        mask = hf & peak
        target = np.expm1(bg)
        newmag = np.where(mask, mag * (1 - strength) + target * strength, mag)
        F = F * (newmag / np.maximum(mag, 1e-8))
        out[..., ch] = np.real(np.fft.ifft2(np.fft.ifftshift(F)))
    return out


def chromatic_aberration(a, amount):
    h, w = a.shape[:2]
    out = a.copy()
    for ch, s in ((0, 1 + amount), (2, 1 - amount)):
        img = Image.fromarray(np.clip(a[..., ch], 0, 255).astype(np.uint8))
        nw, nh = round(w * s), round(h * s)
        img = img.resize((nw, nh), Image.BICUBIC)
        canvas = Image.new("L", (w, h))
        canvas.paste(img, ((w - nw) // 2, (h - nh) // 2))
        if s > 1:
            canvas = img.crop(((nw - w) // 2, (nh - h) // 2, (nw - w) // 2 + w, (nh - h) // 2 + h))
        else:
            # fill thin border with the original channel
            arr = np.asarray(canvas, dtype=np.float32)
            border = arr == 0
            arr[border] = a[..., ch][border]
            out[..., ch] = arr
            continue
        out[..., ch] = np.asarray(canvas, dtype=np.float32)
    return out


def vignette(a, strength):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r2 = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    return a * (1 - strength * r2 / 2)[..., None]


def mosaic(a):
    """RGGB Bayer mosaic: keep one colour sample per pixel."""
    h, w = a.shape[:2]
    h -= h % 2
    w -= w % 2
    a = a[:h, :w]
    m = np.zeros((h, w, 3), np.float32)
    msk = np.zeros((h, w, 3), np.float32)
    m[0::2, 0::2, 0] = a[0::2, 0::2, 0]; msk[0::2, 0::2, 0] = 1
    m[0::2, 1::2, 1] = a[0::2, 1::2, 1]; msk[0::2, 1::2, 1] = 1
    m[1::2, 0::2, 1] = a[1::2, 0::2, 1]; msk[1::2, 0::2, 1] = 1
    m[1::2, 1::2, 2] = a[1::2, 1::2, 2]; msk[1::2, 1::2, 2] = 1
    return m, msk


def demosaic(m, msk):
    """Bilinear demosaic (introduces real-camera CFA interpolation correlations)."""
    def conv3(x, k):
        p = np.pad(x, 1, mode="reflect")
        o = np.zeros_like(x)
        for i in range(3):
            for j in range(3):
                o += k[i, j] * p[i:i + x.shape[0], j:j + x.shape[1]]
        return o

    k = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], np.float32)
    out = np.empty_like(m)
    for ch in range(3):
        out[..., ch] = conv3(m[..., ch], k) / np.maximum(conv3(msk[..., ch], k), 1e-6)
    return out


def sensor_noise(a, iso, read, prnu, rng):
    lin = np.clip(a / 255.0, 0, 1) ** 2.2
    # PRNU: fixed multiplicative pattern, low-pass so it looks like a real sensor fingerprint
    pattern = rng.normal(0, 1, a.shape[:2]).astype(np.float32)
    pattern = np.asarray(Image.fromarray(((pattern * 40) + 128).clip(0, 255).astype(np.uint8))
                         .filter(ImageFilter.GaussianBlur(0.6)), np.float32)
    pattern = (pattern - 128) / 40
    lin = lin * (1 + prnu * pattern[..., None])
    # shot noise (variance ∝ signal) + read noise
    shot = rng.normal(0, 1, lin.shape) * np.sqrt(np.maximum(lin, 0) * iso)
    lin = lin + shot + rng.normal(0, read / 255.0, lin.shape) * 0.5
    return np.clip(lin, 0, 1) ** (1 / 2.2) * 255.0


def tone_curve(a):
    x = np.clip(a / 255.0, 0, 1)
    s = x + 0.06 * np.sin(2 * np.pi * x) * (1 - x) * x * 4 * 0.5  # gentle S-curve
    return np.clip(s, 0, 1) * 255.0


def elastic_warp(a, amp, smooth, rng):
    """Smooth random local warp. Desynchronises spatial watermarks (SynthID-style)
    whose detector relies on pixel alignment, with almost no visible change."""
    h, w = a.shape[:2]
    def field():
        n = rng.normal(0, 1, (h, w)).astype(np.float32)
        n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(smooth)), np.float32)
        n = (n - n.mean())
        return n / (np.abs(n).max() + 1e-6) * amp
    dx, dy = field(), field()
    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
    sx = np.clip(xx + dx, 0, w - 1.001).astype(np.float32)
    sy = np.clip(yy + dy, 0, h - 1.001).astype(np.float32)
    x0, y0 = np.floor(sx).astype(int), np.floor(sy).astype(int)
    x1, y1 = x0 + 1, y0 + 1
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    out = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x1] * fx * (1 - fy)
           + a[y1, x0] * (1 - fx) * fy + a[y1, x1] * fx * fy)
    return out


def camerafy(img, p, seed=None):
    rng = np.random.default_rng(seed)
    img = img.convert("RGB")  # pixels only: drops C2PA/EXIF/XMP/ICC
    img = geometric(img, p["rot"], p["crop"], p["scale"], rng)
    a = np.asarray(img, np.float32)
    if p.get("warp", 0):
        a = elastic_warp(a, p["warp"], p.get("warp_smooth", 12), rng)
    a = suppress_spectral_peaks(a, p["fft"])
    a = chromatic_aberration(a, p["ca"])
    a = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(p["blur"])), np.float32)
    a = vignette(a, p["vign"])
    if p["bayer"]:
        # add noise at the raw (mosaic) stage, as a real sensor does, then demosaic
        m, msk = mosaic(a)
        m = sensor_noise(m, p["iso"], p["read"], p["prnu"], rng) * msk
        a = demosaic(m, msk)
    else:
        a = sensor_noise(a, p["iso"], p["read"], p["prnu"], rng)
    a = tone_curve(a)
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    out = out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=p["sharpen"], threshold=2))
    return out


def save_jpeg(img, path, q):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q, subsampling="4:2:0", optimize=True)  # no exif written
    with open(path, "wb") as f:
        f.write(buf.getvalue())


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def process(path, out_path, p, passes, seed):
    img = ImageOps.exif_transpose(Image.open(path))  # keep phone photos upright
    for i in range(passes):
        img = camerafy(img, p, None if seed is None else seed + i)
    save_jpeg(img, out_path, p["q"])
    return img.size


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="image file or folder with images")
    ap.add_argument("output", help="output .jpg (for a single file) or output folder")
    ap.add_argument("--preset", choices=PRESETS, default="light")
    ap.add_argument("--sweep", action="store_true", help="write every preset into output dir")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--passes", type=int, default=1, help="repeat the pipeline N times")
    ap.add_argument("-r", "--recursive", action="store_true", help="also process subfolders")
    args = ap.parse_args()

    presets = list(PRESETS.items()) if args.sweep else [(args.preset, PRESETS[args.preset])]

    if os.path.isdir(args.input):
        files = []
        for root, dirs, names in os.walk(args.input):
            files += [os.path.join(root, n) for n in sorted(names)
                      if os.path.splitext(n)[1].lower() in IMAGE_EXTS]
            if not args.recursive:
                break
        if not files:
            raise SystemExit(f"no images found in {args.input}")
        ok = 0
        for f in sorted(files):
            rel = os.path.splitext(os.path.relpath(f, args.input))[0]
            for name, p in presets:
                suffix = f"_{name}" if args.sweep else ""
                out = os.path.join(args.output, rel + suffix + ".jpg")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                try:
                    size = process(f, out, p, args.passes, args.seed)
                    print(f"[ok] {f} -> {out} {size}")
                    ok += 1
                except Exception as e:  # keep going on broken files
                    print(f"[fail] {f}: {e}")
        print(f"done: {ok} image(s) written to {args.output}")
        return

    if args.sweep:
        os.makedirs(args.output, exist_ok=True)
    for name, p in presets:
        out = os.path.join(args.output, f"{name}.jpg") if args.sweep else args.output
        if os.path.dirname(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
        size = process(args.input, out, p, args.passes, args.seed)
        print(f"{name}: {out} {size}")


if __name__ == "__main__":
    main()
