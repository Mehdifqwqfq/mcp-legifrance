/**
 * Paramètres de composition — séparés de scenes.ts pour que celui-ci reste
 * de la pure donnée (régénérable depuis scenes.json sans casser le build).
 */
export const FPS = 30;
export const WIDTH = 1280;
export const HEIGHT = 720;

/** Convertit une durée en secondes en frames, jamais < 1 (Remotion rejette 0). */
export const toFrames = (seconds: number): number =>
  Math.max(1, Math.round(seconds * FPS));
