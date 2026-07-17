import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';

/**
 * Sous-titre : affiche le texte de narration en bas de l'écran,
 * avec un léger fondu d'entrée en début de scène.
 */
export const Caption: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [4, 16], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 36,
        display: 'flex',
        justifyContent: 'center',
        opacity,
      }}
    >
      <div
        style={{
          maxWidth: '78%',
          backgroundColor: 'rgba(24, 24, 28, 0.82)',
          color: '#ffffff',
          padding: '12px 26px',
          borderRadius: 12,
          fontSize: 27,
          lineHeight: 1.35,
          textAlign: 'center',
          fontFamily: 'ui-sans-serif, system-ui, sans-serif',
        }}
      >
        {text}
      </div>
    </div>
  );
};
