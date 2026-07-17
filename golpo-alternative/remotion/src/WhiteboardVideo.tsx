import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Series,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {scenes} from './scenes';
import {toFrames} from './config';
import type {Scene} from './types';
import {DrawnPath} from './components/DrawnPath';
import {Caption} from './components/Caption';

const PAPER = '#fcfcfa';

const SceneView: React.FC<{scene: Scene; durationInFrames: number}> = ({
  scene,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const titleOpacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // On dessine tous les traits pendant les premiers 60 % de la scène,
  // répartis au prorata de leur `weight` (défaut 1). Le reste de la scène
  // laisse la narration finir.
  const drawFrames = Math.max(1, Math.floor(durationInFrames * 0.6));
  const weights = scene.paths.map((p) => p.weight ?? 1);
  const totalWeight = weights.reduce((a, b) => a + b, 0);
  let cursor = 0;
  const timings = weights.map((w) => {
    const start = cursor;
    const span = (w / totalWeight) * drawFrames;
    cursor += span;
    return {delay: Math.round(start), draw: Math.max(1, Math.round(span * 0.9))};
  });

  return (
    <AbsoluteFill>
      <svg
        viewBox="0 0 900 480"
        preserveAspectRatio="xMidYMid meet"
        style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}
      >
        <text
          x={60}
          y={82}
          fontSize={40}
          fontWeight={750}
          fill={scene.color}
          opacity={titleOpacity}
          style={{fontFamily: 'ui-sans-serif, system-ui, sans-serif'}}
        >
          {scene.title}
        </text>
        {scene.paths.map((p, i) => (
          <DrawnPath
            key={i}
            d={p.d}
            color={scene.color}
            width={p.w ?? 5}
            delay={timings[i].delay}
            draw={timings[i].draw}
          />
        ))}
      </svg>
      <Caption text={scene.narration} />
    </AbsoluteFill>
  );
};

export const WhiteboardVideo: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: PAPER,
        backgroundImage:
          'linear-gradient(#00000008 1px, transparent 1px), linear-gradient(90deg, #00000008 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }}
    >
      <Series>
        {scenes.map((scene) => {
          const durationInFrames = toFrames(scene.durationInSeconds);
          return (
            <Series.Sequence
              key={scene.id}
              durationInFrames={durationInFrames}
              name={scene.title}
            >
              <SceneView scene={scene} durationInFrames={durationInFrames} />
              {scene.audio ? <Audio src={staticFile(scene.audio)} /> : null}
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
