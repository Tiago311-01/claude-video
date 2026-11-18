#!/usr/bin/env python3
"""Générateur de vidéos TikTok verticales (1080x1920) à partir d'une histoire JSON.

Usage :
    python3 generateur/generer.py histoires/<id>.json [-o videos/<id>.mp4]

Chaîne 100 % gratuite :
  - voix off : edge-tts (voix neuronales Microsoft, gratuites) avec horodatage mot par mot
  - visuels  : Pollinations.ai (générateur d'images gratuit) ; repli procédural (PIL) si indisponible
  - musique  : nappe d'ambiance synthétisée ici même (numpy) -> 100 % originale, sans droits
  - montage  : PIL (Ken Burns, fondus, grain, vignette, sous-titres mot par mot, barre de progression)
               + ffmpeg (encodage H.264, normalisation du volume à -14 LUFS)

Format JSON attendu : voir histoires/MODELE.json
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import wave
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
W, H, FPS = 1080, 1920, 30
SR = 48000
SRC_SCALE = 1.25  # l'image source est 25 % plus grande que l'écran pour le Ken Burns
GAP = 0.32  # silence entre deux segments de voix (s)
XFADE = 0.45  # fondu enchaîné entre deux visuels (s)

# --------------------------------------------------------------------------------------
# Réseau : dans le conteneur cloud, un proxy TLS impose son propre certificat racine.
# --------------------------------------------------------------------------------------
_CA = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
if os.path.exists(_CA):
    try:
        import certifi  # edge-tts lit certifi.where()

        certifi.where = lambda: _CA  # type: ignore[assignment]
    except ImportError:
        pass


def log(*a):
    print("[generer]", *a, flush=True)


def run(cmd: list[str]):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Commande échouée: {' '.join(cmd[:6])}...\n{r.stderr[-2000:]}")
    return r


# --------------------------------------------------------------------------------------
# Polices
# --------------------------------------------------------------------------------------
FONT_CANDIDATES_BLACK = [
    "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "C:/Windows/Fonts/ariblk.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
    "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def find_font(cands):
    local = ROOT / "generateur" / "polices"
    for p in sorted(local.glob("*")) if local.exists() else []:
        if p.suffix.lower() in (".ttf", ".otf"):
            return str(p)
    for c in cands:
        if os.path.exists(c):
            return c
    return None


_font_cache: dict = {}


def font(kind: str, size: int):
    key = (kind, size)
    if key not in _font_cache:
        path = find_font(FONT_CANDIDATES_BLACK if kind == "black" else FONT_CANDIDATES_BOLD)
        _font_cache[key] = ImageFont.truetype(path, size) if path else ImageFont.load_default()
    return _font_cache[key]


# --------------------------------------------------------------------------------------
# Voix off (edge-tts)
# --------------------------------------------------------------------------------------
async def _tts(text: str, voice: str, rate: str, pitch: str, out_mp3: Path):
    import edge_tts

    words = []
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    with open(out_mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7, "w": ch["text"]})
    return words


def tts_segment(text: str, voice: str, rate: str, pitch: str) -> tuple[np.ndarray, list]:
    h = hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    d = CACHE / "tts"
    d.mkdir(parents=True, exist_ok=True)
    mp3, js, wav = d / f"{h}.mp3", d / f"{h}.json", d / f"{h}.wav"
    if not (wav.exists() and js.exists()):
        last = None
        for _ in range(3):
            try:
                words = asyncio.run(_tts(text, voice, rate, pitch, mp3))
                if mp3.stat().st_size > 1000:
                    break
            except Exception as e:  # réseau capricieux : on réessaie
                last = e
        else:
            raise RuntimeError(f"Synthèse vocale impossible : {last}")
        run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR), str(wav)])
        js.write_text(json.dumps(words, ensure_ascii=False))
    with wave.open(str(wav)) as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return pcm, json.loads(js.read_text())


# --------------------------------------------------------------------------------------
# Visuels
# --------------------------------------------------------------------------------------
STYLE_SUFFIX = (
    ", cinematic digital painting, dramatic volumetric lighting, moody, high detail, "
    "vertical composition, no text, no watermark, no logo"
)


def fetch_image(prompt: str, seed: int) -> Image.Image | None:
    import requests

    tw, th = int(W * SRC_SCALE), int(H * SRC_SCALE)
    h = hashlib.sha1(f"{prompt}|{seed}".encode()).hexdigest()[:16]
    p = CACHE / "img" / f"{h}.jpg"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        url = (
            "https://image.pollinations.ai/prompt/"
            + urllib.parse.quote(prompt + STYLE_SUFFIX)
            + f"?width=1080&height=1920&seed={seed}&nologo=true&model=flux"
        )
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=120, verify=_CA if os.path.exists(_CA) else True)
                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                    p.write_bytes(r.content)
                    break
                log(f"image HTTP {r.status_code} (essai {attempt + 1})")
            except Exception as e:
                log(f"image erreur {e} (essai {attempt + 1})")
        else:
            return None
    im = Image.open(p).convert("RGB")
    # retire le filigrane éventuel en bas à droite : on recadre les 7 % du bas
    im = im.crop((0, 0, im.width, int(im.height * 0.93)))
    return cover(im, tw, th)


def cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    s = max(tw / im.width, th / im.height)
    im = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
    x, y = (im.width - tw) // 2, (im.height - th) // 2
    return im.crop((x, y, x + tw, y + th))


def procedural_image(seed: int, palette: str) -> Image.Image:
    """Visuel de secours 100 % local : ciel dégradé, brume, silhouettes, lune."""
    rng = np.random.default_rng(seed)
    tw, th = int(W * SRC_SCALE), int(H * SRC_SCALE)
    pals = {
        "nuit": [(8, 12, 28), (30, 40, 70), (120, 130, 160)],
        "sang": [(20, 4, 8), (90, 15, 25), (200, 80, 60)],
        "brume": [(15, 20, 22), (60, 75, 80), (170, 185, 185)],
        "or": [(18, 10, 4), (90, 55, 20), (230, 170, 90)],
    }
    a, b, c = [np.array(x, dtype=np.float32) for x in pals.get(palette, pals["nuit"])]
    y = np.linspace(0, 1, th)[:, None, None]
    img = np.where(y < 0.6, a + (b - a) * (y / 0.6), b + (c - b) * ((y - 0.6) / 0.4) * 0.5)
    img = np.repeat(img, tw, axis=1)
    noise = rng.normal(0, 1, (th // 8, tw // 8)).astype(np.float32)
    fog = np.array(Image.fromarray(((noise - noise.min()) / np.ptp(noise) * 255).astype(np.uint8)).resize((tw, th), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40)), dtype=np.float32) / 255
    img = img + (c * 0.35) * fog[..., None] * np.linspace(0.2, 1, th)[:, None, None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    mx, my = int(rng.uniform(0.25, 0.75) * tw), int(rng.uniform(0.12, 0.3) * th)
    for r_, al in ((260, 18), (180, 35), (110, 255)):
        glow = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(glow).ellipse((mx - r_, my - r_, mx + r_, my + r_), fill=al)
        glow = glow.filter(ImageFilter.GaussianBlur(r_ / 3))
        im = Image.composite(Image.new("RGB", (tw, th), tuple(int(v) for v in c)), im, glow)
    d = ImageDraw.Draw(im)
    base = th * 0.78
    for layer in range(3):
        col = tuple(int(v * (0.25 + 0.2 * layer)) for v in a)
        pts = [(0, th)]
        x = 0
        while x <= tw:
            pts.append((x, base + layer * 90 - rng.uniform(0, 260 - layer * 60)))
            x += rng.integers(40, 140)
        pts += [(tw, th)]
        d.polygon(pts, fill=col)
    return im.filter(ImageFilter.GaussianBlur(1.2))


# --------------------------------------------------------------------------------------
# Musique d'ambiance originale + effets
# --------------------------------------------------------------------------------------
def synth_ambience(dur: float, mood: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    roots = {"mystere": 55.0, "suspense": 49.0, "paranormal": 46.25, "destin": 65.41}
    f0 = roots.get(mood, 55.0)
    out = np.zeros(n, dtype=np.float32)
    # accord mineur + quinte, chaque voix avec un léger désaccord et une respiration lente
    for ratio, amp in ((1, 0.32), (1.5, 0.18), (2.0, 0.14), (2.378, 0.10), (3.0, 0.06)):
        for det in (-0.6, 0.6):
            ph = rng.uniform(0, 2 * np.pi)
            lfo = 0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(0.03, 0.08) * t + ph)
            out += amp * lfo * np.sin(2 * np.pi * (f0 * ratio + det) * t + ph).astype(np.float32)
    # vent : bruit filtré passe-bas (moyenne glissante) modulé
    wind = rng.normal(0, 1, n).astype(np.float32)
    k = 400
    wind = np.convolve(wind, np.ones(k) / k, mode="same") * 6
    wind *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t + 1.3)
    out += 0.25 * wind
    # cloche lointaine toutes les ~9 s
    for start in np.arange(4.0, dur - 3, rng.uniform(8, 11)):
        i0 = int(start * SR)
        tt = np.arange(int(3 * SR)) / SR
        f = f0 * 8 * rng.choice([1, 1.189, 1.335, 1.498])
        bell = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 1.6) * 0.09
        out[i0 : i0 + len(bell)] += bell[: max(0, n - i0)].astype(np.float32)
    fade = np.minimum(1, np.minimum(t / 2.0, (dur - t) / 2.5))
    out *= fade.astype(np.float32)
    return out / (np.abs(out).max() + 1e-6)


def whoosh(length: float = 0.7, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(length * SR)
    x = rng.normal(0, 1, n).astype(np.float32)
    x = np.convolve(x, np.ones(30) / 30, mode="same")
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return (x * env / (np.abs(x).max() + 1e-6)).astype(np.float32)


def impact(seed: int = 0) -> np.ndarray:
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    f = 55 * np.exp(-t * 1.5) + 30
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)).astype(np.float32)


# --------------------------------------------------------------------------------------
# Construction de la timeline
# --------------------------------------------------------------------------------------
def build_timeline(story: dict):
    voice = story.get("voix", "fr-FR-HenriNeural")
    rate = story.get("debit", "+6%")
    pitch = story.get("hauteur", "-2Hz")
    segs = [{"texte": story["accroche"], "visuel": story["scenes"][0]["visuel"], "kind": "accroche"}]
    for s in story["scenes"]:
        segs.append({"texte": s["texte"], "visuel": s["visuel"], "kind": "scene", "palette": s.get("palette")})
    segs.append({"texte": story["appel_action"], "visuel": story.get("visuel_fin", story["scenes"][-1]["visuel"]), "kind": "cta"})

    voice_track = []
    words = []
    t = 0.15
    for i, sg in enumerate(segs):
        pcm, ws = tts_segment(sg["texte"], voice, rate, pitch)
        sg["start"] = t
        sg["dur"] = len(pcm) / SR
        for w in ws:
            words.append({"t": t + w["t"], "d": w["d"], "w": w["w"], "seg": i})
        voice_track.append((t, pcm))
        t += sg["dur"] + GAP
        log(f"voix segment {i + 1}/{len(segs)} : {sg['dur']:.1f}s")
    total = t + 0.6
    # chaque segment visuel dure jusqu'au début du suivant
    for i, sg in enumerate(segs):
        sg["vis_start"] = 0.0 if i == 0 else sg["start"] - GAP / 2
        sg["vis_end"] = total if i == len(segs) - 1 else segs[i + 1]["start"] - GAP / 2
    # l'accroche et la première scène partagent la même image -> pas de fondu entre elles
    return segs, words, voice_track, total


def group_words(words: list) -> list:
    """Regroupe les mots en petits blocs (1 à 3 mots) pour des sous-titres dynamiques."""
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        txt = " ".join(x["w"] for x in cur)
        brk = (
            nxt is None
            or len(cur) >= 3
            or len(txt) + 1 + len(nxt["w"]) > 16
            or nxt["t"] - (w["t"] + w["d"]) > 0.22
            or nxt["seg"] != w["seg"]
        )
        if brk:
            chunks.append(cur)
            cur = []
    out = []
    for i, c in enumerate(chunks):
        start = c[0]["t"] - 0.05
        end = c[-1]["t"] + c[-1]["d"] + 0.25
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["t"] - 0.05)
        out.append({"words": c, "start": start, "end": end})
    return out


# --------------------------------------------------------------------------------------
# Rendu image par image
# --------------------------------------------------------------------------------------
def make_vignette() -> np.ndarray:
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
    r = np.sqrt(nx**2 * 0.9 + ny**2 * 0.75)
    v = 1 - np.clip((r - 0.55) / 0.9, 0, 1) ** 1.6 * 0.75
    # assombrit légèrement la zone des sous-titres pour la lisibilité
    band = np.exp(-(((y - 1180) / 330) ** 2)) * 0.22
    return (v * (1 - band))[..., None].astype(np.float32)


def ken_burns(im: Image.Image, p: float, idx: int) -> Image.Image:
    sw, sh = im.size
    rng = random.Random(idx * 7919)
    z0, z1 = (1.0, 1.14) if idx % 2 == 0 else (1.14, 1.0)
    e = 0.5 - 0.5 * math.cos(math.pi * p)  # ease in-out
    z = z0 + (z1 - z0) * e
    ww, wh = sw / z, sh / z
    dx = rng.uniform(-1, 1)
    dy = rng.uniform(-1, 1)
    cx = sw / 2 + dx * (sw - ww) / 2 * (2 * e - 1)
    cy = sh / 2 + dy * (sh - wh) / 2 * (2 * e - 1)
    x0, y0 = cx - ww / 2, cy - wh / 2
    a = ww / W
    return im.transform((W, H), Image.AFFINE, (a, 0, x0, 0, a, y0), resample=Image.BICUBIC)


def draw_text_center(d: ImageDraw.ImageDraw, cx: int, y: int, text: str, f, fill, stroke=8, stroke_fill=(0, 0, 0)):
    bb = d.textbbox((0, 0), text, font=f, stroke_width=stroke)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], y - bb[1]), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return bb[3] - bb[1]


def wrap(text: str, f, maxw: int, d: ImageDraw.ImageDraw) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_overlay(img: Image.Image, t: float, ctx: dict):
    d = ImageDraw.Draw(img, "RGBA")
    total = ctx["total"]
    accent = tuple(ctx["accent"])
    # barre de progression (haut de l'écran)
    d.rectangle((0, 0, W, 14), fill=(0, 0, 0, 120))
    d.rectangle((0, 0, int(W * min(1, t / total)), 14), fill=accent + (255,))
    # mention fiction / IA (toujours visible)
    tag = ctx["tag"]
    f = font("bold", 30)
    tl = d.textlength(tag, font=f)
    d.rounded_rectangle((36, 44, 36 + tl + 36, 98), radius=27, fill=(0, 0, 0, 140))
    d.text((54, 54), tag, font=f, fill=(255, 255, 255, 220))

    segs = ctx["segs"]
    # carton d'accroche : titre + numéro d'épisode pendant le premier segment
    s0 = segs[0]
    if t < s0["vis_end"] + 0.3:
        a = min(1, t / 0.25) * min(1, (s0["vis_end"] + 0.3 - t) / 0.3)
        a = max(0, a)
        if ctx["badge"]:
            fb = font("black", 46)
            bw = d.textlength(ctx["badge"], font=fb)
            d.rounded_rectangle((W / 2 - bw / 2 - 30, 300, W / 2 + bw / 2 + 30, 374), radius=14, fill=accent + (int(235 * a),))
            draw_text_center(d, W // 2, 312, ctx["badge"], fb, (255, 255, 255, int(255 * a)), stroke=0)
        ft = font("black", 80)
        y = 410
        for line in wrap(ctx["titre"].upper(), ft, W - 140, d)[:3]:
            y += draw_text_center(d, W // 2, y, line, ft, (255, 255, 255, int(255 * a)), stroke=7, stroke_fill=(0, 0, 0, int(255 * a))) + 22

    # carton de fin : appel à l'action
    sl = segs[-1]
    if t >= sl["vis_start"]:
        a = min(1, (t - sl["vis_start"]) / 0.35)
        fc = font("black", 62)
        y = 420
        lines = [l for part in ctx["carton_fin"].upper().split("•") for l in wrap(part.strip(), fc, W - 160, d)]
        for line in lines[:3]:
            y += draw_text_center(d, W // 2, y, line, fc, accent + (int(255 * a),), stroke=7, stroke_fill=(0, 0, 0, int(255 * a))) + 18

    # sous-titres mot par mot
    for ch in ctx["chunks"]:
        if ch["start"] <= t < ch["end"]:
            fsz = 96
            pieces = []
            for w in ch["words"]:
                active = w["t"] - 0.03 <= t < w["t"] + w["d"] + 0.08
                pop = 0.0
                if active:
                    k = (t - w["t"]) / 0.12
                    pop = max(0, 1 - abs(k - 0.5) * 2) if 0 <= k <= 1 else 0
                pieces.append((w["w"].upper(), active, pop))
            fw = font("black", fsz)
            sp = d.textlength(" ", font=fw)
            widths = [d.textlength(p[0], font=fw) for p in pieces]
            tot = sum(widths) + sp * (len(pieces) - 1)
            scale = min(1.0, (W - 120) / tot) if tot else 1
            f2 = font("black", int(fsz * scale))
            widths = [d.textlength(p[0], font=f2) for p in pieces]
            sp = d.textlength(" ", font=f2)
            tot = sum(widths) + sp * (len(pieces) - 1)
            appear = min(1, (t - ch["start"]) / 0.08)
            x = (W - tot) / 2
            yb = 1130 + (1 - appear) * 25
            for (txt, active, pop), wd in zip(pieces, widths):
                fz = int(fsz * scale * (1 + 0.12 * pop))
                fa = font("black", fz)
                col = accent if active else (255, 255, 255)
                off = (fz - int(fsz * scale)) / 2
                d.text((x - off * 0.5, yb - off), txt, font=fa, fill=col + (255,), stroke_width=9, stroke_fill=(0, 0, 0, 255))
                x += wd + sp
            break
    return img


def _render_range(args):
    frame_from, frame_to, ctx_path, out_path = args
    ctx = json.loads(Path(ctx_path).read_text())
    imgs = [Image.open(p) for p in ctx["img_paths"]]
    vign = make_vignette()
    rng = np.random.default_rng(frame_from)
    grains = [rng.normal(0, 5, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
    grains = [np.array(Image.fromarray(g).resize((W, H), Image.NEAREST))[..., None] for g in grains]
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", out_path],
        stdin=subprocess.PIPE,
    )
    segs = ctx["segs"]
    for fi in range(frame_from, frame_to):
        t = fi / FPS
        cur = next((i for i, s in enumerate(segs) if s["vis_start"] <= t < s["vis_end"]), len(segs) - 1)
        s = segs[cur]
        p = (t - s["vis_start"]) / max(0.01, s["vis_end"] - s["vis_start"])
        frame = ken_burns(imgs[s["img"]], p, s["img"])
        if cur > 0 and t - s["vis_start"] < XFADE and segs[cur - 1]["img"] != s["img"]:
            pr = segs[cur - 1]
            pp = (t - pr["vis_start"]) / max(0.01, pr["vis_end"] - pr["vis_start"])
            prev = ken_burns(imgs[pr["img"]], min(1.0, pp), pr["img"])
            frame = Image.blend(prev, frame, (t - s["vis_start"]) / XFADE)
        arr = np.asarray(frame, dtype=np.float32)
        # légère respiration lumineuse
        flick = 1 + 0.025 * math.sin(t * 2.1) + 0.015 * math.sin(t * 7.3)
        arr = arr * vign * flick + grains[fi % 6]
        # fondu d'ouverture / de fermeture
        fade = min(1, t / 0.2, (ctx["total"] - t) / 0.5)
        arr *= max(0, fade)
        frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        frame = render_overlay(frame, t, ctx)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg (rendu vidéo) a échoué")
    return out_path


def loudnorm_filter(wav: Path) -> str:
    """Normalisation EBU R128 en deux passes (cible -14 LUFS, crête -1,5 dBTP)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    try:
        m = json.loads(r.stderr[r.stderr.rfind("{"):])
        return (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    except Exception:
        return "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("histoire")
    ap.add_argument("-o", "--sortie")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2)))
    args = ap.parse_args()

    story = json.loads(Path(args.histoire).read_text(encoding="utf-8"))
    sid = story["id"]
    out = Path(args.sortie or ROOT / "videos" / f"{sid}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    seed = int(hashlib.sha1(sid.encode()).hexdigest()[:8], 16)

    segs, words, voice_track, total = build_timeline(story)
    log(f"durée totale : {total:.1f}s, {len(words)} mots")

    tmp = Path(tempfile.mkdtemp(prefix="gen_", dir=CACHE))
    # visuels (un par scène ; l'accroche réutilise la scène 1)
    prompts = []
    for sg in segs:
        if sg["visuel"] not in prompts:
            prompts.append(sg["visuel"])
    img_paths = []
    for i, pr in enumerate(prompts):
        im = fetch_image(pr, seed + i)
        if im is None:
            log(f"visuel {i + 1}: repli procédural")
            im = procedural_image(seed + i, story.get("palette", "nuit"))
        p = tmp / f"img{i}.png"
        im.save(p)
        img_paths.append(str(p))
        log(f"visuel {i + 1}/{len(prompts)} prêt")
    for sg in segs:
        sg["img"] = prompts.index(sg["visuel"])

    accent = story.get("couleur", [255, 210, 0])
    serie = story.get("serie")
    badge = f"PARTIE {story['episode']}" if serie and story.get("episode") else ""
    ctx = {
        "segs": [{k: v for k, v in s.items() if k != "texte"} for s in segs],
        "chunks": group_words(words),
        "total": total,
        "img_paths": img_paths,
        "accent": accent,
        "tag": story.get("mention", "Fiction • Histoire inventée • IA"),
        "titre": story.get("titre_ecran", story["titre"]),
        "badge": badge,
        "carton_fin": story.get("carton_fin", "Partie 2 demain"),
    }
    ctx_path = tmp / "ctx.json"
    ctx_path.write_text(json.dumps(ctx))

    # ---- audio ----
    n = int(total * SR)
    voice = np.zeros(n, dtype=np.float32)
    for t0, pcm in voice_track:
        i0 = int(t0 * SR)
        voice[i0 : i0 + len(pcm)] += pcm[: n - i0]
    music = synth_ambience(total, story.get("ambiance", "mystere"), seed)
    # ducking : la musique baisse quand la voix parle
    env = np.convolve(np.abs(voice), np.ones(2400) / 2400, mode="same")
    duck = 1 - 0.55 * np.clip(env / (env.max() + 1e-6) * 4, 0, 1)
    mix = voice * 0.9 + music * 0.16 * duck
    for i, sg in enumerate(segs[1:], 1):
        if segs[i - 1]["img"] != sg["img"]:
            w_ = whoosh(seed=i) * 0.10
            i0 = max(0, int((sg["vis_start"] - 0.35) * SR))
            mix[i0 : i0 + len(w_)] += w_[: n - i0]
    hit = impact() * 0.35
    mix[: len(hit)] += hit[:n]
    mix = np.clip(mix / (np.abs(mix).max() + 1e-6) * 0.89, -1, 1)
    wav_path = tmp / "mix.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())

    # ---- vidéo (rendu parallèle par tranches) ----
    nframes = int(total * FPS)
    k = max(1, args.workers)
    bounds = [round(nframes * i / k) for i in range(k + 1)]
    jobs = [(bounds[i], bounds[i + 1], str(ctx_path), str(tmp / f"part{i}.mp4")) for i in range(k)]
    log(f"rendu de {nframes} images sur {k} processus…")
    with ProcessPoolExecutor(k) as ex:
        parts = list(ex.map(_render_range, jobs))
    lst = tmp / "parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(wav_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "8M", "-bufsize", "16M",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(FPS),
        "-af", loudnorm_filter(wav_path), "-c:a", "aac", "-b:a", "192k", "-ac", "2",
        "-shortest", "-movflags", "+faststart", str(out),
    ])
    # couverture (image à 1 s : titre + visuel)
    run(["ffmpeg", "-y", "-v", "error", "-ss", "1.2", "-i", str(out), "-frames:v", "1", str(out.with_suffix(".jpg"))])
    # transcription (pour la vérification orthographique)
    (out.with_suffix(".mots.json")).write_text(json.dumps(words, ensure_ascii=False))
    shutil.rmtree(tmp, ignore_errors=True)
    log(f"OK -> {out} ({out.stat().st_size / 1e6:.1f} Mo, {total:.1f}s)")


if __name__ == "__main__":
    sys.exit(main())
