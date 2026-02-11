import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, theme } from 'antd';
import {
  HomeOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  MedicineBoxOutlined,
  ShoppingCartOutlined,
  FileProtectOutlined,
  SearchOutlined,
  SettingOutlined,
  BranchesOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

const { Header, Sider, Content } = Layout;

type MenuItem = Required<MenuProps>['items'][number];

const getItem = (
  label: React.ReactNode,
  key: React.Key,
  icon?: React.ReactNode,
  children?: MenuItem[],
  type?: 'group',
): MenuItem => {
  return {
    key,
    icon,
    children,
    label,
    type,
  } as MenuItem;
};

const items: MenuItem[] = [
  getItem('Home', '/', <HomeOutlined />),
  getItem('Dashboard', 'dashboard', <DashboardOutlined />, [
    getItem('Overview', '/dashboard', <DashboardOutlined />),
    getItem('Admin', '/dashboard/admin', <SettingOutlined />),
  ]),
  getItem('Domains', 'domains', <AppstoreOutlined />, [
    getItem('Research & Development', '/rd', <ExperimentOutlined />),
    getItem('Clinical Trials', '/clinical', <MedicineBoxOutlined />),
    getItem('Supply Chain', '/supply', <ShoppingCartOutlined />),
    getItem('Regulatory', '/regulatory', <FileProtectOutlined />),
  ]),
  getItem('Cross-Domain Queries', '/cross-domain', <BranchesOutlined />),
  getItem('Search', '/search', <SearchOutlined />),
  getItem('Settings', '/settings', <SettingOutlined />),
];

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  // Get the selected key based on current location
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path.startsWith('/rd')) return '/rd';
    if (path.startsWith('/clinical')) return '/clinical';
    if (path.startsWith('/supply')) return '/supply';
    if (path.startsWith('/regulatory')) return '/regulatory';
    if (path.startsWith('/cross-domain')) return '/cross-domain';
    if (path.startsWith('/dashboard')) return path;
    return path;
  };

  const selectedKey = getSelectedKey();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="light">
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <h1 style={{ margin: 0, fontSize: collapsed ? '16px' : '20px', fontWeight: 600 }}>
            {collapsed ? 'PK' : 'PharmaKG'}
          </h1>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={items}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer, borderBottom: '1px solid #f0f0f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
            <h2 style={{ margin: 0, fontSize: '18px' }}>
              Pharmaceutical Knowledge Graph
            </h2>
          </div>
        </Header>
        <Content style={{ margin: '24px' }}>
          <div
            style={{
              padding: 24,
              minHeight: '100%',
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
