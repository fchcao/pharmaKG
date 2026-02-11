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
  Slider,
  Select,
  Checkbox,
  Divider,
  Alert,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  ExportOutlined,
  UnorderedListOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { DataTable, TableColumn } from '@/shared/components';
import { useCompounds, useRDStatistics } from './hooks';
import { Compound } from './types';

const { Title, Text } = Typography;
const { Option } = Select;

interface FilterState {
  search: string;
  name: string;
  minMolecularWeight: number;
  maxMolecularWeight: number;
  minLogP: number;
  maxLogP: number;
  drugType: string[];
  isApproved: boolean | null;
  developmentStage: string[];
}

const CompoundsPage: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    name: '',
    minMolecularWeight: 0,
    maxMolecularWeight: 1000,
    minLogP: -5,
    maxLogP: 10,
    drugType: [],
    isApproved: null,
    developmentStage: [],
  });

  const [showFilters, setShowFilters] = useState(false);

  // Build API params from filters
  const apiParams = {
    page: currentPage,
    page_size: pageSize,
    ...(filters.search && { search: filters.search }),
    ...(filters.name && { name: filters.name }),
    ...(filters.minMolecularWeight > 0 && { min_molecular_weight: filters.minMolecularWeight }),
    ...(filters.maxMolecularWeight < 1000 && { max_molecular_weight: filters.maxMolecularWeight }),
    ...(filters.minLogP > -5 && { min_logp: filters.minLogP }),
    ...(filters.maxLogP < 10 && { max_logp: filters.maxLogP }),
    ...(filters.drugType.length > 0 && { drug_type: filters.drugType.join(',') }),
    ...(filters.isApproved !== null && { is_approved: filters.isApproved }),
    ...(filters.developmentStage.length > 0 && {
      development_stage: filters.developmentStage.join(','),
    }),
  };

  const { data, isLoading, error, refetch } = useCompounds(apiParams);
  const { data: statsData } = useRDStatistics();

  // Map backend response to frontend format
  const stats = statsData ? {
    compoundCount: statsData.compounds_count || 0,
    approvedDrugs: statsData.approved_drugs || 0,
    clinicalCandidates: statsData.clinical_candidates || 0,
    avgMolecularWeight: statsData.avg_molecular_weight || 0,
  } : null;

  const handleRowClick = (record: Compound) => {
    navigate(`/rd/compounds/${record.id}`);
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      name: '',
      minMolecularWeight: 0,
      maxMolecularWeight: 1000,
      minLogP: -5,
      maxLogP: 10,
      drugType: [],
      isApproved: null,
      developmentStage: [],
    });
    setCurrentPage(1);
  };

  // Define table columns
  const columns: TableColumn<Compound>[] = [
    {
      key: 'chemblId',
      title: 'ChEMBL ID',
      dataIndex: 'chemblId',
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
      key: 'name',
      title: 'Name',
      dataIndex: 'name',
      width: 200,
      sorter: true,
      filterable: true,
      render: (name: string, record: Compound) => (
        <a
          onClick={() => navigate(`/rd/compounds/${record.id}`)}
          style={{ fontWeight: 500 }}
        >
          {name}
        </a>
      ),
    },
    {
      key: 'molecularWeight',
      title: 'MW (Da)',
      dataIndex: 'molecularWeight',
      width: 100,
      sorter: true,
      align: 'right' as const,
      render: (mw: number) => (mw ? mw.toFixed(2) : '-'),
    },
    {
      key: 'logP',
      title: 'LogP',
      dataIndex: 'logp',
      width: 80,
      sorter: true,
      align: 'right' as const,
      render: (logp: number) => (logp !== undefined ? logp.toFixed(2) : '-'),
    },
    {
      key: 'drugType',
      title: 'Drug Type',
      dataIndex: 'drugType',
      width: 120,
      filterable: true,
      render: (type: string) =>
        type ? (
          <Tag color="blue">{type}</Tag>
        ) : (
          <Tag color="default">Small Molecule</Tag>
        ),
    },
    {
      key: 'maxPhase',
      title: 'Max Phase',
      dataIndex: 'maxPhase',
      width: 100,
      align: 'center' as const,
      render: (phase: number) => {
        if (!phase) return <Text type="secondary">-</Text>;
        const phaseConfig: Record<number, { text: string; color: string }> = {
          0: { text: 'Research', color: 'default' },
          1: { text: 'Phase I', color: 'cyan' },
          2: { text: 'Phase II', color: 'blue' },
          3: { text: 'Phase III', color: 'geekblue' },
          4: { text: 'Approved', color: 'green' },
        };
        const config = phaseConfig[phase] || phaseConfig[0];
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      key: 'targets',
      title: 'Targets',
      dataIndex: 'targets',
      width: 100,
      align: 'center' as const,
      render: (targets: any[]) => (
        <Text>{targets?.length || 0}</Text>
      ),
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
                Compounds
              </Title>
              <Space>
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
              Browse and search {stats?.compoundCount || '...'} compounds from ChEMBL database
            </Text>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Total Compounds</Text>
              <Title level={3} style={{ margin: 0 }}>
                {stats?.compoundCount || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Approved Drugs</Text>
              <Title level={3} style={{ margin: 0, color: '#52c41a' }}>
                {stats?.approvedDrugs || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Clinical Candidates</Text>
              <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                {stats?.clinicalCandidates || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Avg. Molecular Weight</Text>
              <Title level={3} style={{ margin: 0 }}>
                {stats?.avgMolecularWeight || '-'} Da
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
              placeholder="Search by compound name, ChEMBL ID, or SMILES..."
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
              <Col span={24}>
                <Divider orientation="left">Molecular Properties</Divider>
                <Row gutter={16}>
                  <Col span={12}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Text strong>Molecular Weight: {filters.minMolecularWeight} - {filters.maxMolecularWeight} Da</Text>
                      <Slider
                        range
                        min={0}
                        max={1000}
                        value={[filters.minMolecularWeight, filters.maxMolecularWeight]}
                        onChange={(values) =>
                          setFilters({
                            ...filters,
                            minMolecularWeight: values[0],
                            maxMolecularWeight: values[1],
                          })
                        }
                      />
                    </Space>
                  </Col>
                  <Col span={12}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Text strong>LogP: {filters.minLogP} - {filters.maxLogP}</Text>
                      <Slider
                        range
                        min={-5}
                        max={10}
                        step={0.1}
                        value={[filters.minLogP, filters.maxLogP]}
                        onChange={(values) =>
                          setFilters({ ...filters, minLogP: values[0], maxLogP: values[1] })
                        }
                      />
                    </Space>
                  </Col>
                </Row>
              </Col>

              <Col span={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Drug Type</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select drug types"
                    style={{ width: '100%' }}
                    value={filters.drugType}
                    onChange={(values) => setFilters({ ...filters, drugType: values })}
                  >
                    <Option value="small_molecule">Small Molecule</Option>
                    <Option value="antibody">Antibody</Option>
                    <Option value="protein">Protein</Option>
                    <Option value="oligo">Oligonucleotide</Option>
                    <Option value="cell">Cell Therapy</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Development Stage</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select development stages"
                    style={{ width: '100%' }}
                    value={filters.developmentStage}
                    onChange={(values) => setFilters({ ...filters, developmentStage: values })}
                  >
                    <Option value="research">Research</Option>
                    <Option value="preclinical">Preclinical</Option>
                    <Option value="phase_1">Phase I</Option>
                    <Option value="phase_2">Phase II</Option>
                    <Option value="phase_3">Phase III</Option>
                    <Option value="approved">Approved</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={12}>
                <Checkbox
                  checked={filters.isApproved === true}
                  onChange={(e) =>
                    setFilters({ ...filters, isApproved: e.target.checked ? true : null })
                  }
                >
                  Show only approved drugs
                </Checkbox>
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
      {error && (
        <Alert
          message="Error loading compounds"
          description={error.message}
          type="error"
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Data Table */}
      {viewMode === 'table' ? (
        <DataTable<Compound>
          columns={columns}
          data={data?.items || []}
          loading={isLoading}
          pagination={{
            page: currentPage,
            pageSize,
            total: data?.total || 0,
            onPageChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size);
            },
          }}
          onRowClick={handleRowClick}
        />
      ) : (
        <GridCompoundsView
          compounds={data?.items || []}
          loading={isLoading}
          onCompoundClick={(compound) => navigate(`/rd/compounds/${compound.id}`)}
        />
      )}
    </div>
  );
};

// Grid View Component
const GridCompoundsView: React.FC<{
  compounds: Compound[];
  loading: boolean;
  onCompoundClick: (compound: Compound) => void;
}> = ({ compounds, loading, onCompoundClick }) => {
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
      {compounds.map((compound) => (
        <Col key={compound.id} span={6}>
          <Card
            hoverable
            onClick={() => onCompoundClick(compound)}
            style={{ height: '100%' }}
          >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text strong ellipsis style={{ fontSize: 14 }}>
                {compound.name}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {compound.chemblId}
              </Text>
              <Divider style={{ margin: '8px 0' }} />
              <Space size="small">
                <Tag color="blue">{compound.drugType || 'Small Molecule'}</Tag>
                {compound.maxPhase === 4 && <Tag color="green">Approved</Tag>}
              </Space>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text style={{ fontSize: 12 }}>
                  MW: {compound.molecularWeight?.toFixed(1)} Da
                </Text>
                <Text style={{ fontSize: 12 }}>
                  LogP: {compound.logp?.toFixed(2)}
                </Text>
                <Text style={{ fontSize: 12 }}>
                  Targets: {compound.targets?.length || 0}
                </Text>
              </Space>
            </Space>
          </Card>
        </Col>
      ))}
    </Row>
  );
};

export default CompoundsPage;
