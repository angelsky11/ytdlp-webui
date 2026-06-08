import { useEffect, useRef } from 'react';
import { Badge } from 'antd';
import { useStore } from '../stores';
import { getWebSocketUrl } from '../api';
import { useLocale } from '../i18n';

export function WebSocketStatus() {
  const { wsConnected, setWsConnected } = useStore();
  const wsRef = useRef<WebSocket | null>(null);
  const { t } = useLocale();

  useEffect(() => {
    const wsUrl = getWebSocketUrl();
    
    if (!wsUrl) {
      setWsConnected(true);
      return;
    }

    const connect = () => {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onclose = () => {
        setWsConnected(false);
        setTimeout(connect, 3000);
      };

      ws.onerror = () => {};

      ws.onmessage = (event) => {
        try {
          const progress = JSON.parse(event.data);
          useStore.getState().updateDownload(progress);
        } catch {
          // ignore parse errors
        }
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      wsRef.current?.close();
    };
  }, [setWsConnected]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <Badge status={wsConnected ? 'success' : 'error'} />
      <span style={{ color: 'rgba(255,255,255,0.65)', fontSize: 13 }}>
        {wsConnected ? t('status.connected') : t('status.disconnected')}
      </span>
    </div>
  );
}