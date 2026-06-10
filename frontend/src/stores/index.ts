import { create } from 'zustand';
import type { DownloadProgress, FileInfo } from '../types';
import { listDownloads, listFiles, cancelDownload, removeDownload as removeDownloadApi, deleteFile as deleteFileApi, getConfig, updateConfig as updateConfigApi, updateYtdlp as updateYtdlpApi, getCookiesFiles, uploadCookies, deleteCookies, createDownload } from '../api';

interface CookiesFile {
  name: string;
  size: number;
  modified: number;
}

interface StoreState {
  downloads: DownloadProgress[];
  files: FileInfo[];
  wsConnected: boolean;
  defaultFormat: 'mp4' | 'mkv';
  ytdlpVersion: 'stable' | 'nightly';
  ytdlpCurrentVersion: string;
  cookiesEnabled: boolean;
  logLevel: string;
  language: string;
  cookiesFiles: CookiesFile[];
  pendingFormat: 'mp4' | 'mkv';
  pendingYtdlpVersion: 'stable' | 'nightly';
  pendingCookiesEnabled: boolean;
  pendingLogLevel: string;
  hasPendingChanges: boolean;
  downloadsLoading: boolean;
  filesLoading: boolean;
  setDownloads: (downloads: DownloadProgress[]) => void;
  updateDownload: (progress: DownloadProgress) => void;
  setFiles: (files: FileInfo[]) => void;
  setWsConnected: (connected: boolean) => void;
  fetchConfig: () => Promise<void>;
  fetchCookiesFiles: () => Promise<void>;
  setPendingFormat: (format: 'mp4' | 'mkv') => void;
  setPendingYtdlpVersion: (version: 'stable' | 'nightly') => void;
  setPendingCookiesEnabled: (enabled: boolean) => void;
  setPendingLogLevel: (level: string) => void;
  saveConfig: () => Promise<void>;
  updateYtdlp: () => Promise<{ success: boolean; version?: string; error?: string }>;
  uploadCookiesFile: (file: File) => Promise<void>;
  removeCookiesFile: (filename: string) => Promise<void>;
  fetchDownloads: () => Promise<void>;
  fetchFiles: () => Promise<void>;
  cancelTask: (taskId: string) => Promise<void>;
  removeTask: (taskId: string) => Promise<void>;
  retryDownload: (task: DownloadProgress) => Promise<void>;
  deleteFile: (filename: string) => Promise<void>;
}

function checkHasPendingChanges(state: StoreState): boolean {
  return state.pendingFormat !== state.defaultFormat ||
         state.pendingYtdlpVersion !== state.ytdlpVersion ||
         state.pendingCookiesEnabled !== state.cookiesEnabled ||
         state.pendingLogLevel !== state.logLevel;
}

export const useStore = create<StoreState>((set, get) => ({
  downloads: [],
  files: [],
  wsConnected: false,
  defaultFormat: 'mp4',
  ytdlpVersion: 'stable',
  ytdlpCurrentVersion: '',
  cookiesEnabled: false,
  logLevel: 'info',
  language: 'en',
  cookiesFiles: [],
  pendingFormat: 'mp4',
  pendingYtdlpVersion: 'stable',
  pendingCookiesEnabled: false,
  pendingLogLevel: 'info',
  hasPendingChanges: false,
  downloadsLoading: true,
  filesLoading: true,

  setDownloads: (downloads) => set({ downloads }),

  updateDownload: (progress) => {
    const downloads = get().downloads;
    const index = downloads.findIndex(d => d.task_id === progress.task_id);
    if (index >= 0) {
      const newDownloads = [...downloads];
      newDownloads[index] = progress;
      set({ downloads: newDownloads });
    } else {
      set({ downloads: [progress, ...downloads] });
    }
  },

  setFiles: (files) => set({ files }),

  setWsConnected: (connected) => set({ wsConnected: connected }),

  fetchConfig: async () => {
    try {
      const config = await getConfig();
      set({ 
        defaultFormat: config.default_format as 'mp4' | 'mkv',
        ytdlpVersion: config.ytdlp_version as 'stable' | 'nightly',
        ytdlpCurrentVersion: config.ytdlp_current_version,
        cookiesEnabled: config.cookies_enabled,
        logLevel: config.log_level,
        language: config.language,
        pendingFormat: config.default_format as 'mp4' | 'mkv',
        pendingYtdlpVersion: config.ytdlp_version as 'stable' | 'nightly',
        pendingCookiesEnabled: config.cookies_enabled,
        pendingLogLevel: config.log_level,
        hasPendingChanges: false
      });
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  },

  fetchCookiesFiles: async () => {
    try {
      const files = await getCookiesFiles();
      set({ cookiesFiles: files });
    } catch (error) {
      console.error('Failed to fetch cookies files:', error);
    }
  },

  setPendingFormat: (format) => {
    set(state => ({ 
      pendingFormat: format, 
      hasPendingChanges: checkHasPendingChanges({ ...state, pendingFormat: format }) 
    }));
  },

  setPendingYtdlpVersion: (version) => {
    set(state => ({ 
      pendingYtdlpVersion: version, 
      hasPendingChanges: checkHasPendingChanges({ ...state, pendingYtdlpVersion: version }) 
    }));
  },

  setPendingCookiesEnabled: (enabled) => {
    set(state => ({ 
      pendingCookiesEnabled: enabled, 
      hasPendingChanges: checkHasPendingChanges({ ...state, pendingCookiesEnabled: enabled }) 
    }));
  },

  setPendingLogLevel: (level) => {
    set(state => ({ 
      pendingLogLevel: level, 
      hasPendingChanges: checkHasPendingChanges({ ...state, pendingLogLevel: level }) 
    }));
  },

  saveConfig: async () => {
    try {
      const current = get();
      const config = await updateConfigApi({ 
        default_format: current.pendingFormat,
        ytdlp_version: current.pendingYtdlpVersion,
        cookies_enabled: current.pendingCookiesEnabled,
        log_level: current.pendingLogLevel,
        language: current.language,
      });
      set({ 
        defaultFormat: config.default_format as 'mp4' | 'mkv',
        ytdlpVersion: config.ytdlp_version as 'stable' | 'nightly',
        ytdlpCurrentVersion: config.ytdlp_current_version,
        cookiesEnabled: config.cookies_enabled,
        logLevel: config.log_level,
        language: config.language,
        hasPendingChanges: false
      });
    } catch (error) {
      console.error('Failed to save config:', error);
      throw error;
    }
  },

  updateYtdlp: async () => {
    try {
      const result = await updateYtdlpApi();
      if (result.success && result.version) {
        set({ ytdlpCurrentVersion: result.version });
      }
      return result;
    } catch (error) {
      console.error('Failed to update yt-dlp:', error);
      return { success: false, error: String(error) };
    }
  },

  uploadCookiesFile: async (file) => {
    try {
      const result = await uploadCookies(file);
      if (result.success) {
        await get().fetchCookiesFiles();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Failed to upload cookies:', error);
      throw error;
    }
  },

  removeCookiesFile: async (filename) => {
    try {
      await deleteCookies(filename);
      await get().fetchCookiesFiles();
    } catch (error) {
      console.error('Failed to delete cookies:', error);
      throw error;
    }
  },

  fetchDownloads: async () => {
    try {
      const { downloads } = get();
      if (downloads.length === 0) set({ downloadsLoading: true });
      const result = await listDownloads();
      set({ downloads: result, downloadsLoading: false });
    } catch (error) {
      console.error('Failed to fetch downloads:', error);
      set({ downloadsLoading: false });
    }
  },

  fetchFiles: async () => {
    try {
      const { files } = get();
      if (files.length === 0) set({ filesLoading: true });
      const result = await listFiles();
      set({ files: result, filesLoading: false });
    } catch (error) {
      console.error('Failed to fetch files:', error);
      set({ filesLoading: false });
    }
  },

  cancelTask: async (taskId) => {
    try {
      await cancelDownload(taskId);
      get().fetchDownloads();
    } catch (error) {
      console.error('Failed to cancel task:', error);
    }
  },

  removeTask: async (taskId) => {
    try {
      await removeDownloadApi(taskId);
      get().fetchDownloads();
    } catch (error) {
      console.error('Failed to remove task:', error);
    }
  },

  retryDownload: async (task) => {
    try {
      const request = {
        url: task.url || '',
        format: task.format || 'best',
        audio_only: task.audio_only || false,
        output_template: task.output_template || '%(title)s.%(ext)s',
        title: task.title
      };
      await createDownload(request);
      get().fetchDownloads();
    } catch (error) {
      console.error('Failed to retry download:', error);
    }
  },

  deleteFile: async (filename) => {
    try {
      await deleteFileApi(filename);
      get().fetchFiles();
    } catch (error) {
      console.error('Failed to delete file:', error);
    }
  },
}));