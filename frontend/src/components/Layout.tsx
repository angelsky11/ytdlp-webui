import { useState, useEffect } from 'react';
import { Layout as AntLayout, Menu, Button, Drawer } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { HomeOutlined, CheckSquareOutlined, DownloadOutlined, SettingOutlined, InfoCircleOutlined, MenuOutlined } from '@ant-design/icons';
import { WebSocketStatus } from './WebSocketStatus';
import { useLocale } from '../i18n';
import type { MenuProps } from 'antd';

const { Header, Sider, Content } = AntLayout;

export function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { t } = useLocale();

  const menuItems: MenuProps['items'] = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: t('nav.home'),
    },
    {
      key: '/tasks',
      icon: <CheckSquareOutlined />,
      label: t('nav.tasks'),
    },
    {
      key: '/downloads',
      icon: <DownloadOutlined />,
      label: t('nav.downloads'),
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: t('nav.settings'),
    },
    {
      key: '/about',
      icon: <InfoCircleOutlined />,
      label: t('nav.about'),
    },
  ];

  // Check if mobile
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (!mobile) {
        setDrawerVisible(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key);
    setDrawerVisible(false);
  };

  // Desktop layout
  const desktopLayout = (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          background: '#001529',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ color: 'white', marginRight: 16 }}
          />
          <div style={{ color: 'white', fontSize: 18, fontWeight: 'bold' }}>
            {t('app.title')}
          </div>
        </div>
        <WebSocketStatus />
      </Header>
      <AntLayout>
        <Sider
          width={200}
          collapsedWidth={80}
          collapsed={collapsed}
          style={{
            background: '#001529',
            position: 'sticky',
            top: 64,
            height: 'calc(100vh - 64px)',
            overflow: 'auto',
          }}
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            style={{
              height: '100%',
              borderRight: 0,
              background: '#001529',
            }}
            theme="dark"
          />
        </Sider>
        <Content style={{ padding: '24px 50px', background: '#f0f2f5', minHeight: 'calc(100vh - 64px)' }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );

  // Mobile layout with drawer
  const mobileLayout = (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          background: '#001529',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setDrawerVisible(true)}
            style={{ color: 'white', marginRight: 12 }}
          />
          <div style={{ color: 'white', fontSize: 16, fontWeight: 'bold' }}>
            {t('app.title')}
          </div>
        </div>
        <WebSocketStatus />
      </Header>
      <Content style={{ padding: 16, background: '#f0f2f5', minHeight: 'calc(100vh - 64px)' }}>
        <Outlet />
      </Content>
      <Drawer
        title={t('app.menu')}
        placement="left"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        styles={{ body: { padding: 0 } }}
        width={250}
      >
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ height: '100%', borderRight: 0 }}
        />
      </Drawer>
    </AntLayout>
  );

  return isMobile ? mobileLayout : desktopLayout;
}