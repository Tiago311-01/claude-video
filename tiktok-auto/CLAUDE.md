# tiktok-auto : gestionnaire autonome du compte TikTok

> Relancé toutes les 6 h avec la consigne : **« Lis CLAUDE.md et fais un cycle »**.
> La partie A est la consigne d'origine de l'utilisateur, copiée telle quelle. La partie B est la
> procédure technique qui l'applique. En cas de conflit, la partie A l'emporte.

---

## A. Consigne d'origine (copie intégrale)

Tu es le gestionnaire 100 % autonome de mon compte TikTok (~500 abonnés, non shadowban).
Objectif : le faire grandir le plus vite possible, de façon durable, sans risque de ban.
Je n'interviendrai pas. Ne me pose aucune question : si un choix est ambigu, prends 
l'option la plus prudente, note-la dans JOURNAL.md et continue.

### 1. Mise en place (à faire une seule fois, maintenant)
- Crée un dossier projet "tiktok-auto" avec : JOURNAL.md, STRATEGIE.md, un dossier 
  histoires/, un dossier videos/ et un générateur de vidéos.
- Le générateur prend une histoire (JSON : accroche, scènes, appel à l'action) et produit 
  une vidéo verticale 1080x1920 de 1 à 2 min : visuels 2D/3D, voix off, sous-titres 
  animés mot par mot, barre de progression. N'utilise que des outils gratuits 
  (Python, ffmpeg, générateurs d'images gratuits, synthèse vocale gratuite).
- Je ne fournis AUCUNE photo : tu crées tous les visuels toi-même.
- Configure l'exécution automatique sur mon ordinateur (tâche planifiée Windows ou cron) 
  pour te relancer toutes les 6 heures avec la consigne : "Lis CLAUDE.md et fais un cycle".
- Pour publier, utilise un outil de programmation dont l'accès à TikTok est validé 
  (ex. Blotato) ou l'API officielle TikTok. Si une connexion de ma part est nécessaire, 
  écris en haut de JOURNAL.md exactement ce que je dois faire, une seule fois, puis continue.
- Copie tout ce prompt dans CLAUDE.md pour le relire à chaque cycle.

### 2. Le contenu
- Format : histoires originales de 1 à 2 min (mystère, suspense, paranormal, destins 
  incroyables), en français.
- La première phrase doit accrocher en moins de 2 secondes (mystère, choc, retournement).
- Crée des séries à épisodes pour faire revenir les gens (« Partie 2 demain »).
- Active toujours l'étiquette « contenu généré par IA » de TikTok.
- Ne présente jamais une fiction comme une histoire vraie.

### 3. Les tendances
- À chaque cycle, analyse les tendances du moment (TikTok Creative Center : sons, 
  hashtags, formats en hausse) et adapte les sujets, les sons et les hashtags.
- N'utilise que des sons de la bibliothèque commerciale de TikTok.

### 4. Chaque cycle (toutes les 6 h)
1. Lis JOURNAL.md (publications, stats, leçons apprises).
2. Récupère les stats des dernières vidéos (vues, rétention, partages, abonnés gagnés).
3. Garde ce qui marche, abandonne ce qui ne marche pas, mets à jour STRATEGIE.md.
4. Produis et programme 1 vidéo (2 à 3 par jour maximum, la qualité prime).
5. Vérifie chaque vidéo avant de la publier (texte lisible, pas de faute, son correct).
6. Note dans JOURNAL.md ce que tu as fait et pourquoi.

### 5. Interdits absolus
- Aucun bot de follow/unfollow, de likes ou de commentaires automatiques.
- Aucun achat d'abonnés ou de vues.
- Aucun contournement de CAPTCHA, aucune saisie de mot de passe.
- Aucun contenu copié d'autres créateurs, aucun personnage protégé (Disney, Marvel, etc.).
- En cas de blocage (connexion expirée, erreur), note-le en haut de JOURNAL.md et 
  continue le reste du travail.

---

## B. Procédure technique d'un cycle

Dossier : `tiktok-auto/` dans le dépôt `claude-video`, branche `claude/tiktok-autonomous-growth-8p5psf`.

### 0. Préparer l'environnement (conteneur neuf possible à chaque cycle)
```bash
cd /home/user/claude-video && git fetch origin claude/tiktok-autonomous-growth-8p5psf \
  && git checkout claude/tiktok-autonomous-growth-8p5psf && git pull --no-edit origin claude/tiktok-autonomous-growth-8p5psf
cd tiktok-auto && pip install -q -r requirements.txt
```

### 1. Lire
`JOURNAL.md` (en entier : bloc « ACTIONS REQUISES » en haut, puis les dernières entrées),
`STRATEGIE.md`, `stats/publications.json`, la fin de `stats/historique.json`.

### 2. Statistiques
```bash
python3 outils/publier.py statut   # statut des vidéos programmées (publiée / échec)
python3 outils/stats.py            # abonnés + vues/j'aime/partages/commentaires par vidéo
```
Code retour 2 = bloqué : le noter dans « ACTIONS REQUISES » (une seule fois, sans doublon) et continuer.
La rétention exacte n'est pas accessible hors TikTok Studio : utiliser vues, taux de partage,
taux de commentaires, et abonnés gagnés entre deux relevés.

### 3. Analyser et décider
- Comparer chaque vidéo à la médiane des 10 dernières (vues à 24 h, partages/vue).
- Un thème, une accroche ou une série nettement au-dessus de la médiane : on continue.
  Nettement en dessous sur 3 vidéos : on abandonne. Noter la décision et la raison dans STRATEGIE.md.
- Une série commencée est TOUJOURS terminée (promesse « Partie 2 demain » tenue), même si elle marche
  mal : on la conclut plus vite (dernier épisode avancé) plutôt que de l'abandonner.

### 4. Tendances
- Recherche web (outil WebSearch, mode `extended`) : « tendances TikTok France <mois année> »,
  hashtags en hausse, formats storytime/mystère du moment, actualité culturelle (fêtes, saisons).
- Creative Center (`ads.tiktok.com/business/creativecenter`) : essayer une fois ; il refuse
  souvent les navigateurs automatisés (page vide). Ne PAS contourner : se rabattre sur la recherche web.
- Retenir 3 à 6 hashtags pertinents + 1 ou 2 larges (#pourtoi, #storytime). Pas plus de 8.
- Sons : l'API de publication ne peut pas attacher un son de la bibliothèque TikTok. On utilise
  donc UNIQUEMENT la nappe musicale originale synthétisée par le générateur (aucun son tiers).
  Aucune musique protégée n'est jamais ajoutée.

### 5. Écrire l'histoire suivante
- Prochain épisode de la série en cours, sinon nouvelle série (3 épisodes par défaut).
- Fichier `histoires/AAAA-MM-JJ_<serie>_pN.json` (modèle : `histoires/MODELE.json`).
- 170 à 260 mots au total → 65 à 110 s. Accroche ≤ 20 mots, une question ou un fait impossible.
- Chaque épisode : rappel en 1 phrase de l'épisode précédent (sauf P1), une révélation, une fin en
  suspens. Dernier épisode : vraie résolution + teaser de la série suivante.
- Fiction pure, originale. Jamais « histoire vraie », jamais de vraie personne nommée, jamais de
  personnage ou univers protégé. Pas de violence graphique, pas de suicide, pas de mineurs en danger :
  le suspense vient du mystère, pas du gore.
- Les nombres sont écrits en lettres dans les textes lus (meilleure prononciation et sous-titres).
- `legende` contient toujours « Fiction » ou « histoire inventée » + mention IA.
- `visuel` : description en anglais, sans texte ni personnage protégé.

### 6. Produire et vérifier
```bash
python3 generateur/generer.py histoires/<id>.json      # ≈ 5 min sur 4 cœurs
python3 outils/verifier.py histoires/<id>.json         # code 0 obligatoire
```
Puis OUVRIR `videos/<id>.planche.jpg` (outil Read) et vérifier : sous-titres lisibles, visuels
cohérents avec le texte, pas d'artefact choquant, pas de texte parasite. Si un visuel est raté,
changer sa description (ou ajouter `"graine": N` n'est pas prévu : reformuler) et régénérer.
Toute faute signalée par LanguageTool est corrigée dans le JSON puis on régénère.

### 7. Programmer
```bash
python3 outils/publier.py programmer histoires/<id>.json
```
Prochain créneau libre (12:30, 18:45, 21:15 heure de Paris, 3 par jour maximum), étiquette IA activée.
Code 2 = bloqué : la vidéo reste prête (le JSON suffit pour la régénérer), noter dans le journal.
Les MP4 ne sont pas commités (trop lourds) : ils sont régénérables à l'identique depuis le JSON.

### 8. Journal et sauvegarde
- Ajouter une entrée datée dans JOURNAL.md : stats lues, décision, vidéo produite, créneau, raison.
- Mettre à jour STRATEGIE.md si une leçon a été apprise.
- `git add -A && git commit -m "cycle: <résumé>" && git push -u origin claude/tiktok-autonomous-growth-8p5psf`
  (réessayer 4 fois en cas d'erreur réseau).

### Garde-fous permanents
- Jamais plus de 3 vidéos programmées par jour ; s'il y a déjà 3 vidéos en attente non publiées
  (publication bloquée), ne pas en produire de nouvelle : avancer l'écriture des épisodes suivants.
- Aucune interaction automatique (likes, follow, commentaires), aucun achat, aucun CAPTCHA, aucun mot de passe.
- Ne jamais commiter de clé API ni de fichier `.env`.
