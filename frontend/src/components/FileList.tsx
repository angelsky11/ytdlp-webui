import { useMemo, useState, useEffect } from 'react';
import { Button, message, Card, Empty, Popconfirm, Skeleton } from 'antd';
import { DownloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useStore } from '../stores';
import { useLocale } from '../i18n';
import { getDownloadUrl } from '../api';
import type { FileInfo } from '../types';

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`;
}

function formatDate(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString();
}

interface GroupedFile {
  groupKey: string;
  videoFile: FileInfo | null;
  thumbnailFile: FileInfo | null;
  jsonFile: FileInfo | null;
  otherFiles: FileInfo[];
  totalSize: number;
  createdAt: number;
  displayName: string;
}

/** Normalize video ID pattern from filename like "Title [videoID].ext" */
function normalizeDisplayName(filename: string): string {
  // Remove extension (include both video and audio)
  let name = filename.replace(/\.(info\.)?json$|\.(mp4|mkv|webm|avi|mov|flv|mp3|m4a|ogg|wav|webp|jpg|jpeg|png)$/i, '');
  // Remove video ID bracket suffix like [abc123]
  name = name.replace(/\s*\[[\w-]+\]$/, '');
  return name.trim();
}

/** Get file group key - everything except video-specific extensions */
function getFileGroupKey(filename: string): string {
  const lower = filename.toLowerCase();
  // Handle .info.json specially
  let base = lower;
  if (base.endsWith('.info.json')) base = base.slice(0, -10);
  else {
    const dotIdx = base.lastIndexOf('.');
    if (dotIdx > 0) base = base.slice(0, dotIdx);
  }
  // Remove video ID suffix [xxx] for grouping
  base = base.replace(/\s*\[[\w-]+\]$/, '');
  return base;
}

/** Get file type category */
function getFileCategory(filename: string): 'video' | 'thumbnail' | 'json' | 'other' {
  const lower = filename.toLowerCase();
  if (lower.endsWith('.info.json')) return 'json';
  if (lower.endsWith('.json')) return 'json';
  // Include both video and audio extensions
  if (lower.match(/\.(mp4|mkv|webm|avi|mov|flv|mp3|m4a|ogg|wav)$/)) return 'video';
  if (lower.match(/\.(webp|jpg|jpeg|png)$/)) return 'thumbnail';
  return 'other';
}

function groupFiles(files: FileInfo[]): GroupedFile[] {
  const groups = new Map<string, GroupedFile>();
  
  for (const file of files) {
    const key = getFileGroupKey(file.name);
    const cat = getFileCategory(file.name);
    
    if (!groups.has(key)) {
      groups.set(key, {
        groupKey: key,
        videoFile: null,
        thumbnailFile: null,
        jsonFile: null,
        otherFiles: [],
        totalSize: 0,
        createdAt: file.created_at,
        displayName: normalizeDisplayName(file.name),
      });
    }
    
    const group = groups.get(key)!;
    group.totalSize += file.size;
    group.createdAt = Math.max(group.createdAt, file.created_at);
    
    switch (cat) {
      case 'video':
        group.videoFile = file;
        break;
      case 'thumbnail':
        // Prefer jpg over webp
        if (!group.thumbnailFile || file.name.toLowerCase().endsWith('.jpg')) {
          group.thumbnailFile = file;
        }
        break;
      case 'json':
        group.jsonFile = file;
        break;
      default:
        group.otherFiles.push(file);
    }
  }
  
  return Array.from(groups.values()).sort((a, b) => b.createdAt - a.createdAt);
}

/** 缩略图组件：加载失败时显示 fallback 图标 */
function ThumbnailCover({ src, alt, icon }: { src: string; alt: string; icon: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <div style={{
        height: 120,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 48,
        background: '#fafafa',
      }}>
        {icon}
      </div>
    );
  }
  return (
    <div style={{
      height: 180,
      overflow: 'hidden',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f0f0f0',
    }}>
      <img
        src={src}
        alt={alt}
        style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
        onError={() => setFailed(true)}
      />
    </div>
  );
}

export function FileList() {
  const { files, deleteFile, fetchFiles, filesLoading } = useStore();
  const { t } = useLocale();

  // 组件挂载时刷新数据。已有缓存立即显示，数据返回后自动更新。
  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const groupedFiles = useMemo(() => groupFiles(files), [files]);
  
  /** 构建缩略图 URL：优先使用 DB 记录，否则根据视频文件名构造 .jpg 路径 */
  const getThumbnailUrl = (group: GroupedFile): string | null => {
    if (group.thumbnailFile) {
      return getDownloadUrl(group.thumbnailFile.name);
    }
    // DB 中无缩略图记录时，尝试加载同名的 .jpg（由 convert_thumbnail_to_jpg 生成）
    if (group.videoFile) {
      const jpgName = group.videoFile.name.replace(/\.\w+$/, '.jpg');
      return getDownloadUrl(jpgName);
    }
    return null;
  };

  const handleDownload = (filename: string) => {
    window.open(getDownloadUrl(filename), '_blank');
  };

  const handleDeleteGroup = async (group: GroupedFile) => {
    try {
      // 只需删除视频文件，后端会自动删除同组所有文件
      if (group.videoFile) {
        await deleteFile(group.videoFile.name);
        message.success(t('downloads.deleted'));
      }
    } catch {
      message.error(t('downloads.deleteFailed'));
    }
  };

  return (
    <div>
      <h3 style={{ marginBottom: 16 }}>{t('downloads.title')}</h3>
      {filesLoading && groupedFiles.length === 0 ? (
        <Skeleton active paragraph={{ rows: 6 }} />
      ) : groupedFiles.length === 0 ? (
        <Empty description={t('downloads.noFiles')} />
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: 16,
        }}>
          {groupedFiles.map((group) => {
            const mainFile = group.videoFile || group.otherFiles[0];
            const thumbnailUrl = getThumbnailUrl(group);
            const icon = group.videoFile ? '🎬' : group.thumbnailFile ? '🖼️' : '📁';
            
            return (
              <Card
                key={group.groupKey}
                size="small"
                hoverable
                style={{ height: '100%' }}
                cover={
                  <ThumbnailCover
                    src={thumbnailUrl || ''}
                    alt={group.displayName}
                    icon={icon}
                  />
                }
                actions={[
                  mainFile && (
                      <Button
                      type="primary"
                      icon={<DownloadOutlined />}
                      size="small"
                      onClick={() => handleDownload(mainFile.name)}
                    >
                      {t('downloads.download')}
                    </Button>
                  ),
                  <Popconfirm
                    title={t('downloads.deleteConfirm')}
                    description={t('downloads.deleteDesc')}
                    onConfirm={() => handleDeleteGroup(group)}
                    okText={t('common.yes')}
                    cancelText={t('common.cancel')}
                  >
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      size="small"
                    />
                  </Popconfirm>,
                ].filter(Boolean)}
              >
                <Card.Meta
                  title={
                    <div style={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      fontSize: 13,
                    }}>
                      {group.displayName}
                    </div>
                  }
                  description={
                    <div>
                      <div style={{ color: '#999', fontSize: 12 }}>
                        {formatSize(group.totalSize)}
                        {group.videoFile && group.thumbnailFile && ` · ${t('downloads.withThumbnail')}`}
                        {group.jsonFile && ` · ${t('downloads.info')}`}
                      </div>
                      <div style={{ color: '#999', fontSize: 12 }}>
                        {formatDate(group.createdAt)}
                      </div>
                    </div>
                  }
                />
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}