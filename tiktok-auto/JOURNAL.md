# JOURNAL

## ✅ ACTIONS REQUISES : aucune pour l'instant

Connexions faites le 2026-11-18 (Blotato relié au compte TikTok @rt_production_, clé API enregistrée
en « network secret » de l'environnement cloud). Si une connexion expire, l'instruction réapparaîtra ici.

### Blocages en cours
- TikTok Creative Center : page vide en navigateur automatisé (protection anti-robot).
  Non contourné ; tendances relevées par recherche web à la place.
- Liste détaillée des vidéos (vues par vidéo) non récupérée au premier relevé : seuls les chiffres du
  profil le sont. À surveiller aux prochains cycles.

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

### 2026-11-18 ~21 h 40 (Paris) — Connexions terminées
- Blotato : connexion OK, compte TikTok **@rt_production_** (id Blotato 69898) enregistré dans config.json.
- **« L'Étage 4 » P1 programmée pour le 19/11 à 18 h 45** (postSubmissionId a2ee75b3-…), étiquette IA activée.
- Premier relevé de stats : **407 abonnés, 9 877 j'aime, 2 vidéos** (point de départ de la croissance).

### 2026-11-18 ~21 h 50 (Paris) — Test de publication immédiate (demandé par l'utilisateur)
- « L'Étage 4 » P1 **publiée tout de suite** : https://www.tiktok.com/@rt_production_/video/7709614358640233750
  (statut Blotato « published » en ~80 s, étiquette IA activée).
- Programmation du 19/11 18 h 45 annulée (DELETE /v2/schedules/7154212) pour éviter un doublon.
- Conséquence : **P2 doit sortir le 19/11 à 18 h 45** (promesse « la suite demain »). Priorité du prochain cycle.
- Note technique : la liste des programmations est `GET /v2/schedules`, l'annulation `DELETE /v2/schedules/<id numérique>`.

### 2026-11-18 ~23 h (Paris) — Retour de l'utilisateur appliqué + P2 programmée
- Demande de l'utilisateur : (1) voix accordée au personnage (fille → voix de femme, garçon → voix d'homme),
  (2) plus d'images. Appliqué dans le générateur et inscrit comme règle permanente dans CLAUDE.md :
  champ `narrateur.genre` → fr-FR-DeniseNeural / fr-FR-HenriNeural ; un plan toutes les ~4,5 s.
- Incidents corrigés : le service d'images gratuit refuse les requêtes parallèles (HTTP 402, 1 image / 45 s
  par IP) et les graines trop grandes (HTTP 400) → téléchargements séquentiels espacés de 47 s, graine réduite.
  Durée de production : ~20 min par vidéo.
- Défaut repéré à la vérification : le mot surligné débordait sur l'espace suivant (« FRAPPÉÀ ») → corrigé
  (agrandissement centré sur le mot, espaces plus larges).
- **« L'Étage 4 » P2** : 85,5 s, voix de femme (Léa), 18 images / 19 plans, -14,5 LUFS. 2 faux positifs
  LanguageTool justifiés. **Programmée le 19/11 à 18 h 45** (postSubmissionId bca0f17c-…).
- Prochain cycle : écrire et produire P3 (fin de série, voix de femme) pour le 20/11 à 18 h 45, puis lancer
  une 2ᵉ série au créneau de 21 h 15.

### 2026-11-18 ~23 h 05 (Paris) — P1 remplacée (demande de l'utilisateur)
- L'utilisateur a supprimé l'ancienne P1 (voix d'homme, 5 images) sur TikTok.
- Nouvelle **P1 v2** (voix de femme pour Léa, 18 images / plans de ~4,5 s, 84 s, -14,8 LUFS, vérifiée)
  **publiée immédiatement** : https://www.tiktok.com/@rt_production_/video/7709636116361628950
- Nouvelle option : `publier.py programmer <json> --maintenant` (publication immédiate).
- P2 reste programmée le 19/11 à 18 h 45 ; P3 à produire pour le 20/11 à 18 h 45.
- Note : supprimer une vidéo déjà publiée n'est pas possible par l'API (Blotato/TikTok) : seulement
  depuis l'appli TikTok, par l'utilisateur.

### 2026-11-19 ~02 h (Paris) — Cycle 2 (automatique)
1. Statut : P1 v2 publiée, P2 programmée le 19/11 à 18 h 45 (Blotato : scheduled).
2. Stats : profil 406 abonnés (-1), 9 865 j'aime, 1 vidéo visible. P1 v2 : **28 vues**, 0 j'aime, 0 partage
   après ~2 h 30 (publiée à 23 h, heure creuse). Trop tôt pour conclure.
   Nouveau : `stats.py` lit maintenant la page publique de chaque vidéo publiée (vues, j'aime, commentaires,
   partages, enregistrements).
3. Décision : rien à abandonner encore. Remarque : le profil n'affiche qu'une vidéo (les 2 anciennes vidéos
   du compte ne sont plus visibles — supprimées ou privées par l'utilisateur ? aucune action de ma part).
4. Tendances (recherche web ; Creative Center toujours inaccessible) : les hashtags génériques (#fyp, #pourtoi)
   n'aident pas, 1 à 5 hashtags précis oui → passage à 5 hashtags (#storytime #mystere #frisson #creepytiktok #fiction).
5. **« L'Étage 4 » P3 (fin)** : 92 s, voix de femme, 20 images / 21 plans, -14,6 LUFS, 0 faute. Planche contrôlée :
   « 4ᵉ » seul sur une ligne du titre → retour à la ligne corrigé dans le générateur, vidéo refaite.
   Programmée le 20/11 à 18 h 45.
6. Prochaine série prête à écrire : **« Le Dernier Train »** (voix d'homme, narrateur Thomas), P1 le 21/11 à
   18 h 45 — promis à la fin de P3. Bible : histoires/series/dernier_train.md.

### 2026-11-19 ~08 h 15 (Paris) — Cycle 3 (automatique)
1. Statut : P2 (19/11 18 h 45) et P3 (20/11 18 h 45) programmées ; P1 v2 en ligne.
2. Stats : 406 abonnés, 9 865 j'aime. P1 v2 : **37 vues, 0 j'aime, 0 partage** en ~8 h.
3. Décision : une seule donnée, publiée à 23 h → pas de changement de format. Hypothèses notées dans
   STRATEGIE.md (première image plus forte, accroche plus courte, durée plus courte) à tester si les
   publications de 18 h 45 restent faibles.
4. **« Le Dernier Train » P1** produite : narrateur Thomas → voix d'homme (fr-FR-HenriNeural), 86 s,
   20 images / 20 plans, -15,4 LUFS. 1 faux positif LanguageTool justifié (« Puis il s'est levé »).
   Planche contrôlée. **Programmée le 21/11 à 18 h 45** (tenue de la promesse de fin de L'Étage 4).
   Hashtags : #storytime #mystere #frisson #train #fiction.
5. Prochain cycle : P2 du Dernier Train (22/11) ou une histoire courte autonome au créneau de 21 h 15
   pour tester un 2ᵉ créneau quotidien.

### 2026-11-19 ~14 h (Paris) — Cycle 4 (automatique)
1. Statut : P2 ce soir 18 h 45, P3 le 20/11, Dernier Train P1 le 21/11 (toutes programmées).
2. Stats : 406 abonnés, 9 870 j'aime. P1 v2 : **90 vues, 5 j'aime**, 0 commentaire, 0 partage (~14 h).
3. Décision : continuer le format. Test d'un 2ᵉ créneau quotidien avec un format court autonome.
4. **« La pellicule de 1974 »** (histoire courte, narratrice Camille → voix de femme) : 69,5 s, 17 images,
   -14,9 LUFS, 0 faute, planche contrôlée. **Programmée ce soir 19/11 à 21 h 15.**
5. Prochain cycle : Dernier Train P2 (22/11 18 h 45) ; nouvelle histoire courte pour le 20/11 à 21 h 15 si le
   temps le permet (1 vidéo par cycle).

### 2026-11-19 ~20 h (Paris) — Cycle 5 (automatique)
1. Statut : **L'Étage 4 P2 publiée à 18 h 45** comme prévu (https://www.tiktok.com/@rt_production_/video/7709940130899070231).
   « La pellicule de 1974 » programmée ce soir 21 h 15 ; P3 le 20/11 ; Dernier Train P1 le 21/11.
2. Stats : 406 abonnés (stable), 9 871 j'aime. P1 v2 : **257 vues, 6 j'aime, 1 enregistrement** (~21 h).
   P2 : 12 vues à 40 min.
3. Décision : pas de changement (données encore insuffisantes, test du 21 h 15 en cours ce soir).
   Point d'attention : 0 abonné gagné pour l'instant → à surveiller sur 3 vidéos.
4. **« Le Dernier Train » P2** : voix d'homme, 92 s, 21 images, -15,4 LUFS, 0 faute, planche contrôlée.
   **Programmée le 22/11 à 18 h 45.**
5. Prochain cycle : Dernier Train P3 (23/11) ou nouvelle histoire courte à 21 h 15 selon le résultat du test.

### 2026-11-20 ~02 h (Paris) — Cycle 6 (automatique)
1. Statut : « La pellicule de 1974 » publiée hier à 21 h 15 (https://www.tiktok.com/@rt_production_/video/7709978807909862678).
   À venir : L'Étage 4 P3 (20/11), Dernier Train P1 (21/11), P2 (22/11).
2. Stats : **404 abonnés (-2)**, 9 877 j'aime. P1 v2 : 271 vues / 8 j'aime ; P2 (18 h 45) : **232 vues en ~6 h** ;
   La pellicule (21 h 15) : 106 vues en ~3 h. Toujours 0 commentaire, 0 partage.
3. Décisions : 18 h 45 = meilleur créneau. Problème n°1 = conversion (0 commentaire, 0 abonné) → test d'un
   carton de fin « question + oui ou non en commentaire » à la place de « Abonne-toi » (STRATEGIE.md).
   Règle LanguageTool VIRGULE_DEBUT_DE_PHRASE ignorée globalement (3 faux positifs sur 3).
4. **« Le Dernier Train » P3 (fin)** : voix d'homme, 92,6 s, images sans repli, -15,6 LUFS, 0 faute, carton
   de fin interactif vérifié. **Programmée le 23/11 à 18 h 45.**
5. Prochain cycle : nouvelle série pour le 24/11 (promise en fin de P3), et/ou histoire courte à 21 h 15
   selon les vues à 24 h de « La pellicule ».
