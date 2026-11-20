#!/usr/bin/env python3
"""Format court « POV » (8-15 s) : une image IA animée + texte « Pov : … » façon TikTok, sans voix off.

Usage : python3 generateur/pov.py histoires/pov_<id>.json

JSON :
  id, texte_pov (1ʳᵉ phrase, affichée dès le début), texte_revelation (2ᵉ phrase, à la révélation),
  visuel (description EN ANGLAIS : sujet au premier plan + élément effrayant à l'arrière-plan),
  graine (optionnel), duree (s, défaut 10), legende, hashtags.

Mise en scène « révélation » (fonctionne quelle que soit la position de l'élément effrayant) :
  0 → 3 s   : seule la zone du visage est éclairée (lumière du téléphone), le reste est noir
  3 → 6 s   : la lampe clignote : à chaque flash on aperçoit toute la pièce (et ce qu'il y a derrière)
  6 → 8,3 s : la pièce reste éclairée, lente poussée de caméra, 2ᵉ texte
  8,3 s     : sursaut (secousse, décalage RGB, coup sonore) puis noir
Son : drone + battements de cœur qui accélèrent + coup final — synthétisés ici, 100 % originaux.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer as g  # noqa: E402  (réutilise images, polices, sons, normalisation)

W, H, FPS, SR = g.W, g.H, g.FPS, g.SR


def caption(img: Image.Image, lines: list[tuple[str, float]], y0: int = 1330):
    """Texte blanc façon TikTok : police grasse, légère ombre, centré. lines = [(texte, opacité)]."""
    d = ImageDraw.Draw(img, "RGBA")
    f = g.font("bold", 64)
    y = y0
    for text, a in lines:
        if a <= 0:
            y += 0
            continue
        for line in g.wrap(text, f, W - 180, d):
            bb = d.textbbox((0, 0), line, font=f)
            x = (W - (bb[2] - bb[0])) / 2 - bb[0]
            sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).text((x + 2, y + 3), line, font=f, fill=(0, 0, 0, int(200 * a)))
            img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
            d = ImageDraw.Draw(img, "RGBA")
            d.text((x, y), line, font=f, fill=(255, 255, 255, int(255 * a)))
            y += (bb[3] - bb[1]) + 22
        y += 14
    return img


def heartbeat(n: int, t0: float, t1: float, bpm0: float, bpm1: float) -> np.ndarray:
    out = np.zeros(n, dtype=np.float32)
    t = t0
    while t < t1:
        k = (t - t0) / max(0.01, t1 - t0)
        bpm = bpm0 + (bpm1 - bpm0) * k
        for off, amp in ((0.0, 1.0), (0.18, 0.7)):
            i0 = int((t + off) * SR)
            tt = np.arange(int(0.25 * SR)) / SR
            thump = np.sin(2 * np.pi * 48 * tt) * np.exp(-tt * 22) * amp
            out[i0:i0 + len(thump)] += thump[: max(0, n - i0)]
        t += 60 / bpm
    return out


def main():
    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    dur = float(story.get("duree", 10))
    out = g.ROOT / "videos" / f"{story['id']}.mp4"
    out.parent.mkdir(exist_ok=True)
    seed = int(story.get("graine", 7))
    im = g.fetch_image(story["visuel"], seed)
    if im is None:
        raise SystemExit("image indisponible (service saturé) : relancer plus tard")
    src = im  # 1350x2400 (SRC_SCALE)
    sw, sh = src.size

    # masque « lumière du téléphone » : ovale doux autour du visage (haut-centre de l'image)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    fx, fy = float(story.get("visage_x", 0.5)) * W, float(story.get("visage_y", 0.38)) * H
    r = np.sqrt(((xx - fx) / 330) ** 2 + ((yy - fy) / 420) ** 2)
    face_mask = np.clip(1.25 - r, 0, 1)[..., None] ** 1.3

    # flashs de la lampe entre 3 et 6 s (instants fixes => rendu déterministe)
    flashes = [(3.05, 0.10), (3.45, 0.06), (4.30, 0.16), (4.75, 0.07), (5.40, 0.22), (5.75, 0.10)]
    t_full, t_hit = 6.0, dur - 1.7

    tmp = Path(tempfile.mkdtemp(prefix="pov_", dir=g.CACHE))
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", str(tmp / "v.mp4")],
        stdin=subprocess.PIPE,
    )
    rng = np.random.default_rng(seed)
    grain = [np.array(Image.fromarray(rng.normal(0, 6, (H // 2, W // 2)).astype(np.float32)).resize((W, H)))[..., None] for _ in range(4)]
    n = int(dur * FPS)
    for fi in range(n):
        t = fi / FPS
        # caméra de téléphone tenue à la main : léger tremblement + poussée lente
        z = 1.0 + 0.06 * min(1, t / dur) + (0.05 * max(0, t - t_full) / 3 if t > t_full else 0)
        jx = 6 * math.sin(t * 1.7) + 3 * math.sin(t * 4.1)
        jy = 5 * math.sin(t * 1.3 + 1) + 2 * math.sin(t * 5.3)
        if t_hit <= t < t_hit + 0.5:
            k = 1 - (t - t_hit) / 0.5
            jx += rng.uniform(-40, 40) * k
            jy += rng.uniform(-40, 40) * k
        ww, wh = sw / z, sh / z
        x0 = (sw - ww) / 2 + jx
        y0 = (sh - wh) / 2 + jy
        frame = src.transform((W, H), Image.AFFINE, (ww / W, 0, x0, 0, ww / W, y0), resample=Image.BICUBIC)
        arr = np.asarray(frame, dtype=np.float32)

        # éclairage
        lit = 0.0
        if t >= t_full:
            lit = min(1.0, (t - t_full) / 0.4) * 0.85
        for ft, fd in flashes:
            if ft <= t < ft + fd:
                lit = max(lit, 0.95)
        phone = 0.9 + 0.08 * math.sin(t * 9) * (rng.random() > 0.5)
        light = face_mask * phone * (1 - lit) + lit
        arr = arr * (0.06 + 0.94 * light)
        # teinte froide légère + grain
        arr[..., 2] *= 1.05
        arr = arr + grain[fi % 4]
        # sursaut : décalage RGB
        if t_hit <= t < t_hit + 0.35:
            s = int(18 * (1 - (t - t_hit) / 0.35)) + 2
            arr[..., 0] = np.roll(arr[..., 0], s, axis=1)
            arr[..., 2] = np.roll(arr[..., 2], -s, axis=1)
            arr *= 1.25
        # noir final
        if t > dur - 0.9:
            arr *= max(0, (dur - t) / 0.9) ** 2
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

        # textes
        a1 = min(1, t / 0.3) * (1 if t < dur - 0.9 else max(0, (dur - t) / 0.9))
        a2 = (min(1, (t - t_full - 0.3) / 0.3) if t > t_full + 0.3 else 0) * (1 if t < dur - 0.9 else max(0, (dur - t) / 0.9))
        img = caption(img, [(story["texte_pov"], a1), (story.get("texte_revelation", ""), a2)])
        # mention fiction / IA discrète
        d = ImageDraw.Draw(img, "RGBA")
        d.text((40, 52), story.get("mention", "Fiction • IA"), font=g.font("bold", 26), fill=(255, 255, 255, 120))
        ff.stdin.write(img.convert("RGB").tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg (vidéo POV) a échoué")

    # ---- son ----
    N = int(dur * SR)
    tt = np.arange(N) / SR
    drone = g.synth_ambience(dur, "paranormal", seed) * 0.35
    hb = heartbeat(N, 0.6, t_hit, 62, 128) * 0.55
    room = np.convolve(rng.normal(0, 1, N).astype(np.float32), np.ones(200) / 200, mode="same") * 2.0 * 0.15
    flick = np.zeros(N, dtype=np.float32)
    for ft, fd in flashes:  # petit grésillement électrique à chaque flash
        i0 = int(ft * SR)
        m = int(fd * SR)
        flick[i0:i0 + m] += (rng.normal(0, 1, m) * np.sin(2 * np.pi * 100 * np.arange(m) / SR)).astype(np.float32) * 0.25
    hit = np.zeros(N, dtype=np.float32)
    i0 = int(t_hit * SR)
    k = g.impact() * 1.0
    hit[i0:i0 + len(k)] += k[: N - i0]
    nb = rng.normal(0, 1, int(0.4 * SR)).astype(np.float32) * np.exp(-np.arange(int(0.4 * SR)) / SR * 9) * 0.6
    hit[i0:i0 + len(nb)] += nb[: N - i0]
    mix = drone + hb + room + flick + hit
    mix *= np.minimum(1, np.minimum(tt / 0.3, (dur - tt) / 0.4)).astype(np.float32)
    mix = np.clip(mix / (np.abs(mix).max() + 1e-6) * 0.9, -1, 1)
    with wave.open(str(tmp / "a.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())

    g.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp / "v.mp4"), "-i", str(tmp / "a.wav"), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-af", g.loudnorm_filter(tmp / "a.wav"), "-c:a", "aac", "-b:a", "192k", "-ac", "2",
           "-shortest", "-movflags", "+faststart", str(out)])
    g.run(["ffmpeg", "-y", "-v", "error", "-ss", "4.35", "-i", str(out), "-frames:v", "1", str(out.with_suffix(".jpg"))])
    print(f"OK -> {out}")


if __name__ == "__main__":
    main()
