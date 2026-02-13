import React, { useState, useEffect } from 'react';
import { Card, Switch, Typography, Space, Divider, Form, Select, Button, message, Row, Col, Layout } from 'antd';
import {
  SettingOutlined,
  UserOutlined,
  BgColorsOutlined,
  TranslationOutlined,
  BellOutlined,
  ApiOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Content } = Layout;

interface SettingsForm {
  theme: 'light' | 'dark';
  language: 'en' | 'zh';
  notifications: boolean;
  autoRefresh: boolean;
  apiBaseUrl: string;
  resultsPerPage: number;
}

const SettingsPage: React.FC = () => {
  // Load settings from localStorage on mount
  const [settings, setSettings] = useState<SettingsForm>(() => {
    const stored = localStorage.getItem('pharmakg_settings');
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return {
          theme: 'light',
          language: 'en',
          notifications: true,
          autoRefresh: false,
          apiBaseUrl: '/api',
          resultsPerPage: 20,
        };
      }
    }
    return {
      theme: 'light',
      language: 'en',
      notifications: true,
      autoRefresh: false,
      apiBaseUrl: '/api',
      resultsPerPage: 20,
    };
  });

  // Apply theme to document
  useEffect(() => {
    if (settings.theme === 'dark') {
      document.body.style.backgroundColor = '#141414';
      document.body.style.color = '#ffffff';
    } else {
      document.body.style.backgroundColor = '#f0f2f5';
      document.body.style.color = '#000000';
    }
  }, [settings.theme]);

  const handleSave = (values: SettingsForm) => {
    setSettings(values);
    localStorage.setItem('pharmakg_settings', JSON.stringify(values));
    message.success('Settings saved successfully');
  };

  const handleReset = () => {
    const defaultSettings: SettingsForm = {
      theme: 'light',
      language: 'en',
      notifications: true,
      autoRefresh: false,
      apiBaseUrl: '/api',
      resultsPerPage: 20,
    };
    setSettings(defaultSettings);
    localStorage.setItem('pharmakg_settings', JSON.stringify(defaultSettings));
    // Reset document theme
    document.body.style.backgroundColor = '#f0f2f5';
    document.body.style.color = '#000000';
    message.info('Settings reset to default');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px', background: settings.theme === 'dark' ? '#141414' : '#f0f2f5' }}>
        <Row gutter={[24]}>
          <Col span={24}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* Page Title */}
              <div style={{ marginBottom: 24 }}>
                <Title level={2} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <SettingOutlined style={{ fontSize: 24, color: settings.theme === 'dark' ? '#fff' : '#1890ff' }} />
                  Settings
                </Title>
                <Text type="secondary">
                  Manage your application preferences and configurations
                </Text>
              </div>

              {/* Appearance Card */}
              <Card title={<span style={{ fontSize: 16, fontWeight: 500 }}>Appearance</span>}>
                <Form
                  layout="vertical"
                  initialValues={settings}
                  onFinish={handleSave}
                >
                  <Form.Item
                    label="Theme"
                    name="theme"
                    tooltip="Choose your preferred color scheme"
                  >
                    <Select style={{ width: '100%' }}>
                      <Select.Option value="light">
                        <Space>
                          <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#fff', border: '1px solid #d9d9d9' } as React.CSSProperties}>
                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#faad14' }}></div>
                          </div>
                        </Space>
                        Light Mode
                      </Select.Option>
                      <Select.Option value="dark">
                        <Space>
                          <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#141414', display: 'flex', alignItems: 'center', justifyContent: 'center' } as React.CSSProperties}>
                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#722ed1' }}></div>
                          </div>
                        </Space>
                        Dark Mode
                      </Select.Option>
                    </Select>
                  </Form.Item>

                  <Form.Item
                    label="Language"
                    name="language"
                    tooltip="Select your preferred language"
                  >
                    <Select style={{ width: '100%' }}>
                      <Select.Option value="en">English</Select.Option>
                      <Select.Option value="zh">中文</Select.Option>
                    </Select>
                  </Form.Item>

                  <Form.Item
                    label="Results Per Page"
                    name="resultsPerPage"
                    tooltip="Number of results to show per page in search"
                  >
                    <Select style={{ width: '100%' }}>
                      <Select.Option value={10}>10</Select.Option>
                      <Select.Option value={20}>20</Select.Option>
                      <Select.Option value={50}>50</Select.Option>
                      <Select.Option value={100}>100</Select.Option>
                    </Select>
                  </Form.Item>
                </Form>
              </Card>

              {/* Notifications Card */}
              <Card title={<span style={{ fontSize: 16, fontWeight: 500 }}>Notifications</span>}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <Text strong>Push Notifications</Text>
                      <Text type="secondary">Receive alerts for important updates</Text>
                    </div>
                    <Switch
                      checked={settings.notifications}
                      onChange={(checked) => setSettings({ ...settings, notifications: checked })}
                    />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <Text strong>Email Notifications</Text>
                      <Text type="secondary">Receive updates via email</Text>
                    </div>
                    <Switch
                      checked={settings.notifications}
                      onChange={(checked) => setSettings({ ...settings, notifications: checked })}
                    />
                  </div>
                </Space>
              </Card>

              {/* API Configuration Card */}
              <Card title={<span style={{ fontSize: 16, fontWeight: 500 }}>API Configuration</span>}>
                <Form
                  layout="vertical"
                  initialValues={settings}
                  onFinish={handleSave}
                >
                  <Form.Item
                    label="API Base URL"
                    name="apiBaseUrl"
                    tooltip="Base URL for API requests (default: /api)"
                    rules={[{ required: true, message: 'Please enter API base URL' }]}
                  >
                    <Select style={{ width: '100%' }}>
                      <Select.Option value="/api">/api (Development)</Select.Option>
                      <Select.Option value="https://api.pharmakg.com">https://api.pharmakg.com (Production)</Select.Option>
                    </Select>
                  </Form.Item>

                  <Form.Item
                    label="Auto-refresh Results"
                    name="autoRefresh"
                    valuePropName="checked"
                    tooltip="Automatically refresh search results when filters change"
                  >
                    <Switch />
                  </Form.Item>
                </Form>
              </Card>

              {/* Data Management Card */}
              <Card title={<span style={{ fontSize: 16, fontWeight: 500 }}>Data Management</span>}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button
                    type="primary"
                    danger
                    icon={<DatabaseOutlined />}
                    onClick={handleReset}
                    style={{ width: '100%' }}
                  >
                    Reset Settings to Default
                  </Button>
                </Space>
              </Card>

              {/* Info Card */}
              <Card>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Current Configuration:</Text>
                  </div>
                  <Divider style={{ margin: '8px 0' }} />
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">Theme:</Text>
                      <Text code>{settings.theme === 'dark' ? 'Dark' : 'Light'}</Text>
                    </div>
                    <div>
                      <Text type="secondary">Language:</Text>
                      <Text code>{settings.language === 'en' ? 'English' : '中文'}</Text>
                    </div>
                    <div>
                      <Text type="secondary">Results Per Page:</Text>
                      <Text code>{settings.resultsPerPage}</Text>
                    </div>
                    <div>
                      <Text type="secondary">API Base URL:</Text>
                      <Text code>{settings.apiBaseUrl}</Text>
                    </div>
                    <div>
                      <Text type="secondary">Notifications:</Text>
                      <Text code>{settings.notifications ? 'Enabled' : 'Disabled'}</Text>
                    </div>
                  </Space>
                </Space>
              </Card>
            </Space>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default SettingsPage;