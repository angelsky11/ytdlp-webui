import { useState, useRef, useEffect, Fragment, useCallback } from 'react';
import { Card, Typography, Space, Segmented, Button, message, Divider, Switch, Popconfirm, List, Drawer } from 'antd';
import { SaveOutlined, SyncOutlined, UploadOutlined, DeleteOutlined, FileTextOutlined, EyeOutlined } from '@ant-design/icons';
import { useStore } from '../stores';
import { useLocale, type Locale } from '../i18n';
import { getLogFiles, getLogFileContent, deleteLogFile, clearAllLogs, type LogFile } from '../api';

const { Title, Text } = Typography;

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export default function Settings() {
  const { 
    ytdlpCurrentVersion, cookiesFiles,
    pendingFormat, pendingYtdlpVersion, pendingCookiesEnabled, pendingLogLevel, hasPendingChanges,
    setPendingFormat, setPendingYtdlpVersion, setPendingCookiesEnabled, setPendingLogLevel, 
    saveConfig, updateYtdlp, fetchConfig, fetchCookiesFiles, uploadCookiesFile, removeCookiesFile
  } = useStore();
  const { t, locale, setLocale } = useLocale();
  
  const [saving, setSaving] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [logFiles, setLogFiles] = useState<LogFile[]>([]);
  const [logFilesLoading, setLogFilesLoading] = useState(false);
  const [logContentVisible, setLogContentVisible] = useState(false);
  const [currentLogContent, setCurrentLogContent] = useState('');
  const [currentLogFilename, setCurrentLogFilename] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchLogFiles = useCallback(async () => {
    setLogFilesLoading(true);
    try {
      const files = await getLogFiles();
      setLogFiles(files);
    } catch {
      message.error(t('settings.saveFailed'));
    } finally {
      setLogFilesLoading(false);
    }
  }, [t]);

  const handleViewLog = async (filename: string) => {
    try {
      const result = await getLogFileContent(filename);
      setCurrentLogFilename(filename);
      setCurrentLogContent(result.content);
      setLogContentVisible(true);
    } catch {
      message.error(t('settings.saveFailed'));
    }
  };

  const handleDeleteLog = useCallback(async (filename: string) => {
    try {
      await deleteLogFile(filename);
      message.success(t('settings.deleteSuccess'));
      fetchLogFiles();
    } catch {
      message.error(t('settings.saveFailed'));
    }
  }, [fetchLogFiles, t]);

  const handleClearAllLogs = useCallback(async () => {
    try {
      await clearAllLogs();
      message.success(t('settings.saved'));
      fetchLogFiles();
    } catch {
      message.error(t('settings.saveFailed'));
    }
  }, [fetchLogFiles, t]);

  useEffect(() => {
    fetchCookiesFiles();
    fetchLogFiles();
  }, [fetchCookiesFiles, fetchLogFiles]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveConfig();
      message.success(t('settings.saved'));
    } catch {
      message.error(t('settings.saveFailed'));
    } finally {
      setSaving(false);
    }
  };

  const handleCheckUpdate = async () => {
    setUpdating(true);
    try {
      const result = await updateYtdlp();
      if (result.success) {
        message.success(t('settings.updated', { version: result.version || '' }));
        await fetchConfig();
      } else {
        message.error(t('settings.updateFailed', { error: result.error || '' }));
      }
    } catch {
      message.error(t('settings.saveFailed'));
    } finally {
      setUpdating(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!file.name.endsWith('.txt')) {
      message.error(t('settings.uploadFailed'));
      return;
    }
    
    setUploading(true);
    try {
      await uploadCookiesFile(file);
      message.success(t('settings.uploadSuccess'));
    } catch {
      message.error(t('settings.uploadFailed'));
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteCookies = async (filename: string) => {
    try {
      await removeCookiesFile(filename);
      message.success(t('settings.deleteSuccess'));
    } catch {
      message.error(t('settings.saveFailed'));
    }
  };

  const handleLanguageChange = (value: string) => {
    setLocale(value as Locale);
    // Trigger save via the store's language field
    useStore.getState().language = value;
  };

  return (
    <Fragment>
      <Drawer
        title={`${t('settings.logFile')}: ${currentLogFilename}`}
        placement="right"
        onClose={() => setLogContentVisible(false)}
        open={logContentVisible}
        width={800}
      >
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0, maxHeight: '600px', overflowY: 'auto' }}>
          {currentLogContent}
        </pre>
      </Drawer>
      <Card>
      <Title level={4}>{t('settings.title')}</Title>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text strong>{t('settings.downloadDir')}:</Text>
          <Text style={{ marginLeft: 8 }}>/downloads</Text>
        </div>
        <div>
          <Text strong>{t('settings.configDir')}:</Text>
          <Text style={{ marginLeft: 8 }}>./config</Text>
        </div>
        <div>
          <Text strong>{t('settings.port')}:</Text>
          <Text style={{ marginLeft: 8 }}>58888</Text>
        </div>
        <Divider style={{ margin: '16px 0' }} />

        {/* Language Selector */}
        <div>
          <Text strong>{t('settings.language')}:</Text>
          <div style={{ marginTop: 8 }}>
            <Segmented
              value={locale}
              onChange={handleLanguageChange}
              options={[
                { label: 'English', value: 'en' },
                { label: '中文', value: 'zh' },
              ]}
            />
          </div>
        </div>
        <Divider style={{ margin: '16px 0' }} />

        <div>
          <Text strong>{t('settings.defaultFormat')}:</Text>
          <div style={{ marginTop: 8 }}>
            <Segmented
              value={pendingFormat}
              onChange={(value) => setPendingFormat(value as 'mp4' | 'mkv')}
              options={[
                { label: 'MP4', value: 'mp4' },
                { label: 'MKV', value: 'mkv' },
              ]}
            />
          </div>
        </div>
        <Divider style={{ margin: '16px 0' }} />
        <div>
          <Text strong>{t('settings.ytdlpVersion')}:</Text>
          <div style={{ marginTop: 8 }}>
            <Segmented
              value={pendingYtdlpVersion}
              onChange={(value) => setPendingYtdlpVersion(value as 'stable' | 'nightly')}
              options={[
                { label: 'Stable', value: 'stable' },
                { label: 'Nightly', value: 'nightly' },
              ]}
            />
          </div>
          <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
            <Text type="secondary">
              {t('settings.currentVersion')}: <Text code>{ytdlpCurrentVersion || t('settings.loading')}</Text>
            </Text>
            <Button 
              icon={<SyncOutlined spin={updating} />} 
              onClick={handleCheckUpdate}
              loading={updating}
              size="small"
            >
              {t('settings.checkUpdate')}
            </Button>
          </div>
          <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 12 }}>
            {pendingYtdlpVersion === 'nightly' 
              ? t('settings.nightlyHint')
              : t('settings.stableHint')}
          </Text>
        </div>
        <Divider style={{ margin: '16px 0' }} />
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Text strong>{t('settings.useCookies')}:</Text>
            <Switch
              checked={pendingCookiesEnabled}
              onChange={(checked) => setPendingCookiesEnabled(checked)}
            />
          </div>
          <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 12 }}>
            {t('settings.cookiesHint')}
          </Text>
          
          {pendingCookiesEnabled && (
            <div style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Text strong>{t('settings.cookiesFiles')}:</Text>
                <input
                  ref={fileInputRef as any}
                  type="file"
                  accept=".txt"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
                <Button
                  icon={<UploadOutlined />}
                  loading={uploading}
                  onClick={() => fileInputRef.current?.click()}
                  size="small"
                >
                  {t('settings.upload')}
                </Button>
              </div>
              <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
                {t('settings.cookiesNameHint')}
              </Text>
              
              {cookiesFiles.length > 0 ? (
                <List
                  size="small"
                  dataSource={cookiesFiles}
                  renderItem={(item) => (
                    <List.Item
                      actions={[
                        <Popconfirm
                          key="delete"
                          title={t('settings.deleteFileConfirm')}
                          onConfirm={() => handleDeleteCookies(item.name)}
                          okText={t('common.yes')}
                          cancelText={t('common.no')}
                        >
                          <Button danger icon={<DeleteOutlined />} size="small" />
                        </Popconfirm>
                      ]}
                    >
                      <List.Item.Meta
                        avatar={<FileTextOutlined style={{ fontSize: 18 }} />}
                        title={item.name}
                        description={`${formatFileSize(item.size)} • ${t('settings.modified')}: ${new Date(item.modified * 1000).toLocaleDateString()}`}
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Text type="secondary">{t('settings.noCookies')}</Text>
              )}
            </div>
          )}
        </div>
        <Divider style={{ margin: '16px 0' }} />
        <div>
          <Text strong>{t('settings.logLevel')}:</Text>
          <div style={{ marginTop: 8 }}>
            <Segmented
              value={pendingLogLevel}
              onChange={(value) => setPendingLogLevel(value as string)}
              options={[
                { label: 'Debug', value: 'debug' },
                { label: 'Verbose', value: 'verbose' },
                { label: 'Info', value: 'info' },
                { label: 'Warn', value: 'warn' },
                { label: 'Error', value: 'error' },
              ]}
            />
          </div>
          <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 12 }}>
            {t('settings.logLevelHint')}
          </Text>
        </div>
        <div style={{ marginTop: 16 }}>
          <Space>
            <Text strong>{t('settings.logFiles')}:</Text>
            <Popconfirm
              title={t('settings.clearAllConfirm')}
              onConfirm={handleClearAllLogs}
              okText={t('common.yes')}
              cancelText={t('common.no')}
            >
              <Button 
                size="small" 
                danger 
                icon={<DeleteOutlined />}
                disabled={logFiles.length === 0 || logFilesLoading}
              >
                {t('settings.clearAll')}
              </Button>
            </Popconfirm>
          </Space>
          <div style={{ marginTop: 8 }}>
            {logFilesLoading ? (
              <Text type="secondary">{t('settings.loading')}</Text>
            ) : logFiles.length > 0 ? (
              <List
                size="small"
                dataSource={logFiles}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button 
                        key="view" 
                        size="small" 
                        icon={<EyeOutlined />}
                        onClick={() => handleViewLog(item.name)}
                      >
                        {t('settings.view')}
                      </Button>,
                      <Popconfirm
                        key="delete"
                        title={t('settings.deleteFileConfirm')}
                        onConfirm={() => handleDeleteLog(item.name)}
                        okText={t('common.yes')}
                        cancelText={t('common.no')}
                      >
                        <Button key="delete" danger size="small" icon={<DeleteOutlined />}>
                          {t('settings.delete')}
                        </Button>
                      </Popconfirm>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<FileTextOutlined style={{ fontSize: 18 }} />}
                      title={item.name}
                      description={`${formatFileSize(item.size)} • ${new Date(item.modified * 1000).toLocaleString()}`}
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Text type="secondary">{t('settings.noLogFiles')}</Text>
            )}
          </div>
        </div>
        <Divider style={{ margin: '16px 0' }} />
        <Button
          type="primary"
          icon={<SaveOutlined />}
          onClick={handleSave}
          loading={saving}
          disabled={!hasPendingChanges}
          size="large"
        >
          {t('settings.saveSettings')}
        </Button>
        {hasPendingChanges && (
          <Text type="warning" style={{ display: 'block' }}>
            {t('settings.unsavedChanges')}
          </Text>
        )}
      </Space>
    </Card>
    </Fragment>
  );
}