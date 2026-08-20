import React from "react";
import { Composition } from "remotion";
import { DouyinVideo } from "./Video";
import { DouyinVideoProps } from "./types";

// 默认 props：空数据，真实运行时由 --props=props.json 注入
const defaultProps: DouyinVideoProps = {
  shots: [],
  audioFile: "audio.wav",
  totalDurationSec: 12,
  aspectRatio: "9:16",
  aiLabelConfig: {
    mode: "overlay",
    duration_sec: 3,
    text: "本视频含 AI 生成内容",
  },
  title: "默认标题",
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="DouyinVideo"
      component={DouyinVideo}
      durationInFrames={300}
      fps={25}
      width={1080}
      height={1920}
      defaultProps={defaultProps}
    />
  );
};
