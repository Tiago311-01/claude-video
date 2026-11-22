#!/usr/bin/env python3
"""Contrôle qualité d'une vidéo AVANT publication.

Usage : python3 outils/verifier.py histoires/<id>.json [videos/<id>.mp4]

Vérifie :
  1. format : 1080x1920, H.264, 30 i/s, durée entre 60 et 120 s, piste audio présente
  2. son    : volume intégré proche de -14 LUFS, pas de silence anormal, pas de saturation
  3. texte  : orthographe/grammaire de tous les textes (accroche, scènes, appel à l'action, légende)
              via l'API publique gratuite LanguageTool
  4. image  : pas d'images noires prolongées ; produit une planche contact (videos/<id>.planche.jpg)
              que l'agent DOIT regarder pour vérifier la lisibilité des sous-titres.
  5. règles : mention fiction présente dans la légende, pas de « histoire vraie », hashtags <= 8

Code retour 0 = publiable, 1 = à corriger. Le rapport est écrit dans videos/<id>.verif.json
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CA = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"

# Règles LanguageTool non pertinentes pour des textes oraux / stylisés
IGNORED_RULES = {
    "WHITESPACE_RULE", "FRENCH_WHITESPACE", "UPPERCASE_SENTENCE_START", "DOUBLE_PUNCTUATION",
    "APOS_TYP", "FR_SPLIT_WORDS_HYPHEN", "TIRET", "POINTS_SUSPENSION", "ESPACE_INSECABLE",
    "EMOJI", "DASH_RULE", "COMMA_PARENTHESIS_WHITESPACE",
    # faux positif récurrent sur « Puis il… », « Alors je… » (3 fois sur nos textes, jamais une vraie faute)
    "VIRGULE_DEBUT_DE_PHRASE",
}


def ffprobe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)


def loudness(path: Path) -> dict:
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    get = lambda k: float(re.search(k + r":\s+(-?[\d.]+|-inf)", tail).group(1).replace("-inf", "-99"))
    return {"I": get("I"), "LRA": get("LRA"), "peak": get("Peak")}


def silences(path: Path) -> list:
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=n=-45dB:d=2.0", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    return re.findall(r"silence_duration: ([\d.]+)", r.stderr)


def black_frames(path: Path) -> list:
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-vf", "blackdetect=d=1.0:pix_th=0.06", "-an", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    return re.findall(r"black_duration:([\d.]+)", r.stderr)


def contact_sheet(path: Path, dur: float) -> Path:
    out = path.with_suffix(".planche.jpg")
    times = [0.8 + i * (dur - 1.6) / 11 for i in range(12)]
    sel = "+".join(f"between(t\\,{t:.2f}\\,{t + 0.034:.2f})" for t in times)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", f"select='{sel}',scale=270:480,tile=6x2",
         "-frames:v", "1", "-fps_mode", "vfr", str(out)],
        check=True,
    )
    return out


def spellcheck(texts: list[str], ignore: dict | None = None) -> list:
    ignore = ignore or {}
    import requests

    issues = []
    for txt in texts:
        try:
            r = requests.post(
                "https://api.languagetool.org/v2/check",
                data={"text": txt, "language": "fr", "level": "default"},
                timeout=30, verify=CA if os.path.exists(CA) else True,
            )
            r.raise_for_status()
        except Exception as e:  # le service gratuit peut être indisponible : on le signale sans bloquer
            issues.append({"warning": f"LanguageTool indisponible : {e}"})
            return issues
        for m in r.json().get("matches", []):
            rid = m["rule"]["id"]
            if rid in IGNORED_RULES or rid in ignore or m["rule"].get("issueType") == "typographical":
                continue
            frag = txt[m["offset"]: m["offset"] + m["length"]]
            issues.append({
                "texte": frag, "regle": rid, "message": m["message"],
                "suggestions": [x["value"] for x in m.get("replacements", [])[:3]],
                "contexte": m["context"]["text"],
            })
    return issues


def main():
    story_path = Path(sys.argv[1])
    story = json.loads(story_path.read_text(encoding="utf-8"))
    video = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "videos" / f"{story['id']}.mp4"
    errors, warnings = [], []

    if not video.exists():
        print(json.dumps({"ok": False, "erreurs": ["vidéo introuvable"]}, ensure_ascii=False))
        return 1

    info = ffprobe(video)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / 1e6
    if not v or (v["width"], v["height"]) != (1080, 1920):
        errors.append(f"résolution incorrecte : {v and (v['width'], v['height'])}")
    if v and v["codec_name"] != "h264":
        errors.append(f"codec vidéo {v['codec_name']} (attendu h264)")
    if not a:
        errors.append("aucune piste audio")
    pov = story.get("format") == "pov"
    lo, hi = (6, 20) if pov else (60, 120)
    if not lo <= dur <= hi:
        errors.append(f"durée {dur:.1f}s hors de [{lo}, {hi}]")
    if size_mb > 250:
        errors.append(f"fichier trop lourd ({size_mb:.0f} Mo)")

    loud = loudness(video) if a else {}
    if loud and not -16.5 <= loud["I"] <= -11.5:
        errors.append(f"volume intégré {loud['I']} LUFS (attendu ~ -14)")
    if loud and loud["peak"] > 0.0:
        warnings.append(f"crête {loud['peak']} dBFS")
    sil = [float(x) for x in silences(video)] if a else []
    if any(s > 3 for s in sil):
        errors.append(f"silence anormal : {sil}")
    blk = [float(x) for x in black_frames(video)]
    if any(b > 1.5 for b in blk):
        errors.append(f"écran noir prolongé : {blk}")

    if pov:
        texts = [story["texte_pov"], story.get("texte_revelation", ""), story["legende"]]
    else:
        texts = [story["accroche"], *[s["texte"] for s in story["scenes"]], story["appel_action"], story["legende"]]
    # faux positifs justifiés par l'agent dans le JSON : {"REGLE": "justification"}
    sp = spellcheck(texts, story.get("verif_faux_positifs"))
    for it in sp:
        (warnings if "warning" in it else errors).append(it)

    leg = story["legende"].lower()
    if "fiction" not in leg and "inventée" not in leg:
        errors.append("la légende doit indiquer que c'est une fiction")
    joined = " ".join(texts).lower()
    if re.search(r"histoire vraie|fait réel|true story|basé sur des faits", joined):
        errors.append("une fiction ne doit jamais être présentée comme vraie")
    if len(story.get("hashtags", [])) > 8:
        warnings.append("plus de 8 hashtags")

    sheet = contact_sheet(video, dur)
    report = {
        "ok": not errors,
        "video": str(video.relative_to(ROOT)),
        "duree_s": round(dur, 1),
        "taille_mo": round(size_mb, 1),
        "volume": loud,
        "erreurs": errors,
        "avertissements": warnings,
        "planche_contact": str(sheet.relative_to(ROOT)),
        "a_faire_par_agent": "Ouvrir la planche contact et confirmer : sous-titres lisibles, visuels cohérents, aucun texte parasite.",
    }
    video.with_suffix(".verif.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
