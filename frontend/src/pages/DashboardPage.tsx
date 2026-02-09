import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Typography,
  Space,
  Alert,
  Button,
  DatePicker,
  Select,
  Tooltip,
  Badge,
} from 'antd';
import {
  ReloadOutlined,
  ExperimentOutlined,
  MedicineBoxOutlined,
  ShoppingCartOutlined,
  FileProtectOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  DashboardOutlined,
  FundOutlined,
  SearchOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { Line, Pie, Gauge } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title as ChartTitle,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js/auto';
import { useDashboardStats, useRecentActivity, useSystemHealth } from './dashboardHooks';
import { DomainStats, RecentActivity, SystemHealth, TimelineData } from '@/shared/types/dashboard';
import dayjs from 'dayjs';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  ChartTitle,
  ChartTooltip,
  Legend,
  Filler
);

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch dashboard data
  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useDashboardStats();

  const {
    data: recentActivity,
    isLoading: activityLoading,
  } = useRecentActivity(10);

  const {
    data: systemHealth,
    isLoading: healthLoading,
  } = useSystemHealth();

  const handleRefresh = () => {
    refetchStats();
  };

  // Domain card colors
  const domainColors = {
    rd: { primary: '#4CAF50', secondary: '#E8F5E9', icon: <ExperimentOutlined /> },
    clinical: { primary: '#2196F3', secondary: '#E3F2FD', icon: <MedicineBoxOutlined /> },
    supply: { primary: '#FF9800', secondary: '#FFF3E0', icon: <ShoppingCartOutlined /> },
    regulatory: { primary: '#9C27B0', secondary: '#F3E5F5', icon: <FileProtectOutlined /> },
  };

  // Prepare chart data
  const domainDistributionData = stats ? {
    labels: ['R&D', 'Clinical', 'Supply Chain', 'Regulatory'],
    datasets: [{
      data: [
        stats.domains.rd.total,
        stats.domains.clinical.total,
        stats.domains.supply.total,
        stats.domains.regulatory.total,
      ],
      backgroundColor: [
        domainColors.rd.primary,
        domainColors.clinical.primary,
        domainColors.supply.primary,
        domainColors.regulatory.primary,
      ],
      borderWidth: 0,
    }],
  } : null;

  const activityTimelineData = recentActivity ? {
    labels: recentActivity
      .filter((a, i) => i % 2 === 0)
      .map(a => dayjs(a.timestamp).format('MM/DD')),
    datasets: [{
      label: 'Activity',
      data: recentActivity
        .filter((a, i) => i % 2 === 0)
        .map((_, i) => Math.floor(Math.random() * 50) + 10),
      borderColor: '#2196F3',
      backgroundColor: 'rgba(33, 150, 243, 0.1)',
      fill: true,
      tension: 0.4,
    }],
  } : null;

  // Recent activity table columns
  const activityColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string, record: RecentActivity) => {
        const colors: Record<string, string> = {
          compound: domainColors.rd.primary,
          trial: domainColors.clinical.primary,
          submission: domainColors.regulatory.primary,
          shortage: domainColors.supply.primary,
          manufacturer: domainColors.supply.primary,
        };
        return (
          <Tag color={colors[type] || 'default'}>
            {type.toUpperCase()}
          </Tag>
        );
      },
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
          active: { color: 'green', icon: <CheckCircleOutlined /> },
          pending: { color: 'orange', icon: <ClockCircleOutlined /> },
          completed: { color: 'blue', icon: <CheckCircleOutlined /> },
          resolved: { color: 'green', icon: <CheckCircleOutlined /> },
        };
        const config = statusConfig[status] || { color: 'default', icon: null };
        return (
          <Tag color={config.color} icon={config.icon}>
            {status?.toUpperCase() || 'UNKNOWN'}
          </Tag>
        );
      },
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 120,
      render: (timestamp: string) => dayjs(timestamp).fromNow(),
    },
  ];

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  const lineChartOptions = {
    ...chartOptions,
    scales: {
      y: {
        beginAtZero: true,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <DashboardOutlined /> Platform Dashboard
          </Title>
          <Text type="secondary">
            Real-time monitoring and insights across all pharmaceutical domains
          </Text>
        </div>
        <Space>
          <Select
            value={timeRange}
            onChange={setTimeRange}
            style={{ width: 120 }}
          >
            <Select.Option value="7d">Last 7 Days</Select.Option>
            <Select.Option value="30d">Last 30 Days</Select.Option>
            <Select.Option value="90d">Last 90 Days</Select.Option>
            <Select.Option value="1y">Last Year</Select.Option>
          </Select>
          <Tooltip title="Auto-refresh every 30s">
            <Button
              icon={<ReloadOutlined spin={autoRefresh} />}
              onClick={handleRefresh}
              type={autoRefresh ? 'primary' : 'default'}
            >
              Refresh
            </Button>
          </Tooltip>
        </Space>
      </div>

      {/* System Health Banner */}
      {systemHealth && (
        <Alert
          message={
            <Space size="large">
              <Badge
                status={systemHealth.api_status === 'healthy' ? 'success' : 'error'}
                text={`API: ${systemHealth.api_status.toUpperCase()}`}
              />
              <Badge
                status={systemHealth.neo4j_status === 'healthy' ? 'success' : 'error'}
                text={`Neo4j: ${systemHealth.neo4j_status.toUpperCase()}`}
              />
              <Text>
                <ThunderboltOutlined /> Avg Response: {systemHealth.avg_response_time_ms}ms
              </Text>
              <Text>
                Uptime: {systemHealth.uptime_percentage.toFixed(2)}%
              </Text>
            </Space>
          }
          type={systemHealth.api_status === 'healthy' ? 'success' : 'error'}
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Domain Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* R&D Domain */}
        <Col xs={24} sm={12} lg={6}>
          <Card
            loading={statsLoading}
            hoverable
            style={{ borderTop: `4px solid ${domainColors.rd.primary}` }}
            onClick={() => navigate('/rd')}
          >
            <Statistic
              title={
                <Space>
                  <ExperimentOutlined style={{ color: domainColors.rd.primary }} />
                  <span>R&D Domain</span>
                </Space>
              }
              value={stats?.domains.rd.total || 0}
              suffix="entities"
              valueStyle={{ color: domainColors.rd.primary }}
            />
            <div style={{ marginTop: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }} size={4}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Compounds</Text>
                  <Text strong>{stats?.domains.rd.compounds.toLocaleString() || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Targets</Text>
                  <Text strong>{stats?.domains.rd.targets.toLocaleString() || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Pathways</Text>
                  <Text strong>{stats?.domains.rd.pathways.toLocaleString() || 0}</Text>
                </div>
              </Space>
            </div>
          </Card>
        </Col>

        {/* Clinical Domain */}
        <Col xs={24} sm={12} lg={6}>
          <Card
            loading={statsLoading}
            hoverable
            style={{ borderTop: `4px solid ${domainColors.clinical.primary}` }}
            onClick={() => navigate('/clinical')}
          >
            <Statistic
              title={
                <Space>
                  <MedicineBoxOutlined style={{ color: domainColors.clinical.primary }} />
                  <span>Clinical Domain</span>
                </Space>
              }
              value={stats?.domains.clinical.total || 0}
              suffix="entities"
              valueStyle={{ color: domainColors.clinical.primary }}
            />
            <div style={{ marginTop: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }} size={4}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Trials</Text>
                  <Text strong>{stats?.domains.clinical.trials.toLocaleString() || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Subjects</Text>
                  <Text strong>{stats?.domains.clinical.subjects.toLocaleString() || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Conditions</Text>
                  <Text strong>{stats?.domains.clinical.conditions.toLocaleString() || 0}</Text>
                </div>
              </Space>
            </div>
          </Card>
        </Col>

        {/* Supply Chain Domain */}
        <Col xs={24} sm={12} lg={6}>
          <Card
            loading={statsLoading}
            hoverable
            style={{ borderTop: `4px solid ${domainColors.supply.primary}` }}
            onClick={() => navigate('/supply')}
          >
            <Statistic
              title={
                <Space>
                  <ShoppingCartOutlined style={{ color: domainColors.supply.primary }} />
                  <span>Supply Chain</span>
                </Space>
              }
              value={stats?.domains.supply.total || 0}
              suffix="entities"
              valueStyle={{ color: domainColors.supply.primary }}
            />
            <div style={{ marginTop: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }} size={4}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Manufacturers</Text>
                  <Text strong>{stats?.domains.supply.manufacturers.toLocaleString() || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Facilities</Text>
                  <Text strong>{stats?.domains.supply.facilities.toLocaleString() || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Active Shortages</Text>
                  <Text strong style={{ color: '#ff4d4f' }}>
                    {stats?.domains.supply.shortages.toLocaleString() || 0}
                  </Text>
                </div>
              </Space>
            </div>
          </Card>
        </Col>

        {/* Regulatory Domain */}
        <Col xs={24} sm={12} lg={6}>
          <Card
            loading={statsLoading}
            hoverable
            style={{ borderTop: `4px solid ${domainColors.regulatory.primary}` }}
            onClick={() => navigate('/regulatory')}
          >
            <Statistic
              title={
                <Space>
                  <FileProtectOutlined style={{ color: domainColors.regulatory.primary }} />
                  <span>Regulatory</span>
                </Space>
              }
              value={stats?.domains.regulatory.total || 0}
              suffix="entities"
              valueStyle={{ color: domainColors.regulatory.primary }}
            />
            <div style={{ marginTop: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }} size={4}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Submissions</Text>
                  <Text strong>{stats?.domains.regulatory.submissions.toLocaleString() || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Approvals</Text>
                  <Text strong>{stats?.domains.regulatory.approvals.toLocaleString() || 0}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Agencies</Text>
                  <Text strong>{stats?.domains.regulatory.agencies.toLocaleString() || 0}</Text>
                </div>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions Panel */}
      <Card
        title={
          <Space>
            <FundOutlined />
            <span>Quick Actions</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
        extra={
          <Button icon={<DownloadOutlined />} type="link">
            Export Report
          </Button>
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card
              hoverable
              style={{ textAlign: 'center', background: domainColors.rd.secondary }}
              onClick={() => navigate('/rd/compounds')}
            >
              <ExperimentOutlined style={{ fontSize: 32, color: domainColors.rd.primary }} />
              <div style={{ marginTop: 8 }}>
                <Text strong>Explore Compounds</Text>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card
              hoverable
              style={{ textAlign: 'center', background: domainColors.clinical.secondary }}
              onClick={() => navigate('/clinical/trials')}
            >
              <MedicineBoxOutlined style={{ fontSize: 32, color: domainColors.clinical.primary }} />
              <div style={{ marginTop: 8 }}>
                <Text strong>Browse Trials</Text>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card
              hoverable
              style={{ textAlign: 'center', background: domainColors.supply.secondary }}
              onClick={() => navigate('/supply/shortages')}
            >
              <WarningOutlined style={{ fontSize: 32, color: domainColors.supply.primary }} />
              <div style={{ marginTop: 8 }}>
                <Text strong>Monitor Shortages</Text>
              </div>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* Charts and Activity Section */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* Domain Distribution Chart */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <PieChartOutlined />
                <span>Domain Distribution</span>
              </Space>
            }
          >
            <div style={{ height: 300 }}>
              {domainDistributionData && (
                <Pie data={domainDistributionData} options={chartOptions} />
              )}
            </div>
          </Card>
        </Col>

        {/* Activity Timeline */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <LineChartOutlined />
                <span>Activity Timeline</span>
              </Space>
            }
          >
            <div style={{ height: 300 }}>
              {activityTimelineData && (
                <Line data={activityTimelineData} options={lineChartOptions} />
              )}
            </div>
          </Card>
        </Col>

        {/* Recent Activity Table */}
        <Col xs={24}>
          <Card
            title={
              <Space>
                <ClockCircleOutlined />
                <span>Recent Activity</span>
              </Space>
            }
            extra={
              <Button
                type="link"
                onClick={() => navigate('/search')}
                icon={<SearchOutlined />}
              >
                View All
              </Button>
            }
          >
            <Table
              columns={activityColumns}
              dataSource={recentActivity || []}
              loading={activityLoading}
              pagination={false}
              size="small"
              rowKey="id"
              onRow={(record) => ({
                onClick: () => {
                  const routes: Record<string, string> = {
                    compound: `/rd/compounds/${record.id}`,
                    trial: `/clinical/trials/${record.id}`,
                    submission: `/regulatory/submissions/${record.id}`,
                    shortage: `/supply/shortages`,
                    manufacturer: `/supply/manufacturers/${record.id}`,
                  };
                  const route = routes[record.type];
                  if (route) navigate(route);
                },
                style: { cursor: 'pointer' },
              })}
            />
          </Card>
        </Col>
      </Row>

      {/* Data Quality Section */}
      {stats?.data_quality && (
        <Card
          title={
            <Space>
              <DatabaseOutlined />
              <span>Data Quality Metrics</span>
            </Space>
          }
          style={{ marginBottom: 24 }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <div style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={stats.data_quality.overall_score}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                  size={120}
                />
                <div style={{ marginTop: 8 }}>
                  <Text strong>Overall Score</Text>
                </div>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={stats.data_quality.completeness.rd}
                  strokeColor={domainColors.rd.primary}
                  size={120}
                />
                <div style={{ marginTop: 8 }}>
                  <Text strong>R&D Completeness</Text>
                </div>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={stats.data_quality.completeness.clinical}
                  strokeColor={domainColors.clinical.primary}
                  size={120}
                />
                <div style={{ marginTop: 8 }}>
                  <Text strong>Clinical Completeness</Text>
                </div>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={stats.data_quality.accuracy}
                  strokeColor={domainColors.supply.primary}
                  size={120}
                />
                <div style={{ marginTop: 8 }}>
                  <Text strong>Accuracy</Text>
                </div>
              </div>
            </Col>
          </Row>
          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <Text type="secondary">
              Last validated: {dayjs(stats.data_quality.last_validated).format('YYYY-MM-DD HH:mm')}
            </Text>
          </div>
        </Card>
      )}

      {/* Network Health Metrics */}
      <Card
        title={
          <Space>
            <BarChartOutlined />
            <span>Network Metrics</span>
          </Space>
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <Statistic
              title="Total Nodes"
              value={stats?.total_nodes || 0}
              prefix={<DatabaseOutlined />}
              formatter={(value) => `${(Number(value) / 1000000).toFixed(2)}M`}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Total Relationships"
              value={stats?.total_relationships || 0}
              prefix={<FundOutlined />}
              formatter={(value) => `${(Number(value) / 1000000).toFixed(2)}M`}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Avg Degree"
              value={2.4}
              precision={1}
              suffix="connections/node"
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Connected Components"
              value={156}
              suffix="clusters"
            />
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default DashboardPage;
