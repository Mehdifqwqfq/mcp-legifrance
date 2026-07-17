# Étape 1 — Générer le script de la vidéo avec un LLM

C'est l'étape « cerveau » du pipeline : un LLM (Claude, par exemple) transforme
ton document source (PDF, protocole, fiche HAS, notes…) en un **script de
scènes** prêt à animer.

## Mode d'emploi

1. Ouvre Claude (claude.ai, Claude Desktop ou Claude Code).
2. Colle le prompt ci-dessous, joins ton document (ou colle son texte).
3. Récupère le JSON produit → enregistre-le dans `scripts/scenes.json`.
4. Reporte les scènes dans `remotion/src/scenes.ts` (mêmes champs), puis
   lance l'étape 2 (`generate-voiceover.mjs`) pour créer les voix off.

## Le prompt

```text
Tu es réalisateur de vidéos explicatives « tableau blanc » (style Khan Academy).
Transforme le document ci-joint en un script de vidéo de 60 à 120 secondes,
découpé en 3 à 6 scènes, au format JSON STRICT suivant (aucun texte hors JSON) :

[
  {
    "id": "slug-court",
    "title": "1 · Titre court de la scène",
    "narration": "Une à deux phrases de voix off, 15 à 30 mots, ton clair et chaleureux.",
    "color": "#3d5a99",
    "durationInSeconds": 6,
    "paths": [
      { "d": "M360 120 H500 L560 180 V360 H360 Z", "w": 5 }
    ]
  }
]

Contraintes de dessin (champ "paths") :
- Repère SVG de 900×480 ; zone de dessin utile : x entre 320 et 680, y entre 110 et 380
  (le titre occupe le haut, le sous-titre le bas).
- Formes GÉOMÉTRIQUES SIMPLES uniquement (M, L, H, V, Q, C, S, Z) : boîtes, flèches,
  pictogrammes schématiques — 2 à 6 tracés par scène. Pas de path de plus de 200 caractères.
- Chaque scène illustre UNE idée de sa narration ; les tracés se dessinent dans l'ordre.
- Couleurs de marqueur (une par scène, rotation) : #3d5a99, #c1436d, #2a9d8f, #e0913a.

Contraintes de narration :
- Fidèle au document source, zéro invention (chiffres, posologies, noms).
- durationInSeconds ≈ mots de la narration ÷ 2,5 (arrondi au 0,5 s supérieur).
- Langue : celle du document (ou celle que je te demande).
```

## Astuce qualité

Après génération, relis chaque `narration` **avant** de produire les audios :
c'est l'étape de validation métier (indispensable pour du contenu santé), et
corriger le texte ici ne coûte rien, contrairement aux outils à crédits.
