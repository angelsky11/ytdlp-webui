import { useState, useMemo, useEffect } from 'react';
import { Table, Progress, Tag, Button, Space, Modal, Popconfirm, message, Typography, Tooltip, Skeleton } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  StopOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  DeleteOutlined,
  WarningOutlined,
  CopyOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import { useStore } from '../stores';
import { DownloadStatus } from '../types';
import { useLocale } from '../i18n';
import type { DownloadProgress } from '../types';

const { Text } = Typography;

const statusColors: Record<string, string> = {
  [DownloadStatus.PENDING]: 'default',
  [DownloadStatus.DOWNLOADING]: 'processing',
  [DownloadStatus.COMPLETED]: 'success',
  [DownloadStatus.FAILED]: 'error',
  [DownloadStatus.CANCELLED]: 'warning',
};

const statusIcons: Record<string, React.ReactNode> = {
  [DownloadStatus.PENDING]: null,
  [DownloadStatus.DOWNLOADING]: <PlayCircleOutlined />,
  [DownloadStatus.COMPLETED]: <CheckCircleOutlined />,
  [DownloadStatus.FAILED]: <CloseCircleOutlined />,
  [DownloadStatus.CANCELLED]: <StopOutlined />,
};

function formatDate(ts?: number): string {
  if (!ts) return '-';
  const d = new Date(ts * 1000);
  return d.toLocaleString();
}

export function DownloadList() {
  const { downloads, fetchDownloads, cancelTask, removeTask, retryDownload, downloadsLoading } = useStore();
  const { t } = useLocale();
  const [errorModalVisible, setErrorModalVisible] = useState(false);
  const [currentError, setCurrentError] = useState('');
  const [currentTaskName, setCurrentTaskName] = useState('');

  // 组件挂载时刷新数据。初次加载时立即显示已有缓存（如果有）或骨架屏，
  // 数据返回后自动更新。切换页面再回来时，已有缓存可立即显示。
  useEffect(() => {
    fetchDownloads();
  }, [fetchDownloads]);

  const handleShowError = (error: string, taskName: string) => {
    setCurrentError(error);
    setCurrentTaskName(taskName);
    setErrorModalVisible(true);
  };

  const handleCloseErrorModal = () => {
    setErrorModalVisible(false);
    setCurrentError('');
    setCurrentTaskName('');
  };

  const handleCopyError = () => {
    navigator.clipboard.writeText(currentError).then(() => {
      message.success(t('tasks.copied'));
    }).catch(() => {
      message.error(t('tasks.copyFailed'));
    });
  };

  const handleRetryAllFailed = async () => {
    const failedTasks = downloads.filter(d => d.status === DownloadStatus.FAILED);
    if (failedTasks.length === 0) {
      message.info(t('tasks.noFailed'));
      return;
    }
    let successCount = 0;
    for (const task of failedTasks) {
      try {
        await retryDownload(task);
        successCount++;
      } catch {
        // ignore
      }
    }
    message.success(t('tasks.retried', { success: successCount, total: failedTasks.length }));
    fetchDownloads();
  };

  const handleClearCompleted = async () => {
    const completedTasks = downloads.filter(
      d => d.status === DownloadStatus.COMPLETED || d.status === DownloadStatus.CANCELLED
    );
    if (completedTasks.length === 0) {
      message.info(t('tasks.noCompleted'));
      return;
    }
    let successCount = 0;
    for (const task of completedTasks) {
      try {
        await removeTask(task.task_id);
        successCount++;
      } catch {
        // ignore
      }
    }
    message.success(t('tasks.cleared', { success: successCount, total: completedTasks.length }));
    fetchDownloads();
  };

  const statusLabel = (status: DownloadStatus) => {
    switch (status) {
      case DownloadStatus.PENDING: return t('tasks.pending');
      case DownloadStatus.DOWNLOADING: return t('tasks.downloading');
      case DownloadStatus.COMPLETED: return t('tasks.completed');
      case DownloadStatus.FAILED: return t('tasks.failed');
      case DownloadStatus.CANCELLED: return t('tasks.cancelled');
      default: return status;
    }
  };

  const columns: ColumnsType<DownloadProgress> = useMemo(() => [
    {
      title: t('tasks.createdAt'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      sorter: (a, b) => (a.created_at || 0) - (b.created_at || 0),
      defaultSortOrder: 'descend',
      render: (val: number) => (
        <Text style={{ fontSize: 13, color: '#888' }}>{formatDate(val)}</Text>
      ),
    },
    {
      title: t('tasks.title'),
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title: string, record: DownloadProgress) => {
        // 优先使用 title，作为 fallback 使用 filename 去掉后缀，再 fallback 使用 URL/task_id
        const displayName = title ||
          (record.filename
            ? record.filename.replace(/\.(mp4|mkv|webm|avi|mov|flv|mp3|m4a|ogg|wav)$/i, '')
            : (record.url || record.task_id));
        return (
          <Tooltip title={displayName}>
            <Text strong ellipsis>
              {displayName}
            </Text>
          </Tooltip>
        );
      },
    },
    {
      title: t('tasks.progress'),
      key: 'progress',
      width: 260,
      render: (_: unknown, record: DownloadProgress) => {
        if (record.status === DownloadStatus.PENDING) {
          return (
            <Space>
              <Tag color={statusColors[record.status]} icon={statusIcons[record.status]}>
                {statusLabel(record.status)}
              </Tag>
              <Text type="secondary" style={{ fontSize: 12 }}>{t('tasks.waitingQueue')}</Text>
            </Space>
          );
        }
        if (record.status === DownloadStatus.DOWNLOADING) {
          return (
            <div style={{ minWidth: 200 }}>
              <Space style={{ marginBottom: 4 }}>
                <Tag color={statusColors[record.status]} icon={statusIcons[record.status]}>
                  {statusLabel(record.status)}
                </Tag>
              </Space>
              <Progress
                percent={Math.round(record.progress)}
                size="small"
                status="active"
                format={(p) => `${p}%`}
              />
              <Space size="small" style={{ fontSize: 12, color: '#888', marginTop: 2 }}>
                {record.speed && <span>{t('tasks.speed')}: {record.speed}</span>}
                {record.eta && <span>{t('tasks.eta')}: {record.eta}</span>}
              </Space>
            </div>
          );
        }
        if (record.status === DownloadStatus.COMPLETED) {
          return (
            <Space>
              <Tag color={statusColors[record.status]} icon={statusIcons[record.status]}>
                {statusLabel(record.status)}
              </Tag>
              <Text style={{ color: '#52c41a' }}>100%</Text>
            </Space>
          );
        }
        if (record.status === DownloadStatus.FAILED) {
          return (
            <Space>
              <Tag color={statusColors[record.status]} icon={statusIcons[record.status]}>
                {statusLabel(record.status)}
              </Tag>
              <Button
                type="link"
                danger
                size="small"
                onClick={() => handleShowError(record.error || '', record.filename || record.task_id)}
                style={{ padding: 0, height: 'auto' }}
              >
                {t('tasks.viewError')}
              </Button>
            </Space>
          );
        }
        if (record.status === DownloadStatus.CANCELLED) {
          return (
            <Tag color={statusColors[record.status]} icon={statusIcons[record.status]}>
              {statusLabel(record.status)}
            </Tag>
          );
        }
        return <Text type="secondary">-</Text>;
      },
    },
    {
      title: t('tasks.actions'),
      key: 'actions',
      width: 180,
      render: (_: unknown, record: DownloadProgress) => {
        const items: React.ReactNode[] = [];

        if (record.status === DownloadStatus.DOWNLOADING) {
          items.push(
            <Popconfirm
              key="cancel"
              title={t('tasks.confirmCancel')}
              onConfirm={() => cancelTask(record.task_id)}
              okText={t('tasks.confirm')}
              cancelText={t('tasks.cancelBtn')}
            >
              <Tooltip title={t('tasks.cancel')}>
                <Button size="small" danger icon={<StopOutlined />} shape="circle" />
              </Tooltip>
            </Popconfirm>
          );
        }

        if (record.status === DownloadStatus.FAILED) {
          items.push(
            <Tooltip key="retry" title={t('tasks.retry')}>
              <Button size="small" icon={<ReloadOutlined />} shape="circle" onClick={() => retryDownload(record)} />
            </Tooltip>
          );
          items.push(
            <Popconfirm
              key="delete"
              title={t('tasks.confirmDelete')}
              onConfirm={() => removeTask(record.task_id)}
              okText={t('tasks.confirm')}
              cancelText={t('tasks.cancelBtn')}
            >
              <Tooltip title={t('tasks.delete')}>
                <Button size="small" danger icon={<DeleteOutlined />} shape="circle" />
              </Tooltip>
            </Popconfirm>
          );
          items.push(
            <Tooltip key="error" title={t('tasks.error')}>
              <Button
                size="small"
                icon={<WarningOutlined />}
                shape="circle"
                onClick={() => handleShowError(record.error || '', record.filename || record.task_id)}
              />
            </Tooltip>
          );
        }

        if (record.status === DownloadStatus.COMPLETED || record.status === DownloadStatus.CANCELLED || record.status === DownloadStatus.PENDING) {
          items.push(
            <Popconfirm
              key="delete"
              title={t('tasks.confirmDelete')}
              onConfirm={() => removeTask(record.task_id)}
              okText={t('tasks.confirm')}
              cancelText={t('tasks.cancelBtn')}
            >
              <Tooltip title={t('tasks.delete')}>
                <Button size="small" danger icon={<DeleteOutlined />} shape="circle" />
              </Tooltip>
            </Popconfirm>
          );
        }

        return (
          <Space size="small">
            {items}
          </Space>
        );
      },
    },
  ], [t, cancelTask, removeTask, retryDownload]);

  const hasFailed = downloads.some(d => d.status === DownloadStatus.FAILED);
  const hasCompleted = downloads.some(d => d.status === DownloadStatus.COMPLETED || d.status === DownloadStatus.CANCELLED);

  return (
    <>
      {(hasFailed || hasCompleted) && (
        <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {hasFailed && (
            <Button size="small" icon={<ReloadOutlined />} onClick={handleRetryAllFailed}>
              {t('tasks.retryAll')}
            </Button>
          )}
          {hasCompleted && (
            <Button size="small" icon={<DeleteOutlined />} onClick={handleClearCompleted}>
              {t('tasks.clearCompleted')}
            </Button>
          )}
        </div>
      )}

      {downloadsLoading && downloads.length === 0 ? (
        <Skeleton active paragraph={{ rows: 8 }} />
      ) : (
      <Table<DownloadProgress>
        dataSource={downloads}
        columns={columns}
        rowKey="task_id"
        pagination={{
          pageSize: 10,
          pageSizeOptions: [10, 20, 50],
          showSizeChanger: true,
          showTotal: (total) => t('tasks.totalItems', { total }),
        }}
        size="middle"
        scroll={{ x: 760 }}
      />

      )}

      <Modal
        title={`${t('tasks.errorDetails')} - ${currentTaskName}`}
        open={errorModalVisible}
        onCancel={handleCloseErrorModal}
        footer={[
          <Button key="copy" type="primary" icon={<CopyOutlined />} onClick={handleCopyError}>
            {t('tasks.copyToClipboard')}
          </Button>,
          <Button key="close" onClick={handleCloseErrorModal}>
            {t('tasks.close')}
          </Button>,
        ]}
      >
        <pre style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          maxHeight: '400px',
          overflowY: 'auto',
          background: '#f5f5f5',
          padding: 12,
          borderRadius: 4,
          fontSize: 13,
        }}>
          {currentError}
        </pre>
      </Modal>
    </>
  );
}