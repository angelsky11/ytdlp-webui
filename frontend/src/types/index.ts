export const DownloadStatus = {
  PENDING: "pending",
  DOWNLOADING: "downloading",
  COMPLETED: "completed",
  FAILED: "failed",
  CANCELLED: "cancelled",
} as const;

export type DownloadStatus = typeof DownloadStatus[keyof typeof DownloadStatus];

export interface DownloadProgress {
  task_id: string;
  status: DownloadStatus;
  url?: string;
  filename?: string;
  title?: string;
  progress: number;
  stage?: string;
  speed?: string;
  eta?: string;
  error?: string;
  created_at?: number;
  format?: string;
  audio_only?: boolean;
  output_template?: string;
}

export interface FileInfo {
  name: string;
  path: string;
  size: number;
  created_at: number;
}

export interface VideoFormat {
  format_id: string;
  ext: string;
  resolution?: string;
  fps?: number;
  filesize?: number;
  vcodec?: string;
  acodec?: string;
  format_note?: string;
}

export interface VideoInfo {
  title: string;
  thumbnail?: string;
  duration?: number;
  uploader?: string;
  formats: VideoFormat[];
}

export interface DownloadRequest {
  url: string;
  format?: string;
  audio_only?: boolean;
  output_template?: string;
  video_format_id?: string;
  title?: string;
}