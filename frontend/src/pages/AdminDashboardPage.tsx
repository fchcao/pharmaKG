import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Typography,
  Space,
  Alert,
  Button,
  Progress,
  Timeline,
  Descriptions,
  Badge,
  Tabs,
  List,
} from 'antd';
import {
  ReloadOutlined,
  ServerOutlined,
  DatabaseOutlined,
  ApiOutlined,
  ClusterOutlined,
  BugOutlined,
  SafetyOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  SettingOutlined,
  MonitorOutlined,
  ThunderboltOutlined,
  HeatMapOutlined,
} from '@ant-design/icons';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title as ChartTitle,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js/auto';
import { useSystemAlerts, useTimelineData } from './dashboardHooks';
import { SystemAlert } from '@/shared/types/dashboard';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ChartTitle,
  ChartTooltip,
  Legend,
  Filler
);

const AdminDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);

  const { data: alerts, isLoading: alertsLoading } = useSystemAlerts();
  const { data: timelineData } = useTimelineData();

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate refresh
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  // Mock performance data
  const performanceData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'],
    datasets: [
      {
        label: 'API Response Time (ms)',
        data: [45, 52, 48, 65, 58, 50, 47],
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Neo4j Query Time (ms)',
        data: [120, 135, 125, 180, 160, 140, 130],
        borderColor: '#4CAF50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Mock throughput data
  const throughputData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'Requests per Hour',
      data: [1250, 1480, 1320, 1650, 1520, 980, 890],
      backgroundColor: '#FF9800',
      borderRadius: 4,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  // Alerts table columns
  const alertColumns = [
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => {
        const config = {
          critical: { color: 'error', icon: <CloseCircleOutlined /> },
          error: { color: 'error', icon: <CloseCircleOutlined /> },
          warning: { color: 'warning', icon: <WarningOutlined /> },
          info: { color: 'processing', icon: <MonitorOutlined /> },
        };
        const { color, icon } = config[severity as keyof typeof config] || config.info;
        return <Tag color={color} icon={icon}>{severity.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => dayjs(timestamp).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Status',
      dataIndex: 'resolved',
      key: 'resolved',
      width: 100,
      render: (resolved: boolean) => (
        <Badge
          status={resolved ? 'success' : 'error'}
          text={resolved ? 'Resolved' : 'Active'}
        />
      ),
    },
  ];

  // System metrics
  const systemMetrics = [
    {
      title: 'CPU Usage',
      value: 45,
      suffix: '%',
      status: 'normal' as const,
      icon: <ServerOutlined />,
    },
    {
      title: 'Memory Usage',
      value: 68,
      suffix: '%',
      status: 'normal' as const,
      icon: <DatabaseOutlined />,
    },
    {
      title: 'Disk Usage',
      value: 72,
      suffix: '%',
      status: 'warning' as const,
      icon: <ClusterOutlined />,
    },
    {
      title: 'Network I/O',
      value: 23,
      suffix: 'MB/s',
      status: 'normal' as const,
      icon: <ApiOutlined />,
    },
  ];

  // Recent system events
  const systemEvents = [
    {
      time: '5 mins ago',
      title: 'Data ingestion completed',
      description: 'ChEMBL batch import: 10,000 compounds processed',
      status: 'success',
    },
    {
      time: '15 mins ago',
      title: 'Index rebuild completed',
      description: 'Neo4j index optimization finished',
      status: 'success',
    },
    {
      time: '1 hour ago',
      title: 'High memory usage detected',
      description: 'Memory usage exceeded 80% threshold',
      status: 'warning',
    },
    {
      time: '2 hours ago',
      title: 'API rate limit triggered',
      description: 'IP 192.168.1.100 exceeded request limit',
      status: 'error',
    },
    {
      time: '3 hours ago',
      title: 'Backup completed',
      description: 'Daily database backup successful',
      status: 'success',
    },
  ];

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <SettingOutlined /> Admin Dashboard
          </Title>
          <Text type="secondary">
            System monitoring, performance metrics, and administrative controls
          </Text>
        </div>
        <Button
          icon={<ReloadOutlined spin={refreshing} />}
          onClick={handleRefresh}
          loading={refreshing}
        >
          Refresh
        </Button>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Overview" key="overview">
          {/* System Status Banner */}
          <Alert
            message="System Operational"
            description="All services are running normally. No critical issues detected."
            type="success"
            showIcon
            style={{ marginBottom: 24 }}
          />

          {/* System Metrics */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            {systemMetrics.map((metric) => (
              <Col xs={12} sm={6} key={metric.title}>
                <Card size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text type="secondary">
                      {metric.icon} {metric.title}
                    </Text>
                    <Progress
                      percent={metric.value}
                      status={metric.status === 'warning' ? 'exception' : 'active'}
                      strokeColor={
                        metric.status === 'warning' ? '#faad14' : '#52c41a'
                      }
                    />
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>

          {/* Performance Charts */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card
                title={
                  <Space>
                    <ThunderboltOutlined />
                    <span>Response Times</span>
                  </Space>
                }
              >
                <div style={{ height: 300 }}>
                  <Line data={performanceData} options={chartOptions} />
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card
                title={
                  <Space>
                    <HeatMapOutlined />
                    <span>Request Throughput</span>
                  </Space>
                }
              >
                <div style={{ height: 300 }}>
                  <Bar data={throughputData} options={chartOptions} />
                </div>
              </Card>
            </Col>
          </Row>

          {/* Quick Stats */}
          <Row gutter={[16, 16]}>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Active Connections"
                  value={156}
                  suffix="/ 1000"
                  prefix={<ApiOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Cache Hit Rate"
                  value={94.2}
                  suffix="%"
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Error Rate"
                  value={0.12}
                  suffix="%"
                  prefix={<BugOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Uptime"
                  value={99.95}
                  suffix="%"
                  prefix={<SafetyOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Alerts" key="alerts">
          <Card
            title={
              <Space>
                <WarningOutlined />
                <span>System Alerts</span>
              </Space>
            }
          >
            <Table
              columns={alertColumns}
              dataSource={alerts || []}
              loading={alertsLoading}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Card>
        </TabPane>

        <TabPane tab="Events" key="events">
          <Card
            title={
              <Space>
                <ClockCircleOutlined />
                <span>Recent System Events</span>
              </Space>
            }
          >
            <Timeline
              items={systemEvents.map((event) => ({
                color: event.status === 'success' ? 'green' : event.status === 'warning' ? 'orange' : 'red',
                children: (
                  <div>
                    <Text strong>{event.title}</Text>
                    <br />
                    <Text type="secondary">{event.description}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {event.time}
                    </Text>
                  </div>
                ),
              }))}
            />
          </Card>
        </TabPane>

        <TabPane tab="Configuration" key="config">
          <Card title="System Configuration">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="API Version">v1.0.0</Descriptions.Item>
              <Descriptions.Item label="Neo4j Version">5.x</Descriptions.Item>
              <Descriptions.Item label="Cache Provider">Redis</Descriptions.Item>
              <Descriptions.Item label="Cache TTL">3600s</Descriptions.Item>
              <Descriptions.Item label="Rate Limiting">Enabled</Descriptions.Item>
              <Descriptions.Item label="Max Requests/min">1000</Descriptions.Item>
              <Descriptions.Item label="Query Timeout">30s</Descriptions.Item>
              <Descriptions.Item label="Max Batch Size">1000</Descriptions.Item>
              <Descriptions.Item label="Index Optimization">Daily 2:00 AM</Descriptions.Item>
              <Descriptions.Item label="Data Validation">Enabled</Descriptions.Item>
              <Descriptions.Item label="Auto-refresh">30s</Descriptions.Item>
              <Descriptions.Item label="LogLevel">INFO</Descriptions.Item>
            </Descriptions>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default AdminDashboardPage;
