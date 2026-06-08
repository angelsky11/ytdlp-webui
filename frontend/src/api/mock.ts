import type { DownloadProgress, FileInfo, VideoInfo } from '../types';
import { DownloadStatus } from '../types';

export const mockDownloads: DownloadProgress[] = [
  {
    task_id: 'abc123',
    status: DownloadStatus.COMPLETED,
    filename: 'Video Title 1.mp4',
    title: 'Video Title 1',
    progress: 100,
    created_at: Date.now() / 1000 - 3600,
  },
  {
    task_id: 'def456',
    status: DownloadStatus.DOWNLOADING,
    filename: 'Video Title 2.mp4',
    title: 'Video Title 2',
    progress: 45,
    speed: '2.5 MB/s',
    eta: '00:15',
    created_at: Date.now() / 1000 - 1800,
  },
  {
    task_id: 'ghi789',
    status: DownloadStatus.PENDING,
    filename: 'Video Title 3.mp4',
    title: 'Video Title 3',
    progress: 0,
    created_at: Date.now() / 1000 - 900,
  },
  {
    task_id: 'jkl012',
    status: DownloadStatus.FAILED,
    filename: 'Video Title 4.mp4',
    title: 'Video Title 4',
    progress: 0,
    error: 'Network error',
    created_at: Date.now() / 1000 - 300,
  },
];

export const mockFiles: FileInfo[] = [
  {
    name: 'video1.mp4',
    path: '/downloads/video1.mp4',
    size: 12582912,
    created_at: Date.now() / 1000 - 3600,
  },
  {
    name: 'audio.mp3',
    path: '/downloads/audio.mp3',
    size: 3565158,
    created_at: Date.now() / 1000 - 7200,
  },
  {
    name: 'video2.webm',
    path: '/downloads/video2.webm',
    size: 8945678,
    created_at: Date.now() / 1000 - 1800,
  },
];

export const mockVideoInfo: VideoInfo = {
  title: 'Sample Video Title',
  thumbnail: 'https://via.placeholder.com/320x180',
  duration: 60,
  uploader: 'Sample Channel',
  formats: [
    { format_id: '137', ext: 'mp4', resolution: '1920x1080', fps: 30, filesize: 52428800, vcodec: 'h264', acodec: 'aac', format_note: '1080p' },
    { format_id: '136', ext: 'mp4', resolution: '1280x720', fps: 30, filesize: 26214400, vcodec: 'h264', acodec: 'aac', format_note: '720p' },
    { format_id: '135', ext: 'mp4', resolution: '854x480', fps: 30, filesize: 13107200, vcodec: 'h264', acodec: 'aac', format_note: '480p' },
    { format_id: '134', ext: 'mp4', resolution: '640x360', fps: 30, filesize: 6553600, vcodec: 'h264', acodec: 'aac', format_note: '360p' },
    { format_id: '133', ext: 'mp4', resolution: '426x240', fps: 30, filesize: 3276800, vcodec: 'h264', acodec: 'aac', format_note: '240p' },
  ],
};