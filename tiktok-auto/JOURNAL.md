# JOURNAL

## ⚠️ ACTIONS REQUISES (à faire une seule fois par toi)

La production tourne seule. **La publication et les statistiques sont bloquées** tant que ces
deux connexions ne sont pas faites (je n'ai le droit ni de saisir un mot de passe ni de créer un
compte à ta place). Tout le reste continue en attendant ; les vidéos restent prêtes à partir.

1. **Relier TikTok à Blotato** (outil de programmation avec accès TikTok validé, offre payante
   requise pour l'API : Starter suffit).
   - Va sur https://my.blotato.com → crée ton compte → *Settings* → *Accounts* → *Connect TikTok*
     → connecte-toi à TikTok et autorise Blotato.
   - *Settings* → *API* → *Generate API key* → copie la clé (entière, y compris les `=` de fin).
2. **Donner la clé à l'automatisation** (jamais dans le chat, jamais dans un fichier du dépôt) :
   - Sur claude.ai/code : menu de l'environnement cloud dans la barre de titre de la session →
     *Edit* → **Network secrets** (ou « API credentials ») → *Add* :
     hôte `backend.blotato.com`, en-tête `blotato-api-key`, valeur = ta clé.
     (Il s'agit de ton environnement « Default » : la clé y sera disponible pour tes sessions cloud.)
   - Si tu fais tourner l'automatisation sur ton propre ordinateur à la place : crée le fichier
     `~/.config/tiktok-auto/.env` contenant `BLOTATO_API_KEY=ta_clé` (droits 600).
3. **Indiquer ton nom d'utilisateur TikTok** (pour lire les statistiques publiques) : remplace
   `null` par `"@ton_pseudo"` dans `tiktok-auto/config.json` (branche
   `claude/tiktok-autonomous-growth-8p5psf` du dépôt claude-video), ou écris-le dans une
   nouvelle session ; je le reporterai.

Rien d'autre n'est nécessaire. Dès que la clé est là, le cycle suivant programme automatiquement
les vidéos en attente (avec l'étiquette « contenu généré par IA »).

### Blocages en cours
- 2026-11-18 — Blotato : HTTP 401 (aucune clé configurée) → publication impossible. Voir étapes 1-2.
- 2026-11-18 — Statistiques : pseudo TikTok inconnu → relevé impossible. Voir étape 3.
- 2026-11-18 — TikTok Creative Center : page vide en navigateur automatisé (protection anti-robot).
  Non contourné ; tendances relevées par recherche web à la place.

---

## Choix prudents pris sans te consulter
- **Exécution toutes les 6 h** : ton ordinateur n'est pas relié à cette session ; j'ai donc programmé
  une tâche planifiée **cloud** (claude.ai) qui me relance toutes les 6 h avec « Lis CLAUDE.md et
  fais un cycle », même ordinateur éteint. Des installateurs locaux sont aussi fournis
  (`outils/planifier_windows.ps1`, `outils/planifier_cron.sh`) : **ne pas les activer en plus**,
  sinon les cycles seraient doublés.
- **Sons** : l'API de publication ne peut pas attacher un son de la bibliothèque commerciale TikTok.
  Aucun son tiers n'est utilisé : seulement une musique d'ambiance originale synthétisée. Zéro risque
  de droits d'auteur.
- **Rétention** : non accessible hors TikTok Studio ; remplacée par vues, partages/vue,
  commentaires/vue et abonnés gagnés.
- **Rythme** : 2 vidéos/jour la première semaine (pas 4) — la qualité prime, un épisode par série
  et par jour pour que « Partie 2 demain » soit toujours vrai.
- **Stockage** : les MP4 ne sont pas commités (≈ 50-80 Mo chacun) ; ils sont régénérés à
  l'identique depuis leur JSON si besoin.

---

## Entrées

### 2026-11-18 ~20 h 30 (Paris) — Mise en place + cycle 1
**Mise en place**
- Projet `tiktok-auto/` : générateur (`generateur/generer.py`), vérificateur (`outils/verifier.py`),
  publication Blotato (`outils/publier.py`), statistiques (`outils/stats.py`), CLAUDE.md (consigne
  intégrale + procédure), STRATEGIE.md, ce journal.
- Chaîne gratuite testée : voix edge-tts (fr-FR-HenriNeural, horodatage mot par mot), images
  Pollinations.ai (repli procédural local si indisponible), musique d'ambiance originale synthétisée,
  montage PIL + ffmpeg (Ken Burns, fondus, grain, vignette, sous-titres jaunes mot par mot, barre de
  progression, mention « Fiction • Histoire inventée • IA » permanente), volume normalisé -14 LUFS.
- Tâche planifiée cloud créée : toutes les 6 h (prochain passage 19/11 à 01 h 25, heure de Paris).

**Cycle 1**
1. Journal : premier cycle, pas d'historique.
2. Stats : bloquées (pseudo TikTok inconnu, pas de clé Blotato) → voir ACTIONS REQUISES.
3. Stratégie initiale écrite (STRATEGIE.md) : séries de 3 épisodes, 70-95 s, 2 vidéos/jour en semaine 1.
4. Tendances : Creative Center inaccessible en automatique ; recherche web → #storytime efficace pour le
   visionnage complet, format « faits troublants + boîte à musique » en hausse, Noël très tôt en France.
5. Vidéo produite : **« L'Étage 4 » — Partie 1/3** (`histoires/2026-11-18_etage4_p1.json`), 79 s,
   1080x1920, 81 Mo. Accroche : « Mon immeuble n'a que trois étages. Alors pourquoi l'ascenseur
   s'arrête-t-il au quatrième… ». Créneau fixe de la série : 18:45.
   Pourquoi ce sujet : mystère du quotidien (immeuble, ascenseur), compréhensible en 2 s, très
   « commentable » (« toi, tu ouvrirais ? »), décor français proche du public.
6. Vérification : format OK, 79 s, -14 LUFS (corrigé de -16 → +2 dB), crête -2 dBFS. LanguageTool :
   « 4e » → « 4ᵉ » corrigé dans la légende ; 3 faux positifs justifiés dans le JSON
   (`verif_faux_positifs`). Planche contact contrôlée visuellement : sous-titres lisibles, visuels cohérents.
7. Programmation : **bloquée** (Blotato HTTP 401, pas de clé). La vidéo sera programmée
   automatiquement (prochain 18:45 libre) au premier cycle après ta connexion.
8. Améliorations du générateur pour la suite : normalisation du volume en deux passes, grain allégé,
   encodage final plafonné à 8 Mb/s.
- Suite prévue : écrire et produire « L'Étage 4 » P2 (bible : `histoires/series/etage4.md`).
  Tant que la publication est bloquée : max 3 vidéos prêtes en attente, puis écriture d'avance seulement.
