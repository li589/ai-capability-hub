import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  staticFile,
  useVideoConfig,
  interpolate,
} from "remotion";
import { DouyinVideoProps, Shot } from "./types";

const FONT_FAMILY = '"Noto Sans SC", "Microsoft YaHei", sans-serif';

// 9:16 / 1:1 / 16:9 尺寸映射
const DIMENSIONS: Record<string, { width: number; height: number }> = {
  "9:16": { width: 1080, height: 1920 },
  "1:1": { width: 1080, height: 1080 },
  "16:9": { width: 1920, height: 1080 },
};

const AiLabel: React.FC<{
  text: string;
  durationInFrames: number;
}> = ({ text, durationInFrames }) => {
  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-start",
        alignItems: "center",
        paddingTop: 80,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(0,0,0,0.55)",
          color: "#fff",
          fontFamily: FONT_FAMILY,
          fontSize: 32,
          padding: "10px 24px",
          borderRadius: 8,
          fontWeight: 500,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

const BeatScene: React.FC<{
  shot: Shot;
  isActive: boolean;
}> = ({ shot, isActive }) => {
  const imageSrc = shot.image ? staticFile(shot.image) : null;
  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0b1020",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      {imageSrc ? (
        <Img
          src={imageSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      ) : (
        <div
          style={{
            color: "#fff",
            fontFamily: FONT_FAMILY,
            fontSize: 64,
            textAlign: "center",
            padding: 80,
          }}
        >
          {shot.visual_prompt}
        </div>
      )}

      {/* 底部字幕条 */}
      {shot.caption && (
        <AbsoluteFill
          style={{
            justifyContent: "flex-end",
            alignItems: "center",
            paddingBottom: 140,
            paddingLeft: 60,
            paddingRight: 60,
          }}
        >
          <div
            style={{
              backgroundColor: "rgba(0,0,0,0.6)",
              color: "#fff",
              fontFamily: FONT_FAMILY,
              fontSize: 52,
              lineHeight: 1.5,
              padding: "24px 40px",
              borderRadius: 12,
              textAlign: "center",
              fontWeight: 700,
              textShadow: "0 2px 8px rgba(0,0,0,0.8)",
            }}
          >
            {shot.caption}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

export const DouyinVideo: React.FC<DouyinVideoProps> = ({
  shots,
  audioFile,
  totalDurationSec,
  aspectRatio = "9:16",
  aiLabelConfig,
  title,
}) => {
  const { fps, width, height } = useVideoConfig();
  const dims = DIMENSIONS[aspectRatio] || DIMENSIONS["9:16"];

  // 按 shot_plan 累积起始时间
  const timedShots = useMemo(() => {
    let cursor = 0;
    return shots.map((s) => {
      const start = cursor;
      cursor += s.duration_sec;
      return { ...s, startSec: start };
    });
  }, [shots]);

  const labelFrames = Math.min(
    Math.round((aiLabelConfig?.duration_sec ?? 3) * fps),
    Math.round(totalDurationSec * fps)
  );

  return (
    <AbsoluteFill
      style={{
        width: dims.width,
        height: dims.height,
        backgroundColor: "#0b1020",
      }}
    >
      <Audio src={staticFile(audioFile)} />

      {timedShots.map((shot) => {
        const from = Math.round(shot.startSec * fps);
        const durationInFrames = Math.round(shot.duration_sec * fps);
        return (
          <Sequence
            key={shot.beat}
            from={from}
            durationInFrames={durationInFrames}
          >
            <BeatScene shot={shot} isActive />
          </Sequence>
        );
      })}

      {/* 片头标题（前 2 秒） */}
      {title && (
        <Sequence from={0} durationInFrames={Math.min(2 * fps, labelFrames)}>
          <AbsoluteFill
            style={{
              justifyContent: "center",
              alignItems: "center",
              padding: 80,
              backgroundColor: "rgba(0,0,0,0.35)",
            }}
          >
            <h1
              style={{
                color: "#fff",
                fontFamily: FONT_FAMILY,
                fontSize: 96,
                textAlign: "center",
                fontWeight: 800,
                textShadow: "0 4px 16px rgba(0,0,0,0.8)",
              }}
            >
              {title}
            </h1>
          </AbsoluteFill>
        </Sequence>
      )}

      {/* AI 标识埋点：前 N 秒 */}
      {aiLabelConfig && (
        <Sequence from={0} durationInFrames={labelFrames}>
          <AiLabel
            text={aiLabelConfig.text || "本视频含 AI 生成内容"}
            durationInFrames={labelFrames}
          />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
