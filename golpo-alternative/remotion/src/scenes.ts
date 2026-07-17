import type {Scene} from './types';

/**
 * Le « script » de la vidéo — PURE DONNÉE, miroir de scripts/scenes.json
 * (source canonique produite par le LLM, voir ../scripts/generate-script.md).
 *
 * En production : (1) le LLM génère scenes.json, (2) on reporte ici les mêmes
 * champs, (3) ../scripts/generate-voiceover.mjs synthétise les voix off dans
 * public/audio/. Une fois les MP3 générés, décommente les lignes `audio:` et
 * ajuste `durationInSeconds` à la durée réelle de chaque audio — un MP3
 * manquant ferait échouer tout le rendu.
 * (Les constantes FPS/dimensions vivent dans ./config.ts.)
 */
export const scenes: Scene[] = [
  {
    id: 'script',
    title: '1 · Le script',
    color: '#3d5a99',
    narration:
      "D'abord, un modèle de langage transforme ton document en un script, découpé scène par scène.",
    durationInSeconds: 5.5,
    // audio: 'audio/scene-1.mp3',
    paths: [
      {d: 'M360 120 H500 L560 180 V360 H360 Z', w: 5},
      {d: 'M500 120 V180 H560', w: 5},
      {d: 'M392 224 H520', w: 5},
      {d: 'M392 262 H520', w: 5},
      {d: 'M392 300 H468', w: 5},
    ],
  },
  {
    id: 'voix',
    title: '2 · La voix',
    color: '#c1436d',
    narration:
      'Ensuite, une synthèse vocale génère la narration, dans la langue et le ton de ton choix.',
    durationInSeconds: 5.5,
    // audio: 'audio/scene-2.mp3',
    paths: [
      {d: 'M372 218 H410 L462 176 V304 L410 262 H372 Z', w: 5},
      {d: 'M498 222 Q524 240 498 258', w: 5},
      {d: 'M524 200 Q566 240 524 280', w: 5},
    ],
  },
  {
    id: 'trace',
    title: '3 · Le tracé',
    color: '#2a9d8f',
    narration:
      "Chaque dessin s'anime au tracé : un SVG qui s'écrit tout seul, avec une main qui suit la ligne.",
    durationInSeconds: 6,
    // audio: 'audio/scene-3.mp3',
    paths: [
      {d: 'M356 322 C420 300 438 214 500 206 S612 250 648 190', w: 6},
      {d: 'M648 190 L622 196', w: 5},
      {d: 'M648 190 L640 214', w: 5},
    ],
  },
  {
    id: 'montage',
    title: '4 · Le montage',
    color: '#e0913a',
    narration:
      'Enfin, tout est assemblé et synchronisé en une seule vidéo. Aucun Golpo requis.',
    durationInSeconds: 5,
    // audio: 'audio/scene-4.mp3',
    paths: [
      {d: 'M356 250 H560 V332 H356 Z', w: 5},
      {d: 'M356 250 L364 214 L566 224 L560 250', w: 5},
      {d: 'M404 217 L396 250', w: 4},
      {d: 'M452 220 L444 250', w: 4},
      {d: 'M500 223 L492 250', w: 4},
    ],
  },
];
