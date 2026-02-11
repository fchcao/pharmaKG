import React, { useState } from 'react';
import {
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
  Progress,
  Tooltip,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  ExportOutlined,
  UnorderedListOutlined,
  AppstoreOutlined,
  EnvironmentOutlined,
  TeamOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { DataTable, TableColumn } from '@/shared/components';
import { useTrials, useClinicalStatistics } from './hooks';
import { ClinicalTrial } from './types';
import { mockClinicalTrials, mockStatistics } from './mockData';

const { Title, Text } = Typography;
const { Option } = Select;

interface FilterState {
  search: string;
  phase: string[];
  status: string[];
  studyType: string[];
  condition: string;
  minEnrollment: number | null;
}

const TrialsPage: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [useMockData, setUseMockData] = useState(true); // Use mock data by default

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    phase: [],
    status: [],
    studyType: [],
    condition: '',
    minEnrollment: null,
  });

  const [showFilters, setShowFilters] = useState(false);

  // Build API params from filters
  const apiParams = {
    page: currentPage,
    page_size: pageSize,
    ...(filters.search && { search: filters.search }),
    ...(filters.phase.length > 0 && { phase: filters.phase.join(',') }),
    ...(filters.status.length > 0 && { status: filters.status.join(',') }),
    ...(filters.studyType.length > 0 && { study_type: filters.studyType.join(',') }),
    ...(filters.condition && { condition: filters.condition }),
    ...(filters.minEnrollment !== null && { min_enrollment: filters.minEnrollment }),
  };

  // Use real API or mock data based on flag
  const { data: apiData, isLoading, error, refetch } = useTrials(
    useMockData ? {} : apiParams,
    { enabled: !useMockData }
  );
  const { data: stats } = useClinicalStatistics();

  // Use mock data if enabled or API returns empty
  const trials = useMockData || !apiData?.items?.length
    ? mockClinicalTrials
    : apiData.items;
  const statistics = useMockData || !stats ? mockStatistics : stats;
  const total = useMockData ? mockClinicalTrials.length : (apiData?.total || 0);

  const handleRowClick = (record: ClinicalTrial) => {
    navigate(`/clinical/trials/${record.nctId}`);
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      phase: [],
      status: [],
      studyType: [],
      condition: '',
      minEnrollment: null,
    });
    setCurrentPage(1);
  };

  // Define table columns
  const columns: TableColumn<ClinicalTrial>[] = [
    {
      key: 'nctId',
      title: 'NCT ID',
      dataIndex: 'nctId',
      width: 120,
      sorter: true,
      filterable: true,
      render: (id: string) => (
        <Text code copyable={{ text: id }}>
          {id}
        </Text>
      ),
    },
    {
      key: 'title',
      title: 'Title',
      dataIndex: 'title',
      width: 300,
      sorter: true,
      filterable: true,
      render: (title: string, record: ClinicalTrial) => (
        <a
          onClick={() => navigate(`/clinical/trials/${record.nctId}`)}
          style={{ fontWeight: 500 }}
        >
          {title.length > 80 ? `${title.slice(0, 80)}...` : title}
        </a>
      ),
    },
    {
      key: 'phase',
      title: 'Phase',
      dataIndex: 'phase',
      width: 100,
      filterable: true,
      render: (phase: string) => {
        if (!phase || phase === 'N/A') return <Tag color="default">N/A</Tag>;
        const phaseColors: Record<string, string> = {
          'Phase 1': 'cyan',
          'Phase 2': 'blue',
          'Phase 3': 'geekblue',
          'Phase 4': 'green',
          'Phase 1/Phase 2': 'purple',
          'Phase 2/Phase 3': 'magenta',
        };
        return <Tag color={phaseColors[phase] || 'default'}>{phase}</Tag>;
      },
    },
    {
      key: 'status',
      title: 'Status',
      dataIndex: 'status',
      width: 140,
      filterable: true,
      render: (status: string) => {
        if (!status) return <Text type="secondary">-</Text>;
        const statusColors: Record<string, string> = {
          'Recruiting': 'green',
          'Active, not recruiting': 'blue',
          'Completed': 'default',
          'Terminated': 'red',
          'Suspended': 'orange',
          'Withdrawn': 'volcano',
          'Not yet recruiting': 'cyan',
        };
        const color = statusColors[status] || 'default';
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      key: 'studyType',
      title: 'Study Type',
      dataIndex: 'studyType',
      width: 120,
      filterable: true,
      render: (type: string) => type ? <Tag>{type}</Tag> : <Text type="secondary">-</Text>,
    },
    {
      key: 'conditions',
      title: 'Conditions',
      dataIndex: 'conditions',
      width: 200,
      render: (conditions: string[]) => {
        if (!conditions || conditions.length === 0) return <Text type="secondary">-</Text>;
        const display = conditions.slice(0, 2);
        return (
          <Space wrap>
            {display.map((c, i) => (
              <Tag key={i} color="orange">{c}</Tag>
            ))}
            {conditions.length > 2 && (
              <Tooltip title={conditions.slice(2).join(', ')}>
                <Tag>+{conditions.length - 2}</Tag>
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      key: 'enrollment',
      title: 'Enrollment',
      dataIndex: 'enrollment',
      width: 100,
      align: 'right' as const,
      sorter: true,
      render: (enrollment: number) => (
        enrollment ? (
          <Space>
            <TeamOutlined />
            <Text>{enrollment.toLocaleString()}</Text>
          </Space>
        ) : <Text type="secondary">-</Text>
      ),
    },
    {
      key: 'dates',
      title: 'Timeline',
      width: 120,
      render: (_, record: ClinicalTrial) => {
        if (!record.startDate) return <Text type="secondary">-</Text>;
        const startDate = new Date(record.startDate);
        const completionDate = record.completionDate ? new Date(record.completionDate) : null;
        const now = new Date();
        const totalDuration = completionDate
          ? completionDate.getTime() - startDate.getTime()
          : now.getTime() - startDate.getTime();
        const elapsed = now.getTime() - startDate.getTime();
        const progress = Math.min(100, Math.max(0, (elapsed / totalDuration) * 100));

        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text style={{ fontSize: 11 }}>{startDate.toLocaleDateString()}</Text>
            <Progress
              percent={progress}
              size="small"
              status={progress >= 100 ? 'success' : 'active'}
              showInfo={false}
            />
          </Space>
        );
      },
    },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1400px' }}>
      {/* Header */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Title level={2} style={{ margin: 0 }}>
                Clinical Trials
              </Title>
              <Space>
                {useMockData && (
                  <Tag color="warning">Using Mock Data (Domain Empty)</Tag>
                )}
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
              Browse and search {statistics?.totalTrials || '...'} clinical trials from ClinicalTrials.gov
            </Text>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Total Trials</Text>
              <Title level={3} style={{ margin: 0 }}>
                {statistics?.totalTrials?.toLocaleString() || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Recruiting</Text>
              <Title level={3} style={{ margin: 0, color: '#52c41a' }}>
                {statistics?.recruitingTrials?.toLocaleString() || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Active</Text>
              <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                {statistics?.activeTrials?.toLocaleString() || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Completed</Text>
              <Title level={3} style={{ margin: 0, color: '#8c8c8c' }}>
                {statistics?.completedTrials?.toLocaleString() || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Conditions</Text>
              <Title level={3} style={{ margin: 0 }}>
                {statistics?.totalConditions?.toLocaleString() || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Avg. Enrollment</Text>
              <Title level={3} style={{ margin: 0 }}>
                {statistics?.avgEnrollment || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Search and Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Input
              placeholder="Search by NCT ID, title, condition, or sponsor..."
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
              <Col span={6}>
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
                    <Option value="Phase 1/Phase 2">Phase 1/Phase 2</Option>
                    <Option value="Phase 2/Phase 3">Phase 2/Phase 3</Option>
                    <Option value="N/A">N/A</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={6}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Status</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select status"
                    style={{ width: '100%' }}
                    value={filters.status}
                    onChange={(values) => setFilters({ ...filters, status: values })}
                  >
                    <Option value="Recruiting">Recruiting</Option>
                    <Option value="Active, not recruiting">Active, not recruiting</Option>
                    <Option value="Not yet recruiting">Not yet recruiting</Option>
                    <Option value="Completed">Completed</Option>
                    <Option value="Terminated">Terminated</Option>
                    <Option value="Suspended">Suspended</Option>
                    <Option value="Withdrawn">Withdrawn</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={6}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Study Type</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select study types"
                    style={{ width: '100%' }}
                    value={filters.studyType}
                    onChange={(values) => setFilters({ ...filters, studyType: values })}
                  >
                    <Option value="Interventional">Interventional</Option>
                    <Option value="Observational">Observational</Option>
                    <Option value="Patient Registry">Patient Registry</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={6}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Condition</Text>
                  <Input
                    placeholder="Enter condition name"
                    value={filters.condition}
                    onChange={(e) => setFilters({ ...filters, condition: e.target.value })}
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
          message="Error loading clinical trials"
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
        <DataTable<ClinicalTrial>
          columns={columns}
          data={trials}
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
        <GridTrialsView
          trials={trials}
          loading={isLoading}
          onTrialClick={(trial) => navigate(`/clinical/trials/${trial.nctId}`)}
        />
      )}
    </div>
  );
};

// Grid View Component
const GridTrialsView: React.FC<{
  trials: ClinicalTrial[];
  loading: boolean;
  onTrialClick: (trial: ClinicalTrial) => void;
}> = ({ trials, loading, onTrialClick }) => {
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
      {trials.map((trial) => (
        <Col key={trial.id} span={6}>
          <Card
            hoverable
            onClick={() => onTrialClick(trial)}
            style={{ height: '100%' }}
            bodyStyle={{ padding: 16 }}
          >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text strong ellipsis style={{ fontSize: 13 }}>
                  {trial.title}
                </Text>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {trial.nctId}
                </Text>
              </Space>

              <Divider style={{ margin: '8px 0' }} />

              <Space wrap>
                {trial.phase && trial.phase !== 'N/A' && (
                  <Tag color="blue">{trial.phase}</Tag>
                )}
                {trial.status && (
                  <Tag color={
                    trial.status === 'Recruiting' ? 'green' :
                    trial.status === 'Active, not recruiting' ? 'blue' :
                    trial.status === 'Completed' ? 'default' : 'orange'
                  }>
                    {trial.status}
                  </Tag>
                )}
              </Space>

              <Space size="small" style={{ fontSize: 12 }}>
                <TeamOutlined />
                <Text>{trial.enrollment || 0}</Text>
                <CalendarOutlined />
                <Text>{trial.startDate ? new Date(trial.startDate).getFullYear() : '-'}</Text>
              </Space>

              {trial.conditions && trial.conditions.length > 0 && (
                <Space wrap style={{ fontSize: 12 }}>
                  {trial.conditions.slice(0, 2).map((c, i) => (
                    <Tag key={i} color="orange" style={{ fontSize: 11 }}>{c}</Tag>
                  ))}
                  {trial.conditions.length > 2 && (
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      +{trial.conditions.length - 2}
                    </Text>
                  )}
                </Space>
              )}
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );
};

export default TrialsPage;
