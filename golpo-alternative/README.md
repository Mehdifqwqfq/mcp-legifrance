# Golpo, sans Golpo — pipeline maison de vidéos « tableau blanc »

POC complet montrant qu'on peut reproduire ce que fait [Golpo](https://video.golpoai.com)
(document → vidéo explicative « whiteboard » avec voix off synchronisée) avec
des briques standard, open source pour l'essentiel :

```
┌────────────┐    ┌──────────────┐    ┌───────────────────┐    ┌─────────┐
│  Document  │ →  │  LLM (Claude)│ →  │  TTS (ElevenLabs, │ →  │ Remotion│ → MP4
│  PDF/notes │    │  → scènes    │    │  OpenAI…) → MP3   │    │  rendu  │
└────────────┘    └──────────────┘    └───────────────────┘    └─────────┘
     source           scripts/            scripts/                remotion/
                  generate-script.md  generate-voiceover.mjs
```

## Contenu du dossier

| Dossier | Rôle |
|---|---|
| [`preview/whiteboard-demo.html`](preview/whiteboard-demo.html) | Démo autonome à ouvrir dans un navigateur (double-clic) : l'effet « marqueur qui dessine » (SVG `stroke-dashoffset` + `getPointAtLength`) synchronisé à une narration Web Speech. Zéro dépendance, zéro réseau. |
| [`remotion/`](remotion/) | Le chemin « production » : projet [Remotion](https://remotion.dev) (React) qui rend un vrai MP4 h264. Testé : 22 s en 1280×720\@30fps rendus en ~40 s. |
| [`scripts/`](scripts/) | Les deux étapes amont : prompt LLM pour générer les scènes ([`generate-script.md`](scripts/generate-script.md)) et génération des voix off ([`generate-voiceover.mjs`](scripts/generate-voiceover.mjs), ElevenLabs ou OpenAI TTS). |
| [`apothicaire-fiche/`](apothicaire-fiche/) | Fiche d'identité PDF de Golpo pour le magazine *apothicAIre* (source HTML + PDF rendu via Chromium headless). |

## Démarrage rapide (Remotion)

```bash
cd remotion
npm install
npx remotion studio          # éditeur interactif
npx remotion render WhiteboardVideo out/video.mp4
```

Sur un poste normal, Remotion télécharge tout seul son navigateur de rendu.
Dans un conteneur qui fournit déjà un Chromium (comme celui-ci), pointe-le
dessus :

```bash
npx remotion render WhiteboardVideo out/video.mp4 \
  --browser-executable=/opt/pw-browsers/chromium \
  --chrome-mode=chrome-for-testing
```

## Produire TA vidéo (les 3 étapes)

1. **Script** — suis [`scripts/generate-script.md`](scripts/generate-script.md) :
   Claude transforme ton document en `scenes.json` (narration + tracés SVG par scène).
   Reporte les scènes dans [`remotion/src/scenes.ts`](remotion/src/scenes.ts).
2. **Voix** — `ELEVENLABS_API_KEY=... node scripts/generate-voiceover.mjs scripts/scenes.json`
   → un MP3 par scène dans `remotion/public/audio/`. Mesure les durées réelles
   (`cd remotion && npx remotion ffprobe public/audio/scene-1.mp3`) et
   reporte-les dans `durationInSeconds`, puis décommente les lignes `audio:`
   de `scenes.ts`.
3. **Rendu** — `npx remotion render WhiteboardVideo out/video.mp4`.

## Ce que Golpo fait en plus (à savoir avant de choisir)

Le vrai apport de Golpo n'est pas une brique secrète, c'est l'**orchestration** :
génération des visuels par IA, synchro fine au mot près, édition au prompt,
50+ langues en un clic — contre ~1,25–2 $/min de vidéo. Ce POC montre le
mécanisme et suffit pour des besoins simples et maîtrisés ; pour du volume
sans développement, un outil géré garde son intérêt. Voir la fiche
[`apothicaire-fiche/`](apothicaire-fiche/) pour l'analyse complète.

## Régénérer le PDF de la fiche

```bash
/opt/pw-browsers/chromium --headless --no-sandbox --no-pdf-header-footer \
  --print-to-pdf=apothicaire-fiche/fiche-golpo.pdf \
  file://$PWD/apothicaire-fiche/fiche-golpo.html
```
