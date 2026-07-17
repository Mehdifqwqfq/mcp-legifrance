import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';

/**
 * Un trait de marqueur qui « s'écrit tout seul ».
 *
 * Technique : `pathLength={1}` normalise la longueur du tracé à 1, ce qui
 * permet d'animer `strokeDashoffset` de 1 → 0 sans mesurer le SVG.
 * Le dessin démarre à la frame `delay` et dure `draw` frames.
 */
export const DrawnPath: React.FC<{
  /** Attribut `d` du <path> SVG. */
  d: string;
  /** Couleur d'encre. */
  color: string;
  /** Épaisseur du trait. */
  width: number;
  /** Frame (relative à la scène) où le tracé commence. */
  delay: number;
  /** Nombre de frames que prend le tracé. */
  draw: number;
}> = ({d, color, width, delay, draw}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(
    frame,
    [delay, delay + Math.max(1, draw)],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  // Rien à dessiner avant le départ (évite un point parasite au début).
  if (progress <= 0) {
    return null;
  }

  return (
    <path
      d={d}
      pathLength={1}
      fill="none"
      stroke={color}
      strokeWidth={width}
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray={1}
      strokeDashoffset={1 - progress}
    />
  );
};
