// 与 douyin-video-skill 下游 handoff 字段对齐的 TypeScript 类型

export interface Shot {
  beat: number;
  visual_prompt: string;
  source: "ai_gen" | "asset_pool" | "video_clip";
  duration_sec: number;
  image?: string; // public/ 下的文件名或相对路径
  caption?: string; // 该 beat 上显示的字幕
}

export interface AiLabelConfig {
  mode: "overlay" | "burn_sub";
  duration_sec: number;
  text?: string;
}

export interface DouyinVideoProps {
  shots: Shot[];
  audioFile: string; // public/ 下的音频文件名
  totalDurationSec: number;
  aspectRatio?: "9:16" | "1:1" | "16:9";
  aiLabelConfig?: AiLabelConfig;
  title?: string;
}
