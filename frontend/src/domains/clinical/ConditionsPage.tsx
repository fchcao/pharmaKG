import React, { useState } from 'react';
import {
  Container,
  Row,
  Col,
  Card,
  Space,
  Typography,
  Tag,
  Button,
  Input,
  Select,
  Divider,
  Alert,
  Statistic,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  ExportOutlined,
  UnorderedListOutlined,
  AppstoreOutlined,
  MedicineBoxOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { DataTable, TableColumn } from '@/shared/components';
import { useConditions, useClinicalStatistics } from './hooks';
import { Condition } from './types';
import { mockConditions, mockStatistics } from './mockData';

const { Title, Text } = Typography;
const { Option } = Select;

interface FilterState {
  search: string;
  phase: string[];
  minTrialCount: number | null;
}

const ConditionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [useMockData, setUseMockData] = useState(true);

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    phase: [],
    minTrialCount: null,
  });

  const [showFilters, setShowFilters] = useState(false);

  const apiParams = {
    page: currentPage,
    page_size: pageSize,
    ...(filters.search && { search: filters.search }),
    ...(filters.phase.length > 0 && { phase: filters.phase.join(',') }),
    ...(filters.minTrialCount !== null && { min_trial_count: filters.minTrialCount }),
  };

  const { data: apiData, isLoading, error, refetch } = useConditions(
    useMockData ? {} : apiParams,
    { enabled: !useMockData }
  );
  const { data: stats } = useClinicalStatistics();

  const conditions = useMockData || !apiData?.items?.length ? mockConditions : apiData.items;
  const statistics = useMockData || !stats ? mockStatistics : stats;
  const total = useMockData ? mockConditions.length : (apiData?.total || 0);

  const handleRowClick = (record: Condition) => {
    navigate(`/clinical/conditions/${record.id}`);
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      phase: [],
      minTrialCount: null,
    });
    setCurrentPage(1);
  };

  const columns: TableColumn<Condition>[] = [
    {
      key: 'name',
      title: 'Condition',
      dataIndex: 'name',
      width: 300,
      sorter: true,
      filterable: true,
      render: (name: string, record: Condition) => (
        <a
          onClick={() => navigate(`/clinical/conditions/${record.id}`)}
          style={{ fontWeight: 500 }}
        >
          <Space>
            <MedicineBoxOutlined />
            {name}
          </Space>
        </a>
      ),
    },
    {
      key: 'code',
      title: 'Code',
      dataIndex: 'code',
      width: 100,
      filterable: true,
      render: (code: string) => code ? <Text code>{code}</Text> : <Text type="secondary">-</Text>,
    },
    {
      key: 'phase',
      title: 'Most Common Phase',
      dataIndex: 'phase',
      width: 120,
      filterable: true,
      render: (phase: string) => {
        if (!phase || phase === 'N/A') return <Tag color="default">N/A</Tag>;
        const phaseColors: Record<string, string> = {
          'Phase 1': 'cyan',
          'Phase 2': 'blue',
          'Phase 3': 'geekblue',
          'Phase 4': 'green',
        };
        return <Tag color={phaseColors[phase] || 'default'}>{phase}</Tag>;
      },
    },
    {
      key: 'trialCount',
      title: 'Trial Count',
      dataIndex: 'trialCount',
      width: 120,
      align: 'right' as const,
      sorter: true,
      render: (count: number) => (
        <Space>
          <ExperimentOutlined />
          <Text strong>{count?.toLocaleString() || 0}</Text>
        </Space>
      ),
    },
    {
      key: 'description',
      title: 'Description',
      dataIndex: 'description',
      render: (desc: string) => desc ? (
        <Text type="secondary" ellipsis style={{ maxWidth: 300 }}>
          {desc}
        </Text>
      ) : <Text type="secondary">-</Text>,
    },
  ];

  return (
    <Container style={{ padding: '24px', maxWidth: '1400px' }}>
      {/* Header */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Title level={2} style={{ margin: 0 }}>
                Medical Conditions
              </Title>
              <Space>
                {useMockData && <Tag color="warning">Using Mock Data</Tag>}
                <Button
                  icon={viewMode === 'table' ? <AppstoreOutlined /> : <UnorderedListOutlined />}
                  onClick={() => setViewMode(viewMode === 'table' ? 'grid' : 'table')}
                >
                  {viewMode === 'table' ? 'Grid View' : 'Table View'}
                </Button>
                <Button icon={<ExportOutlined />}>Export</Button>
              </Space>
            </Space>
            <Text type="secondary">
              Browse {statistics?.totalConditions || '...'} medical conditions and diseases studied in clinical trials
            </Text>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Conditions"
              value={statistics?.totalConditions || 0}
              suffix="conditions"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Phase 3 Trials"
              value={statistics?.phaseDistribution?.['Phase 3'] || 0}
              suffix="trials"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Trials"
              value={statistics?.activeTrials || 0}
              suffix="trials"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg. Trials per Condition"
              value={Math.round((statistics?.totalTrials || 0) / (statistics?.totalConditions || 1) * 10) / 10}
              suffix="trials"
            />
          </Card>
        </Col>
      </Row>

      {/* Search and Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Input
              placeholder="Search by condition name, code, or description..."
              prefix={<SearchOutlined />}
              size="large"
              value={filters.search}
              onChange={(e) => {
                setFilters({ ...filters, search: e.target.value });
                setCurrentPage(1);
              }}
              allowClear
            />
          </Col>

          {showFilters && (
            <>
              <Col span={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Phase</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select phases"
                    style={{ width: '100%' }}
                    value={filters.phase}
                    onChange={(values) => setFilters({ ...filters, phase: values })}
                  >
                    <Option value="Phase 1">Phase 1</Option>
                    <Option value="Phase 2">Phase 2</Option>
                    <Option value="Phase 3">Phase 3</Option>
                    <Option value="Phase 4">Phase 4</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Minimum Trial Count</Text>
                  <Input
                    type="number"
                    placeholder="Enter minimum number"
                    value={filters.minTrialCount || ''}
                    onChange={(e) => setFilters({ ...filters, minTrialCount: e.target.value ? parseInt(e.target.value) : null })}
                  />
                </Space>
              </Col>
            </>
          )}

          <Col span={24}>
            <Space>
              <Button
                type="primary"
                icon={<FilterOutlined />}
                onClick={() => setShowFilters(!showFilters)}
              >
                {showFilters ? 'Hide Filters' : 'Show Filters'}
              </Button>
              <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
                Refresh
              </Button>
              <Button onClick={handleResetFilters}>Reset Filters</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Error Alert */}
      {error && !useMockData && (
        <Alert
          message="Error loading conditions"
          description={error.message}
          type="error"
          closable
          action={
            <Button size="small" onClick={() => setUseMockData(true)}>
              Use Mock Data
            </Button>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Data Display */}
      {viewMode === 'table' ? (
        <DataTable<Condition>
          columns={columns}
          data={conditions}
          loading={isLoading}
          pagination={{
            page: currentPage,
            pageSize,
            total,
            onPageChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size);
            },
          }}
          onRowClick={handleRowClick}
        />
      ) : (
        <GridConditionsView
          conditions={conditions}
          loading={isLoading}
          onConditionClick={(condition) => navigate(`/clinical/conditions/${condition.id}`)}
        />
      )}
    </Container>
  );
};

// Grid View Component
const GridConditionsView: React.FC<{
  conditions: Condition[];
  loading: boolean;
  onConditionClick: (condition: Condition) => void;
}> = ({ conditions, loading, onConditionClick }) => {
  if (loading) {
    return (
      <Row gutter={[16, 16]}>
        {[...Array(8)].map((_, i) => (
          <Col key={i} span={6}>
            <Card loading />
          </Col>
        ))}
      </Row>
    );
  }

  return (
    <Row gutter={[16, 16]}>
      {conditions.map((condition) => (
        <Col key={condition.id} span={6}>
          <Card
            hoverable
            onClick={() => onConditionClick(condition)}
            style={{ height: '100%' }}
            bodyStyle={{ padding: 16 }}
          >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Space>
                <MedicineBoxOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                <Text strong ellipsis style={{ fontSize: 14 }}>
                  {condition.name}
                </Text>
              </Space>

              <Divider style={{ margin: '8px 0' }} />

              {condition.code && (
                <Text code style={{ fontSize: 11 }}>{condition.code}</Text>
              )}

              {condition.phase && condition.phase !== 'N/A' && (
                <Tag color="blue">{condition.phase}</Tag>
              )}

              <Space>
                <ExperimentOutlined />
                <Text strong>{condition.trialCount?.toLocaleString() || 0}</Text>
                <Text type="secondary">trials</Text>
              </Space>
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );
};

export default ConditionsPage;
