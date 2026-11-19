#!/usr/bin/env python3
"""Relevé des statistiques publiques du compte (lecture seule, 1 chargement de page par cycle).

Usage : python3 outils/stats.py
Lit tiktok_username dans config.json, ouvre la page publique du profil dans Chromium headless
et extrait : abonnés, j'aime totaux, et pour chaque vidéo récente vues / j'aime / commentaires /
partages / enregistrements. Ajoute un relevé horodaté à stats/historique.json.

Limites connues :
  - la RÉTENTION (temps de visionnage moyen, % de vidéos vues en entier) n'est accessible que dans
    TikTok Studio ou via l'API officielle avec autorisation du propriétaire : non disponible ici.
    On utilise des indicateurs de substitution : partages/vue, commentaires/vue, abonnés gagnés/cycle.
  - si TikTok affiche une vérification anti-robot, on NE la contourne PAS : on note « bloqué ».
Codes retour : 0 = OK, 2 = bloqué / non configuré.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HIST = ROOT / "stats" / "historique.json"

JS = r"""
const { chromium } = require('playwright');
(async () => {
  const user = process.argv[2];
  const b = await chromium.launch();
  const p = await b.newPage({ locale: 'fr-FR', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36' });
  const vids = [];
  p.on('response', async r => {
    if (r.url().includes('/api/post/item_list')) { try { const j = await r.json(); for (const it of (j.itemList || [])) vids.push(it); } catch (e) {} }
  });
  let out = { ok: false };
  try {
    await p.goto('https://www.tiktok.com/@' + user, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForTimeout(8000);
    const raw = await p.evaluate(() => { const s = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__'); return s ? s.textContent : null; });
    let stats = null;
    if (raw) { const j = JSON.parse(raw); const ui = j.__DEFAULT_SCOPE__ && j.__DEFAULT_SCOPE__['webapp.user-detail']; stats = ui && ui.userInfo && ui.userInfo.stats; }
    const captcha = await p.$('#captcha-verify-container, .captcha_verify_container, [class*="captcha"]');
    out = { ok: !!stats, captcha: !!captcha, profil: stats,
            videos: vids.map(v => ({ id: v.id, desc: (v.desc || '').slice(0, 80), cree: v.createTime, duree: v.video && v.video.duration, ...(v.stats || {}) })) };
  } catch (e) { out = { ok: false, erreur: String(e) }; }
  // vues par vidéo : page publique de chaque vidéo publiée par l'automatisation
  out.par_video = [];
  for (const url of (process.argv[3] || '').split(',').filter(Boolean)) {
    try {
      await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForTimeout(4000);
      const raw = await p.evaluate(() => { const s = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__'); return s ? s.textContent : null; });
      const j = raw && JSON.parse(raw);
      const it = j && j.__DEFAULT_SCOPE__ && j.__DEFAULT_SCOPE__['webapp.video-detail'] && j.__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo && j.__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo.itemStruct;
      out.par_video.push({ url, ok: !!it, ...(it ? { cree: it.createTime, ...(it.statsV2 || it.stats || {}) } : {}) });
    } catch (e) { out.par_video.push({ url, ok: false, erreur: String(e) }); }
  }
  console.log(JSON.stringify(out));
  await b.close();
})();
"""


def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    user = (cfg.get("tiktok_username") or "").lstrip("@")
    if not user:
        print("BLOQUE: tiktok_username absent de config.json")
        return 2
    js = ROOT / "cache" / "stats.js"
    js.parent.mkdir(exist_ok=True)
    js.write_text(JS)
    pubs_f = ROOT / "stats" / "publications.json"
    pubs = json.loads(pubs_f.read_text(encoding="utf-8")) if pubs_f.exists() else []
    urls = [x["url"] for x in pubs if x.get("statut") == "published" and x.get("url")][-10:]
    r = subprocess.run(["node", str(js), user, ",".join(urls)], capture_output=True, text=True, timeout=400)
    line = next((l for l in r.stdout.splitlines()[::-1] if l.startswith("{")), "{}")
    data = json.loads(line)
    data["releve_le"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else []
    hist.append(data)
    HIST.parent.mkdir(exist_ok=True)
    HIST.write_text(json.dumps(hist[-120:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not data.get("ok"):
        print("BLOQUE: profil illisible" + (" (vérification anti-robot affichée, non contournée)" if data.get("captcha") else "") + f" {data.get('erreur', '')}")
        return 2
    prof = data["profil"]
    print(f"abonnés={prof.get('followerCount')} j'aime={prof.get('heartCount')} vidéos={prof.get('videoCount')}")
    for v in data.get("par_video", []):
        if v.get("ok"):
            vues = int(v.get("playCount") or 0)
            part = int(v.get("shareCount") or 0)
            print(f"  {v['url'].rsplit('/', 1)[-1]} vues={vues} j'aime={v.get('diggCount')} com={v.get('commentCount')} "
                  f"partages={part} enregistrements={v.get('collectCount')}" + (f" taux_partage={part / vues:.2%}" if vues else ""))
        else:
            print(f"  {v['url']} illisible")
    for v in data["videos"][:10]:
        vues = v.get("playCount") or 0
        part = v.get("shareCount") or 0
        print(f"  {v['id']} vues={vues} j'aime={v.get('diggCount')} com={v.get('commentCount')} partages={part} "
              f"taux_partage={part / vues:.3%}" if vues else f"  {v['id']} vues=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
