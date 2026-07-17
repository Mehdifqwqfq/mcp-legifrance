import React from 'react';
import {Composition} from 'remotion';
import {WhiteboardVideo} from './WhiteboardVideo';
import {scenes} from './scenes';
import {FPS, WIDTH, HEIGHT, toFrames} from './config';

const totalFrames = scenes.reduce(
  (acc, s) => acc + toFrames(s.durationInSeconds),
  0,
);

export const Root: React.FC = () => {
  return (
    <Composition
      id="WhiteboardVideo"
      component={WhiteboardVideo}
      durationInFrames={totalFrames}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  );
};
