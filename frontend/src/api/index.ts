import type { DownloadRequest, DownloadProgress, FileInfo, VideoInfo } from '../types';
import { DownloadStatus } from '../types';
import { mockDownloads, mockFiles, mockVideoInfo } from './mock';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:58888';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export interface AppConfig {
  default_format: string;
  ytdlp_version: string;
  ytdlp_current_version: string;
  cookies_enabled: boolean;
  log_level: 'debug' | 'verbose' | 'info' | 'warn' | 'error';
  language: string;
}

export interface UpdateConfigRequest {
  default_format?: string;
  ytdlp_version?: string;
  cookies_enabled?: boolean;
  log_level?: string;
  language?: string;
}

export async function createDownload(request: DownloadRequest): Promise<DownloadProgress> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 500));
    return {
      task_id: 'mock-' + Math.random().toString(36).substr(2, 8),
      status: DownloadStatus.PENDING,
      filename: 'Mock Video.mp4',
      title: request.title || 'Mock Video',
      progress: 0,
      created_at: Date.now() / 1000,
    };
  }
  
  const response = await fetch(`${API_BASE}/downloads/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error('Failed to create download');
  return response.json();
}

export async function getDownload(taskId: string): Promise<DownloadProgress> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return mockDownloads.find(d => d.task_id === taskId) || mockDownloads[0];
  }
  
  const response = await fetch(`${API_BASE}/downloads/${taskId}`);
  if (!response.ok) throw new Error('Failed to get download');
  return response.json();
}

export async function listDownloads(): Promise<DownloadProgress[]> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return mockDownloads;
  }
  
  const response = await fetch(`${API_BASE}/downloads/`);
  if (!response.ok) throw new Error('Failed to list downloads');
  return response.json();
}

export async function cancelDownload(taskId: string): Promise<void> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return;
  }
  
  const response = await fetch(`${API_BASE}/downloads/${taskId}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to cancel download');
}

export async function removeDownload(taskId: string): Promise<void> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return;
  }
  
  const response = await fetch(`${API_BASE}/downloads/${taskId}/remove`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to remove download');
}

export async function getVideoInfo(request: DownloadRequest): Promise<VideoInfo> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockVideoInfo;
  }
  
  const response = await fetch(`${API_BASE}/downloads/info`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error('Failed to get video info');
  return response.json();
}

export async function listFiles(): Promise<FileInfo[]> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return mockFiles;
  }
  
  const response = await fetch(`${API_BASE}/files/`);
  if (!response.ok) throw new Error('Failed to list files');
  return response.json();
}

export function getDownloadUrl(filename: string): string {
  if (USE_MOCK) {
    return '#' + filename;
  }
  return `${API_BASE}/files/${encodeURIComponent(filename)}`;
}

export async function deleteFile(filename: string): Promise<void> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return;
  }
  
  const response = await fetch(`${API_BASE}/files/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete file');
}

export async function getConfig(): Promise<AppConfig> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return { default_format: 'mp4', ytdlp_version: 'stable', ytdlp_current_version: '2024.01.01', cookies_enabled: false, log_level: 'info', language: 'en' };
  }
  
  const response = await fetch(`${API_BASE}/config`);
  if (!response.ok) throw new Error('Failed to get config');
  return response.json();
}

export async function updateConfig(config: UpdateConfigRequest): Promise<AppConfig> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return { 
        default_format: config.default_format || 'mp4', 
        ytdlp_version: config.ytdlp_version || 'stable', 
        ytdlp_current_version: '2024.01.01',
        cookies_enabled: config.cookies_enabled ?? false,
        log_level: config.log_level || 'info',
        language: config.language || 'en'
      };
  }
  
  const response = await fetch(`${API_BASE}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!response.ok) throw new Error('Failed to update config');
  return response.json();
}

export async function getCookiesFiles(): Promise<{ name: string; size: number; modified: number }[]> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return [{ name: 'youtube.txt', size: 1024, modified: Date.now() }];
  }
  
  const response = await fetch(`${API_BASE}/config/cookies`);
  if (!response.ok) throw new Error('Failed to get cookies files');
  return response.json();
}

export async function uploadCookies(file: File): Promise<{ success: boolean; filename?: string; error?: string }> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { success: true, filename: file.name };
  }
  
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE}/config/cookies`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error('Failed to upload cookies');
  return response.json();
}

export async function deleteCookies(filename: string): Promise<{ success: boolean }> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return { success: true };
  }
  
  const response = await fetch(`${API_BASE}/config/cookies/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete cookies');
  return response.json();
}

export interface LogFile {
  name: string;
  size: number;
  modified: number;
  date: string;
}

export async function getLogFiles(): Promise<LogFile[]> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return [
      { name: 'app_20240101_120000.log', size: 1024, modified: Date.now(), date: '20240101' },
      { name: 'app_20240102_153000.log', size: 2048, modified: Date.now() - 86400000, date: '20240102' },
    ];
  }
  
  const response = await fetch(`${API_BASE}/config/logs`);
  if (!response.ok) throw new Error('Failed to get log files');
  return response.json();
}

export async function getLogFileContent(filename: string): Promise<{ filename: string; content: string }> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return { filename, content: '2024-01-01 12:00:00 - INFO - Application started\n2024-01-01 12:01:00 - DEBUG - Debug message' };
  }
  
  const response = await fetch(`${API_BASE}/config/logs/${encodeURIComponent(filename)}`);
  if (!response.ok) throw new Error('Failed to get log file content');
  return response.json();
}

export async function deleteLogFile(filename: string): Promise<void> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return;
  }
  
  const response = await fetch(`${API_BASE}/config/logs/${encodeURIComponent(filename)}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete log file');
}

export async function clearAllLogs(): Promise<void> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 100));
    return;
  }
  
  const response = await fetch(`${API_BASE}/config/logs`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to clear logs');
}

export async function updateYtdlp(): Promise<{ success: boolean; version?: string; type?: string; error?: string; path?: string }> {
  if (USE_MOCK) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    return { success: true, version: '2024.06.07', type: 'stable', path: '/config/ytdlp/yt-dlp' };
  }
  
  const response = await fetch(`${API_BASE}/config/ytdlp-update`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to update yt-dlp');
  return response.json();
}

export function getWebSocketUrl(): string {
  if (USE_MOCK) {
    return '';
  }
  // Use relative path for WebSocket when API_BASE is relative
  if (API_BASE.startsWith('/')) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProtocol}//${window.location.host}${API_BASE}/ws`;
  }
  const wsProtocol = API_BASE.startsWith('https') ? 'wss' : 'ws';
  const host = API_BASE.replace(/^https?:\/\//, '');
  return `${wsProtocol}://${host}/ws`;
}