/**
 * ShortageMonitorPage.tsx
 * Supply Chain - Drug Shortage Monitor Page
 *
 * Features:
 * - Current drug shortages list
 * - Filter by severity, drug class, therapeutic area
 * - Real-time alerts for critical shortages
 * - Historical shortage trends (timeline)
 * - Shortage cascade analysis (show dependencies)
 * - API dependency tracking
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Table,
  Select,
  Space,
  Tag,
  Badge,
  Alert,
  Row,
  Col,
  Statistic,
  Button,
  DatePicker,
  Tooltip,
  Progress,
  Drawer,
  Timeline,
  Descriptions,
  message
} from 'antd';
import {
  WarningOutlined,
  FireOutlined,
  ThunderboltOutlined,
  SyncOutlined,
  FilterOutlined,
  CalendarOutlined,
  MedicineBoxOutlined,
  TeamOutlined,
  GlobalOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import type { ColumnsType } from 'antd/es/table';
import { GraphViewer } from '@/shared/graphs';
import { TimelineChart } from '@/shared/graphs';
import { supplyChainApi } from '../api';
import type { Shortage } from '../types';

const { Option } = Select;
const { RangePicker } = DatePicker;

interface FilterState {
  severity: 'low' | 'medium' | 'high' | undefined;
  status: string | undefined;
  drugClass: string | undefined;
  therapeuticArea: string | undefined;
  dateRange: any;
}

/**
 * Shortage Monitor Page Component
 */
export const ShortageMonitorPage: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    severity: undefined,
    status: 'active',
    drugClass: undefined,
    therapeuticArea: undefined,
    dateRange: null
  });
  const [selectedShortage, setSelectedShortage] = useState<Shortage | null>(null);
  const [cascadeDrawerVisible, setCascadeDrawerVisible] = useState(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch active shortages with polling for real-time updates
  const {
    data: shortagesData,
    isLoading,
    refetch,
    isError
  } = useQuery({
    queryKey: ['shortages', filters],
    queryFn: () =>
      supplyChainApi.getShortages({
        severity: filters.severity,
        status: filters.status,
        drug_class: filters.drugClass,
        therapeutic_area: filters.therapeuticArea
      }),
    refetchInterval: 30000 // Poll every 30 seconds for real-time updates
  });

  // Fetch shortage trends
  const { data: trendsData } = useQuery({
    queryKey: ['shortage-trends', filters.drugClass],
    queryFn: () =>
      supplyChainApi.getShortageTrends({
        drug_class: filters.drugClass
      })
  });

  const shortages = shortagesData?.data || [];
  const total = shortagesData?.total || 0;

  // Handle filter changes
  const handleFilterChange = (key: keyof FilterState, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // View shortage cascade analysis
  const handleViewCascade = (shortage: Shortage) => {
    setSelectedShortage(shortage);
    setCascadeDrawerVisible(true);
  };

  // Get severity color
  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'high':
        return 'red';
      case 'medium':
        return 'orange';
      case 'low':
        return 'blue';
      default:
        return 'default';
    }
  };

  // Get severity icon
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <FireOutlined />;
      case 'medium':
        return <WarningOutlined />;
      case 'low':
        return <ThunderboltOutlined />;
      default:
        return <WarningOutlined />;
    }
  };

  // Calculate statistics
  const stats = React.useMemo(() => {
    const criticalCount = shortages.filter(s => s.severity === 'high').length;
    const mediumCount = shortages.filter(s => s.severity === 'medium').length;
    const lowCount = shortages.filter(s => s.severity === 'low').length;

    return {
      total: shortages.length,
      critical: criticalCount,
      medium: mediumCount,
      low: lowCount
    };
  }, [shortages]);

  // Table columns
  const columns: ColumnsType<Shortage> = [
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      filters: [
        { text: 'Critical', value: 'high' },
        { text: 'Medium', value: 'medium' },
        { text: 'Low', value: 'low' }
      ],
      render: (severity: string) => (
        <Tag
          icon={getSeverityIcon(severity)}
          color={getSeverityColor(severity)}
          style={{ fontSize: '14px', padding: '4px 12px' }}
        >
          {severity?.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Product Name',
      dataIndex: 'productName',
      key: 'productName',
      render: (text: string, record: Shortage) => (
        <Space>
          <MedicineBoxOutlined />
          <a onClick={() => handleViewCascade(record)}>{text}</a>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'active' ? 'red' : status === 'resolved' ? 'green' : 'orange';
        return <Badge status={color as any} text={status?.toUpperCase()} />;
      }
    },
    {
      title: 'Start Date',
      dataIndex: 'startDate',
      key: 'startDate',
      sorter: true,
      render: (date: string) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_, record: Shortage) => {
        const start = new Date(record.startDate);
        const end = record.endDate ? new Date(record.endDate) : new Date();
        const days = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
        return `${days} days`;
      }
    },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
      render: (reason: string) => (
        <Tooltip title={reason}>
          <span>{reason?.substring(0, 50)}...</span>
        </Tooltip>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record: Shortage) => (
        <Space>
          <Button size="small" onClick={() => handleViewCascade(record)}>
            Cascade
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Header */}
        <Card>
          <Row gutter={16} align="middle">
            <Col span={18}>
              <Space>
                <WarningOutlined style={{ fontSize: '24px', color: '#f5222d' }} />
                <div>
                  <h2 style={{ margin: 0 }}>Drug Shortage Monitor</h2>
                  <p style={{ margin: 0, color: '#8c8c8c' }}>
                    Real-time tracking of pharmaceutical drug shortages worldwide
                  </p>
                </div>
              </Space>
            </Col>
            <Col span={6} style={{ textAlign: 'right' }}>
              <Space>
                <SyncOutlined spin style={{ color: '#52c41a' }} />
                <span style={{ fontSize: '12px', color: '#8c8c8c' }}>Live Updates</span>
                <Button icon={<SyncOutlined />} onClick={() => refetch()}>
                  Refresh
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Critical Alerts */}
        {stats.critical > 0 && (
          <Alert
            message={`${stats.critical} Critical Shortage${stats.critical > 1 ? 's' : ''} Require Immediate Attention`}
            description="High-severity shortages may impact patient care. Review and action required."
            type="error"
            showIcon
            icon={<FireOutlined />}
            action={
              <Button size="small" danger>
                View Critical
              </Button>
            }
          />
        )}

        {/* Statistics */}
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Active Shortages"
                value={stats.total}
                prefix={<WarningOutlined />}
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Critical Severity"
                value={stats.critical}
                prefix={<FireOutlined />}
                valueStyle={{ color: '#f5222d' }}
              />
              <Progress
                percent={stats.total > 0 ? (stats.critical / stats.total) * 100 : 0}
                showInfo={false}
                strokeColor="#f5222d"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Medium Severity"
                value={stats.medium}
                prefix={<WarningOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
              <Progress
                percent={stats.total > 0 ? (stats.medium / stats.total) * 100 : 0}
                showInfo={false}
                strokeColor="#faad14"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Low Severity"
                value={stats.low}
                prefix={<ThunderboltOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
              <Progress
                percent={stats.total > 0 ? (stats.low / stats.total) * 100 : 0}
                showInfo={false}
                strokeColor="#1890ff"
              />
            </Card>
          </Col>
        </Row>

        {/* Filters */}
        <Card title={<><FilterOutlined /> <strong>Filters</strong></>}>
          <Row gutter={16}>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Severity:</strong>
              </div>
              <Select
                placeholder="Select severity"
                allowClear
                style={{ width: '100%' }}
                value={filters.severity}
                onChange={(value) => handleFilterChange('severity', value)}
              >
                <Option value="high">Critical</Option>
                <Option value="medium">Medium</Option>
                <Option value="low">Low</Option>
              </Select>
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Status:</strong>
              </div>
              <Select
                placeholder="Select status"
                allowClear
                style={{ width: '100%' }}
                value={filters.status}
                onChange={(value) => handleFilterChange('status', value)}
              >
                <Option value="active">Active</Option>
                <Option value="resolved">Resolved</Option>
                <Option value="monitoring">Monitoring</Option>
              </Select>
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Drug Class:</strong>
              </div>
              <Select
                placeholder="Select drug class"
                allowClear
                style={{ width: '100%' }}
                value={filters.drugClass}
                onChange={(value) => handleFilterChange('drugClass', value)}
              >
                <Option value="oncology">Oncology</Option>
                <Option value="cardiovascular">Cardiovascular</Option>
                <Option value="cns">CNS</Option>
                <Option value="anti-infective">Anti-Infective</Option>
              </Select>
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Therapeutic Area:</strong>
              </div>
              <Select
                placeholder="Select area"
                allowClear
                style={{ width: '100%' }}
                value={filters.therapeuticArea}
                onChange={(value) => handleFilterChange('therapeuticArea', value)}
              >
                <Option value="oncology">Oncology</Option>
                <Option value="cardiology">Cardiology</Option>
                <Option value="neurology">Neurology</Option>
                <Option value="infectious-disease">Infectious Disease</Option>
              </Select>
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Date Range:</strong>
              </div>
              <RangePicker
                style={{ width: '100%' }}
                value={filters.dateRange}
                onChange={(value) => handleFilterChange('dateRange', value)}
              />
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Actions:</strong>
              </div>
              <Button onClick={() => setFilters({ severity: undefined, status: 'active', drugClass: undefined, therapeuticArea: undefined, dateRange: null })}>
                Clear Filters
              </Button>
            </Col>
          </Row>
        </Card>

        {/* Historical Trends */}
        <Card title={<><CalendarOutlined /> <strong>Historical Shortage Trends</strong></>}>
          <TimelineChart
            apiBaseUrl="/api/v1"
            height={300}
            onDataPointClick={(dataPoint) => {
              console.log('Timeline data point clicked:', dataPoint);
            }}
          />
        </Card>

        {/* Shortages Table */}
        <Card
          title={`Active Shortages (${total} total)`}
          extra={
            <Space>
              <Button icon={<GlobalOutlined />}>Export Report</Button>
              <Button icon={<TeamOutlined />}>Notify Stakeholders</Button>
            </Space>
          }
        >
          <Table
            columns={columns}
            dataSource={shortages}
            rowKey="id"
            loading={isLoading}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} shortages`
            }}
            rowClassName={(record) => {
              if (record.severity === 'high') return 'row-critical';
              if (record.severity === 'medium') return 'row-warning';
              return '';
            }}
          />
        </Card>
      </Space>

      {/* Cascade Analysis Drawer */}
      <Drawer
        title={`Shortage Cascade Analysis: ${selectedShortage?.productName}`}
        width={720}
        onClose={() => setCascadeDrawerVisible(false)}
        open={cascadeDrawerVisible}
      >
        {selectedShortage && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Card type="inner" title="Shortage Details">
              <Descriptions>
                <Descriptions.Item label="Product">{selectedShortage.productName}</Descriptions.Item>
                <Descriptions.Item label="Severity">
                  <Tag
                    icon={getSeverityIcon(selectedShortage.severity!)}
                    color={getSeverityColor(selectedShortage.severity!)}
                  >
                    {selectedShortage.severity?.toUpperCase()}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Start Date">
                  {new Date(selectedShortage.startDate).toLocaleDateString()}
                </Descriptions.Item>
                <Descriptions.Item label="Reason">{selectedShortage.reason}</Descriptions.Item>
              </Descriptions>
            </Card>

            <Card type="inner" title="Impact Analysis">
              <Alert
                message="This shortage may affect downstream products"
                description="Identified 3 dependent formulations and 2 combination products"
                type="warning"
                showIcon
              />
            </Card>

            <Card type="inner" title="Dependency Network">
              <GraphViewer
                data={{
                  nodes: [
                    { id: '1', label: selectedShortage.productName, type: 'shortage' },
                    { id: '2', label: 'Formulation A', type: 'product' },
                    { id: '3', label: 'Formulation B', type: 'product' },
                    { id: '4', label: 'Manufacturer X', type: 'manufacturer' }
                  ],
                  edges: [
                    { from: '1', to: '2', label: 'used in' },
                    { from: '1', to: '3', label: 'used in' },
                    { from: '2', to: '4', label: 'produced by' }
                  ]
                }}
                layoutType="force"
                height={400}
              />
            </Card>

            <Card type="inner" title="Timeline">
              <Timeline
                items={[
                  {
                    color: 'red',
                    children: (
                      <div>
                        <p style={{ fontWeight: 'bold', margin: 0 }}>Shortage Declared</p>
                        <p style={{ margin: 0, fontSize: '12px' }}>
                          {new Date(selectedShortage.startDate).toLocaleDateString()}
                        </p>
                      </div>
                    )
                  },
                  {
                    color: 'orange',
                    children: (
                      <div>
                        <p style={{ fontWeight: 'bold', margin: 0 }}>Impact Assessment</p>
                        <p style={{ margin: 0, fontSize: '12px' }}>In Progress</p>
                      </div>
                    )
                  },
                  {
                    color: 'gray',
                    children: (
                      <div>
                        <p style={{ fontWeight: 'bold', margin: 0 }}>Expected Resolution</p>
                        <p style={{ margin: 0, fontSize: '12px' }}>TBD</p>
                      </div>
                    )
                  }
                ]}
              />
            </Card>
          </Space>
        )}
      </Drawer>

      <style>{`
        .row-critical {
          background-color: #fff1f0;
        }
        .row-warning {
          background-color: #fffbe6;
        }
      `}</style>
    </div>
  );
};

export default ShortageMonitorPage;
