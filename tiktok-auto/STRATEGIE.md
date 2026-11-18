# STRATÉGIE — mise à jour à chaque cycle

_Dernière mise à jour : 2026-11-18 (cycle 1)_

## Positionnement
- **Une seule promesse** : « des histoires inventées qui donnent des frissons, en épisodes ».
  Fiction assumée (mention permanente à l'écran + légende), voix off grave, visuels sombres et
  cinématographiques, sous-titres jaunes mot par mot. Identité constante pour que le public
  reconnaisse la chaîne dès la première seconde.
- Niches : mystère, suspense, paranormal léger, destins incroyables. Public visé : francophones 16-35 ans.
- Pas de gore, pas de sujets sensibles (suicide, mineurs en danger, faits divers réels) : risque de
  modération et de baisse de distribution.

## Format (hypothèse de départ, à valider par les chiffres)
| Élément | Choix actuel | Pourquoi |
|---|---|---|
| Durée | 70-95 s | > 60 s pour l'éligibilité aux formats longs, assez court pour garder la rétention |
| Accroche | fait impossible ou question en ≤ 20 mots, lu dès 0,2 s + titre géant à l'écran | il faut accrocher en < 2 s |
| Structure | accroche → contexte (1 phrase) → 3 escalades → cliffhanger → appel à l'action | rétention par paliers |
| Séries | 3 épisodes, 1 épisode par jour et par série, même créneau | fait revenir le public ; « Partie 2 demain » toujours tenu |
| Appel à l'action | « Abonne-toi » + une question fermée en commentaire (« toi, tu ouvrirais ? ») | commentaires = signal fort |
| Voix | selon le narrateur : femme → fr-FR-DeniseNeural, homme → fr-FR-HenriNeural | consigne de l'utilisateur (18/11) |
| Images | un plan toutes les ~4,5 s (≈ 18 images par vidéo) | consigne de l'utilisateur (18/11) : plus d'images |
| Son | nappe originale synthétisée (aucun son tiers) | voir « Sons » ci-dessous |

## Calendrier
- Créneaux (heure de Paris) : **12:30**, **18:45**, **21:15**. Maximum 3 vidéos/jour.
- Phase 1 (semaine 1) : **2 vidéos/jour** — série A à 18:45, puis une 2e série ou des histoires
  uniques à 21:15. On passe à 3/jour seulement si la qualité et les vues tiennent.
- Champ `creneau` dans le JSON d'une série = créneau fixe de cette série.

## Tendances (relevé du 2026-11-18)
- Creative Center inaccessible aux navigateurs automatisés (page vide) → recherche web.
- Format storytime « faits troublants » sur fond de **boîte à musique**, en début de cycle
  (≈ +35 % en 10 jours mi-octobre) → idée : ambiance « boîte à musique » originale synthétisée
  pour une prochaine série.
- France, novembre : Noël arrive tôt dans les contenus dès le 1er novembre → série d'hiver /
  Noël inquiétant à préparer pour début décembre.
- #storytime est un des hashtags les plus efficaces pour le visionnage complet.
- Hashtags retenus : #storytime #histoire #mystere #frisson #paranormal #fiction #pourtoi (≤ 8).

## Sons
La consigne demande des sons de la bibliothèque commerciale TikTok. Or l'API de publication
(Blotato / API officielle) ne permet pas d'attacher un son de cette bibliothèque. Option la plus
prudente retenue : **aucun son tiers**, uniquement une musique d'ambiance originale générée par le
générateur (donc libre de droits, zéro risque de retrait pour droits d'auteur).

## Indicateurs et règles de décision
- Relevé à chaque cycle : abonnés, et par vidéo vues / j'aime / commentaires / partages.
- Indicateurs : vues à 24 h, taux de partage (partages/vues), taux de commentaires, abonnés gagnés
  entre deux relevés. (Rétention précise : non accessible sans TikTok Studio.)
- Une variable (thème, accroche, durée, voix, créneau) au-dessus de la médiane des 10 dernières
  vidéos 2 fois de suite → on la garde. En dessous 3 fois → on l'abandonne.
- Une série commencée est toujours terminée.

## Tests prévus (un seul changement à la fois)
1. Durée : ~75 s vs ~100 s.
3. Accroche : question vs affirmation choc.
4. Créneau : 18:45 vs 21:15.

## Feuille de route des séries
- **L'Étage 4** (en cours, 3 épisodes, 18:45) — immeuble lyonnais, ascenseur qui s'arrête à un étage inexistant.
- À suivre : « Le Passager du dernier train » (destin incroyable), « La Boîte à musique » (paranormal,
  ambiance boîte à musique), série de Noël inquiétante pour décembre.

## Leçons apprises
- 18/11 — Retour de l'utilisateur sur P1 : voix à faire correspondre au narrateur (Léa → voix de femme) et
  pas assez d'images (1 toutes les 12-15 s). Corrigé dans le générateur à partir de P2.
- 18/11 — Le service d'images gratuit limite à 1 image / 45 s par IP et refuse les graines > ~1 million :
  téléchargements séquentiels espacés de 47 s.
