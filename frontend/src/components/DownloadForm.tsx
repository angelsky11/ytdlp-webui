import { useState } from 'react';
import { Form, Input, Button, Switch, message, Card, Modal, Radio, Space, Tag, Spin } from 'antd';
import type { RadioChangeEvent } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { createDownload, getVideoInfo } from '../api';
import type { DownloadRequest, VideoInfo, VideoFormat } from '../types';
import { useStore } from '../stores';
import { useLocale } from '../i18n';

// 前端日志开关，生产环境可关闭
const DEBUG_MODE = true;
const log = {
  info: (...args: unknown[]) => DEBUG_MODE && console.log('[DownloadForm]', new Date().toISOString(), ...args),
  error: (...args: unknown[]) => DEBUG_MODE && console.error('[DownloadForm ERROR]', new Date().toISOString(), ...args),
  warn: (...args: unknown[]) => DEBUG_MODE && console.warn('[DownloadForm WARN]', new Date().toISOString(), ...args),
};

export function DownloadForm() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [audioOnly, setAudioOnly] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [fetchingInfo, setFetchingInfo] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<string>('');
  const [currentUrl, setCurrentUrl] = useState('');
  const { fetchDownloads, defaultFormat } = useStore();
  const { t } = useLocale();

  const handleSubmit = async () => {
    const url = form.getFieldValue('url');
    log.info('handleSubmit called', { url, audioOnly });

    if (!url) {
      log.warn('No URL provided');
      message.error(t('home.urlRequired'));
      return;
    }

    if (audioOnly) {
      // Audio only mode - direct download
      log.info('Audio only mode - starting direct download');
      await startDownload(url, null);
    } else {
      // Video mode - show format selection modal
      log.info('Video mode - opening format selection modal');
      setCurrentUrl(url);
      setFetchingInfo(true);
      setModalVisible(true);
      log.info('Modal state: visible=true, fetchingInfo=true');

      try {
        log.info('Fetching video info for URL:', url);
        const info = await getVideoInfo({ url });
        log.info('Video info fetched successfully:', {
          title: info.title,
          formatCount: info.formats?.length || 0,
        });
        setVideoInfo(info);

        // Auto-select best quality (first format)
        if (info.formats && info.formats.length > 0) {
          setSelectedFormat(info.formats[0].format_id);
          log.info('Auto-selected best format:', info.formats[0].format_id);
        } else {
          log.warn('No formats available in video info');
          setSelectedFormat('');
        }
      } catch (error) {
        log.error('Failed to fetch video info:', error);
        message.error(t('home.failedFetchInfo'));
        setModalVisible(false);
        log.info('Modal state: visible=false (closed due to error)');
      } finally {
        setFetchingInfo(false);
        log.info('Modal state: fetchingInfo=false');
      }
    }
  };

  const startDownload = async (url: string, formatId: string | null) => {
    log.info('startDownload called', { url, formatId, audioOnly, defaultFormat });

    setLoading(true);
    log.info('Loading state: true');

    try {
      const request: DownloadRequest = {
        url,
        format: defaultFormat,
        audio_only: audioOnly,
        video_format_id: formatId || undefined,
        title: videoInfo?.title,  // 传递视频标题
      };
      log.info('Sending download request:', request);

      await createDownload(request);

      log.info('Download request successful');
      message.success(audioOnly ? t('home.audioStarted') : t('home.videoStarted'));
      form.resetFields();
      setVideoInfo(null);
      setSelectedFormat('');
      setModalVisible(false);
      log.info('Form reset, modal closed, refreshing download list');
      fetchDownloads();
    } catch (error) {
      log.error('Download request failed:', error);
      message.error(t('home.failedStart'));
    } finally {
      setLoading(false);
      log.info('Loading state: false');
    }
  };

  const handleModalOk = () => {
    log.info('handleModalOk called', { selectedFormat, currentUrl });

    if (!selectedFormat) {
      log.warn('No format selected');
      message.error(t('home.pleaseSelectFormat'));
      return;
    }
    log.info('Starting download with selected format');
    startDownload(currentUrl, selectedFormat);
  };

  const handleModalCancel = () => {
    log.info('handleModalCancel called');
    setModalVisible(false);
    setVideoInfo(null);
    setSelectedFormat('');
    log.info('Modal closed, state reset');
  };

  const handleFormatChange = (e: RadioChangeEvent) => {
    const newFormat = e.target.value as string;
    log.info('Format changed:', newFormat);
    setSelectedFormat(newFormat);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return t('common.unknown');
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  };

  const getVideoCodecLabel = (format: VideoFormat) => {
    const vcodec = (format.vcodec || '').toLowerCase();
    if (vcodec.includes('av01')) return 'AV1';
    if (vcodec.includes('vp9')) return 'VP9';
    if (vcodec.includes('avc1') || vcodec.includes('h264')) return 'H.264';
    return vcodec.toUpperCase() || format.ext.toUpperCase();
  };

  const getResolutionLabel = (format: VideoFormat) => {
    const res = format.resolution || '';
    const fps = format.fps ? ` ${format.fps}fps` : '';
    const note = format.format_note ? ` (${format.format_note})` : '';
    return `${res}${fps}${note}`;
  };

  // 调试：渲染前打印状态
  log.info('Render:', { modalVisible, fetchingInfo, hasVideoInfo: !!videoInfo, videoInfoTitle: videoInfo?.title });

  return (
    <>
      <Card title={t('home.downloadVideo')} style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical">
          <Form.Item
            name="url"
            label={t('home.videoUrl')}
            rules={[{ required: true, message: t('home.urlRequired') }]}
          >
            <Input
              placeholder={t('home.videoUrlPlaceholder')}
              size="large"
            />
          </Form.Item>

          <Form.Item name="audio_only" label={t('home.audioOnly')} valuePropName="checked">
            <Switch checked={audioOnly} onChange={setAudioOnly} />
          </Form.Item>

          {audioOnly && (
            <p style={{ color: '#666', fontSize: 12, marginTop: -8 }}>
              {t('home.audioOnlyHint')}
            </p>
          )}

          <Form.Item>
            <Button
              type="primary"
              htmlType="button"
              icon={<DownloadOutlined />}
              loading={loading}
              size="large"
              block
              onClick={handleSubmit}
            >
              {t('home.download')}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Modal
        title={t('home.selectQuality')}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        okText={t('home.startDownload')}
        cancelText={t('common.cancel')}
        width={600}
        confirmLoading={loading}
      >
        {fetchingInfo ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
            <p style={{ marginTop: 16 }}>{t('home.fetchingInfo')}</p>
          </div>
        ) : videoInfo ? (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                {videoInfo.thumbnail && (
                  <img
                    src={videoInfo.thumbnail}
                    alt={videoInfo.title}
                    style={{ width: 100, borderRadius: 8 }}
                  />
                )}
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: 0 }}>{videoInfo.title}</h3>
                  {videoInfo.uploader && <p style={{ color: '#666', margin: '4px 0' }}>{videoInfo.uploader}</p>}
                  {videoInfo.duration && (
                    <p style={{ color: '#666', margin: 0 }}>
                      {t('home.duration')}: {Math.floor(videoInfo.duration / 60)}:
                      {(videoInfo.duration % 60).toString().padStart(2, '0')}
                    </p>
                  )}
                </div>
              </div>
            </Card>

            <Radio.Group
              value={selectedFormat}
              onChange={handleFormatChange}
              style={{ width: '100%' }}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                {videoInfo.formats.map((format) => (
                  <Radio
                    key={format.format_id}
                    value={format.format_id}
                    style={{
                      width: '100%',
                      margin: 0,
                      padding: '12px 16px',
                      border: '1px solid #d9d9d9',
                      borderRadius: 8,
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                      <Space>
                        <Tag color="blue">{getResolutionLabel(format)}</Tag>
                        <Tag color="green">{getVideoCodecLabel(format)}</Tag>
                        {format.fps && <Tag color="orange">{format.fps} fps</Tag>}
                      </Space>
                      <span style={{ color: '#999', fontSize: 12 }}>
                        {formatFileSize(format.filesize)}
                      </span>
                    </div>
                  </Radio>
                ))}
              </Space>
            </Radio.Group>

            {videoInfo.formats.length === 0 && (
              <p style={{ textAlign: 'center', color: '#999' }}>
                {t('home.noFormats')}
              </p>
            )}
          </>
        ) : (
          <p style={{ textAlign: 'center', color: '#999' }}>{t('home.noInfo')}</p>
        )}
      </Modal>
    </>
  );
}
