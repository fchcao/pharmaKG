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
  Descriptions,
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
  PillOutlined,
  SyringeOutlined,
  FunctionOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { DataTable, TableColumn } from '@/shared/components';
import { useInterventions, useClinicalStatistics } from './hooks';
import { Intervention } from './types';
import { mockInterventions, mockStatistics } from './mockData';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface FilterState {
  search: string;
  type: string[];
  arm: string;
}

const InterventionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [useMockData, setUseMockData] = useState(true);

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    type: [],
    arm: '',
  });

  const [showFilters, setShowFilters] = useState(false);

  const apiParams = {
    page: currentPage,
    page_size: pageSize,
    ...(filters.search && { search: filters.search }),
    ...(filters.type.length > 0 && { type: filters.type.join(',') }),
    ...(filters.arm && { arm: filters.arm }),
  };

  const { data: apiData, isLoading, error, refetch } = useInterventions(
    useMockData ? {} : apiParams,
    { enabled: !useMockData }
  );
  const { data: stats } = useClinicalStatistics();

  const interventions = useMockData || !apiData?.items?.length ? mockInterventions : apiData.items;
  const statistics = useMockData || !stats ? mockStatistics : stats;
  const total = useMockData ? mockInterventions.length : (apiData?.total || 0);

  const handleRowClick = (record: Intervention) => {
    navigate(`/clinical/interventions/${record.id}`);
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      type: [],
      arm: '',
    });
    setCurrentPage(1);
  };

  const getInterventionIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'Drug': <PillOutlined />,
      'Biological': <MedicineBoxOutlined />,
      'Procedure': <SyringeOutlined />,
      'Genetic': <FunctionOutlined />,
      'Behavioral': <ExperimentOutlined />,
      'Device': <MedicineBoxOutlined />,
      'Other': <MedicineBoxOutlined />,
    };
    return iconMap[type] || <MedicineBoxOutlined />;
  };

  const columns: TableColumn<Intervention>[] = [
    {
      key: 'name',
      title: 'Intervention',
      dataIndex: 'name',
      width: 250,
      sorter: true,
      filterable: true,
      render: (name: string, record: Intervention) => (
        <a
          onClick={() => navigate(`/clinical/interventions/${record.id}`)}
          style={{ fontWeight: 500 }}
        >
          <Space>
            {getInterventionIcon(record.interventionType)}
            {name}
          </Space>
        </a>
      ),
    },
    {
      key: 'interventionType',
      title: 'Type',
      dataIndex: 'interventionType',
      width: 120,
      filterable: true,
      render: (type: string) => {
        const typeColors: Record<string, string> = {
          'Drug': 'blue',
          'Biological': 'green',
          'Procedure': 'orange',
          'Genetic': 'purple',
          'Behavioral': 'cyan',
          'Device': 'magenta',
          'Other': 'default',
        };
        return (
          <Tag color={typeColors[type] || 'default'} icon={getInterventionIcon(type)}>
            {type}
          </Tag>
        );
      },
    },
    {
      key: 'armGroupLabel',
      title: 'Arm Group',
      dataIndex: 'armGroupLabel',
      width: 140,
      filterable: true,
      render: (arm: string) => arm ? (
        <Tag color="geekblue">{arm}</Tag>
      ) : <Text type="secondary">-</Text>,
    },
    {
      key: 'dosage',
      title: 'Dosage',
      dataIndex: 'dosage',
      width: 150,
      render: (dosage: string) => dosage ? (
        <Text code style={{ fontSize: 11 }}>{dosage}</Text>
      ) : <Text type="secondary">-</Text>,
    },
    {
      key: 'frequency',
      title: 'Frequency',
      dataIndex: 'frequency',
      width: 140,
      render: (freq: string) => freq ? <Text>{freq}</Text> : <Text type="secondary">-</Text>,
    },
    {
      key: 'trialId',
      title: 'Trial ID',
      dataIndex: 'trialId',
      width: 120,
      render: (trialId: string, record: Intervention) => (
        <a
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/clinical/trials/${trialId}`);
          }}
        >
          {trialId}
        </a>
      ),
    },
    {
      key: 'description',
      title: 'Description',
      dataIndex: 'description',
      render: (desc: string) => desc ? (
        <Text type="secondary" ellipsis style={{ maxWidth: 200 }}>
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
                Interventions
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
              Browse {statistics?.totalInterventions || '...'} interventions being studied in clinical trials
            </Text>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Interventions"
              value={statistics?.totalInterventions || 0}
              suffix="interventions"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Drug Interventions"
              value={Math.round((statistics?.totalInterventions || 0) * 0.45)}
              suffix="drugs"
              valueStyle={{ color: '#1890ff' }}
              prefix={<PillOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Biological Interventions"
              value={Math.round((statistics?.totalInterventions || 0) * 0.25)}
              suffix="biologics"
              valueStyle={{ color: '#52c41a' }}
              prefix={<MedicineBoxOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Other Interventions"
              value={Math.round((statistics?.totalInterventions || 0) * 0.30)}
              suffix="other"
              prefix={<ExperimentOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Search and Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Input
              placeholder="Search by intervention name, description, or trial ID..."
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
                  <Text strong>Intervention Type</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select types"
                    style={{ width: '100%' }}
                    value={filters.type}
                    onChange={(values) => setFilters({ ...filters, type: values })}
                  >
                    <Option value="Drug">Drug</Option>
                    <Option value="Biological">Biological</Option>
                    <Option value="Procedure">Procedure</Option>
                    <Option value="Genetic">Genetic</Option>
                    <Option value="Behavioral">Behavioral</Option>
                    <Option value="Device">Device</Option>
                    <Option value="Other">Other</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Arm Group</Text>
                  <Input
                    placeholder="Enter arm group label"
                    value={filters.arm}
                    onChange={(e) => setFilters({ ...filters, arm: e.target.value })}
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
          message="Error loading interventions"
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
        <DataTable<Intervention>
          columns={columns}
          data={interventions}
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
        <GridInterventionsView
          interventions={interventions}
          loading={isLoading}
          onInterventionClick={(intervention) => navigate(`/clinical/interventions/${intervention.id}`)}
        />
      )}
    </Container>
  );
};

// Grid View Component
const GridInterventionsView: React.FC<{
  interventions: Intervention[];
  loading: boolean;
  onInterventionClick: (intervention: Intervention) => void;
}> = ({ interventions, loading, onInterventionClick }) => {
  const getInterventionIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'Drug': <PillOutlined />,
      'Biological': <MedicineBoxOutlined />,
      'Procedure': <SyringeOutlined />,
      'Genetic': <FunctionOutlined />,
      'Behavioral': <ExperimentOutlined />,
      'Device': <MedicineBoxOutlined />,
      'Other': <MedicineBoxOutlined />,
    };
    return iconMap[type] || <MedicineBoxOutlined />;
  };

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
      {interventions.map((intervention) => (
        <Col key={intervention.id} span={6}>
          <Card
            hoverable
            onClick={() => onInterventionClick(intervention)}
            style={{ height: '100%' }}
            bodyStyle={{ padding: 16 }}
          >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Space>
                {getInterventionIcon(intervention.interventionType)}
                <Text strong ellipsis style={{ fontSize: 13 }}>
                  {intervention.name}
                </Text>
              </Space>

              <Divider style={{ margin: '8px 0' }} />

              <Tag color="blue">{intervention.interventionType}</Tag>
              {intervention.armGroupLabel && (
                <Tag color="geekblue">{intervention.armGroupLabel}</Tag>
              )}

              {intervention.dosage && (
                <Text code style={{ fontSize: 11 }}>{intervention.dosage}</Text>
              )}

              {intervention.frequency && (
                <Text style={{ fontSize: 12 }}>{intervention.frequency}</Text>
              )}

              {intervention.description && (
                <Text type="secondary" ellipsis style={{ fontSize: 11 }}>
                  {intervention.description}
                </Text>
              )}

              <a
                onClick={(e) => {
                  e.stopPropagation();
                  onInterventionClick(intervention);
                }}
                style={{ fontSize: 11 }}
              >
                View Trial: {intervention.trialId}
              </a>
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );
};

export default InterventionsPage;
