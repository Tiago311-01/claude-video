#!/usr/bin/env python3
"""Publication / programmation sur TikTok via l'API Blotato (outil tiers à accès TikTok validé).

Usage :
    python3 outils/publier.py comptes                       # vérifie la connexion, liste les comptes TikTok
    python3 outils/publier.py programmer histoires/<id>.json  # envoie la vidéo et la programme au prochain créneau
    python3 outils/publier.py programmer histoires/<id>.json --maintenant   # publication immédiate
    python3 outils/publier.py statut                        # met à jour le statut des publications en attente

Clé API (jamais commitée) — par ordre de priorité :
  1. variable d'environnement BLOTATO_API_KEY
  2. fichier ~/.config/tiktok-auto/.env  (ligne BLOTATO_API_KEY=...)
  3. dans le cloud Claude : « secret réseau » de l'environnement pour backend.blotato.com
     (en-tête blotato-api-key) ; le proxy injecte la vraie valeur, on envoie un espace réservé.

Toutes les vidéos sont publiées avec isAiGenerated=true (étiquette « contenu généré par IA »).
Codes retour : 0 = OK, 2 = bloqué (connexion à faire par l'utilisateur), 1 = autre erreur.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://backend.blotato.com/v2"
CA = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
VERIFY = CA if os.path.exists(CA) else True
CONFIG = ROOT / "config.json"
PUBS = ROOT / "stats" / "publications.json"


def load_key() -> str:
    k = os.environ.get("BLOTATO_API_KEY")
    if k:
        return k.strip()
    envf = Path.home() / ".config" / "tiktok-auto" / ".env"
    if envf.exists():
        for line in envf.read_text().splitlines():
            if line.startswith("BLOTATO_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return "proxy-injecte"  # remplacé par le proxy si un secret réseau est configuré


def cfg() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def api(method: str, path: str, **kw):
    h = {"blotato-api-key": load_key(), "Content-Type": "application/json"}
    for attempt in range(4):
        r = requests.request(method, BASE + path, headers=h, timeout=60, verify=VERIFY, **kw)
        if r.status_code == 429:
            time.sleep(15 * (attempt + 1))
            continue
        return r
    return r


class Bloque(Exception):
    pass


def check(r):
    if r.status_code in (401, 403):
        raise Bloque(f"Blotato refuse la clé API (HTTP {r.status_code}) : {r.text[:200]}")
    if r.status_code >= 400:
        raise RuntimeError(f"Blotato HTTP {r.status_code} : {r.text[:400]}")
    return r.json()


def tiktok_account() -> str:
    c = cfg()
    if c.get("blotato_account_id"):
        return str(c["blotato_account_id"])
    items = check(api("GET", "/users/me/accounts", params={"platform": "tiktok"})).get("items", [])
    if not items:
        raise Bloque("Aucun compte TikTok connecté dans Blotato.")
    want = (c.get("tiktok_username") or "").lstrip("@").lower()
    acc = next((a for a in items if want and want in (a.get("username", "").lower(), a.get("fullname", "").lower())), items[0])
    c["blotato_account_id"] = acc["id"]
    CONFIG.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(acc["id"])


def load_pubs() -> list:
    return json.loads(PUBS.read_text(encoding="utf-8")) if PUBS.exists() else []


def save_pubs(p: list):
    PUBS.parent.mkdir(exist_ok=True)
    PUBS.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def next_slot(pubs: list, story: dict | None = None) -> datetime:
    """Prochain créneau libre. Si l'histoire fixe un « creneau » (ex. "18:45"), on ne prend que
    celui-là. Une série ne publie jamais deux épisodes le même jour (promesse « la suite demain »)."""
    c = cfg()
    tz = ZoneInfo(c.get("fuseau", "Europe/Paris"))
    now = datetime.now(tz)
    story = story or {}
    serie_days = {p["programme_le"][:10] for p in pubs if story.get("serie") and p.get("serie") == story.get("serie") and p.get("programme_le")}
    last_serie_day = max(serie_days) if serie_days else ""
    hours = [story["creneau"]] if story.get("creneau") else c.get("creneaux", ["12:30", "18:45", "21:15"])
    taken = {p["programme_le"] for p in pubs if p.get("programme_le")}
    per_day: dict = {}
    for p in pubs:
        if p.get("programme_le"):
            per_day[p["programme_le"][:10]] = per_day.get(p["programme_le"][:10], 0) + 1
    for day in range(0, 7):
        d = (now + timedelta(days=day)).date()
        if per_day.get(d.isoformat(), 0) >= c.get("max_par_jour", 3):
            continue
        if last_serie_day and d.isoformat() <= last_serie_day:
            continue
        for hm in hours:
            hh, mm = map(int, hm.split(":"))
            slot = datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz)
            if slot < now + timedelta(minutes=40) or slot.isoformat() in taken:
                continue
            return slot
    raise RuntimeError("aucun créneau libre sur 7 jours")


def upload(video: Path) -> str:
    j = check(api("POST", "/media/uploads", json={"filename": video.name}))
    with open(video, "rb") as f:
        r = requests.put(j["presignedUrl"], data=f, headers={"Content-Type": "video/mp4"}, timeout=600, verify=VERIFY)
    if r.status_code >= 400:
        raise RuntimeError(f"échec de l'envoi du fichier (HTTP {r.status_code}) : {r.text[:200]}")
    return j["publicUrl"]


def programmer(story_path: Path, maintenant: bool = False):
    story = json.loads(story_path.read_text(encoding="utf-8"))
    video = ROOT / "videos" / f"{story['id']}.mp4"
    verif = video.with_suffix(".verif.json")
    if not verif.exists() or not json.loads(verif.read_text())["ok"]:
        raise RuntimeError("la vidéo n'a pas passé outils/verifier.py : publication refusée")
    pubs = load_pubs()
    if any(p["id"] == story["id"] and p.get("statut") not in ("failed", "erreur") for p in pubs):
        print("déjà programmée")
        return
    acc = tiktok_account()
    url = upload(video)
    tz = ZoneInfo(cfg().get("fuseau", "Europe/Paris"))
    slot = datetime.now(tz).replace(microsecond=0) if maintenant else next_slot(pubs, story)
    text = story["legende"].strip() + "\n\n" + " ".join(story.get("hashtags", []))
    body = {
        "post": {
            "accountId": acc,
            "content": {"text": text[:2200], "mediaUrls": [url], "platform": "tiktok"},
            "target": {
                "targetType": "tiktok",
                "privacyLevel": "PUBLIC_TO_EVERYONE",
                "disabledComments": False,
                "disabledDuet": False,
                "disabledStitch": False,
                "isBrandedContent": False,
                "isYourBrand": False,
                "isAiGenerated": True,
                "videoCoverTimestamp": 1200,
            },
        },
    }
    if not maintenant:
        body["scheduledTime"] = slot.isoformat()
    res = check(api("POST", "/posts", json=body))
    pubs.append({
        "id": story["id"], "serie": story.get("serie"), "episode": story.get("episode"),
        "programme_le": slot.isoformat(), "postSubmissionId": res.get("postSubmissionId"),
        "statut": "in-progress" if maintenant else "scheduled", "cree_le": datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds"),
    })
    save_pubs(pubs)
    print(json.dumps({"ok": True, "programme_le": slot.isoformat(), "postSubmissionId": res.get("postSubmissionId")}, ensure_ascii=False))


def reprogrammer(story_path: Path):
    """Remplace une vidéo déjà programmée (non publiée) par sa nouvelle version, au même créneau."""
    story = json.loads(story_path.read_text(encoding="utf-8"))
    pubs = load_pubs()
    entry = next((p for p in pubs if p["id"] == story["id"] and p.get("statut") == "scheduled"), None)
    if not entry:
        raise RuntimeError("aucune programmation en attente pour cette histoire")
    when = datetime.fromisoformat(entry["programme_le"])
    items = check(api("GET", "/schedules")).get("items", [])
    target = [it for it in items if datetime.fromisoformat(it["scheduledAt"].replace("Z", "+00:00")) == when]
    if len(target) != 1:
        raise RuntimeError(f"programmation introuvable ou ambiguë ({len(target)} trouvée(s))")
    video = ROOT / "videos" / f"{story['id']}.mp4"
    verif = video.with_suffix(".verif.json")
    if not verif.exists() or not json.loads(verif.read_text())["ok"]:
        raise RuntimeError("la nouvelle version n'a pas passé outils/verifier.py")
    url = upload(video)  # envoi d'abord : si ça échoue, l'ancienne programmation reste en place
    r = requests.delete(BASE + f"/schedules/{target[0]['id']}", headers={"blotato-api-key": load_key()}, timeout=60, verify=VERIFY)
    if r.status_code >= 400:
        raise RuntimeError(f"suppression de l'ancienne programmation impossible : HTTP {r.status_code}")
    draft = target[0]["draft"]
    draft["content"]["mediaUrls"] = [url]
    res = check(api("POST", "/posts", json={"post": draft, "scheduledTime": when.isoformat()}))
    entry["postSubmissionId"] = res.get("postSubmissionId")
    entry["note"] = (entry.get("note", "") + " ; remplacée par une nouvelle version (mouvement 3D)").strip(" ;")
    save_pubs(pubs)
    print(json.dumps({"ok": True, "programme_le": when.isoformat(), "postSubmissionId": res.get("postSubmissionId")}, ensure_ascii=False))


def statut():
    pubs = load_pubs()
    for p in pubs:
        if p.get("postSubmissionId") and p.get("statut") in ("scheduled", "in-progress"):
            j = check(api("GET", f"/posts/{p['postSubmissionId']}"))
            p["statut"] = j.get("status", p["statut"])
            if j.get("publicUrl") and "/video/" in j["publicUrl"]:
                p["url"] = j["publicUrl"]
            elif j.get("status") == "published" and "/video/" not in p.get("url", ""):
                p["url"] = ""  # Blotato n'a donné que le profil : stats.py retrouvera la vidéo par sa légende
            if j.get("errorMessage"):
                p["erreur"] = j["errorMessage"]
    save_pubs(pubs)
    print(json.dumps(pubs, ensure_ascii=False, indent=2))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "comptes"
    try:
        if cmd == "comptes":
            print(json.dumps(check(api("GET", "/users/me/accounts", params={"platform": "tiktok"})), ensure_ascii=False, indent=2))
        elif cmd == "programmer":
            programmer(Path(sys.argv[2]), maintenant="--maintenant" in sys.argv)
        elif cmd == "reprogrammer":
            reprogrammer(Path(sys.argv[2]))
        elif cmd == "statut":
            statut()
        else:
            print(__doc__)
            return 1
    except Bloque as e:
        print(f"BLOQUE: {e}")
        return 2
    except requests.RequestException as e:
        print(f"BLOQUE: réseau vers Blotato impossible : {e}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
