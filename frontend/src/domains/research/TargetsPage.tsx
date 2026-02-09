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
  Alert,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { DataTable, TableColumn } from '@/shared/components';
import { useTargets } from './hooks';
import { Target } from './types';

const { Title, Text } = Typography;
const { Option } = Select;

interface FilterState {
  search: string;
  organism: string[];
  proteinType: string[];
  geneFamily: string[];
}

const TargetsPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    organism: [],
    proteinType: [],
    geneFamily: [],
  });

  const [showFilters, setShowFilters] = useState(false);

  // Build API params from filters
  const apiParams = {
    page: currentPage,
    page_size: pageSize,
    ...(filters.search && { search: filters.search }),
    ...(filters.organism.length > 0 && { organism: filters.organism.join(',') }),
    ...(filters.proteinType.length > 0 && { protein_type: filters.proteinType.join(',') }),
    ...(filters.geneFamily.length > 0 && { gene_family: filters.geneFamily.join(',') }),
  };

  const { data, isLoading, error, refetch } = useTargets(apiParams);

  const handleRowClick = (record: Target) => {
    navigate(`/rd/targets/${record.id}`);
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      organism: [],
      proteinType: [],
      geneFamily: [],
    });
    setCurrentPage(1);
  };

  // Define table columns
  const columns: TableColumn<Target>[] = [
    {
      key: 'uniprotId',
      title: 'UniProt ID',
      dataIndex: 'uniprotId',
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
      title: 'Target Name',
      dataIndex: 'name',
      width: 250,
      sorter: true,
      filterable: true,
      render: (name: string, record: Target) => (
        <a
          onClick={() => navigate(`/rd/targets/${record.id}`)}
          style={{ fontWeight: 500 }}
        >
          {name}
        </a>
      ),
    },
    {
      key: 'proteinType',
      title: 'Protein Type',
      dataIndex: 'proteinType',
      width: 150,
      filterable: true,
      render: (type: string) => (type ? <Tag color="blue">{type}</Tag> : '-'),
    },
    {
      key: 'organism',
      title: 'Organism',
      dataIndex: 'organism',
      width: 120,
      filterable: true,
      render: (organism: string) => {
        const orgMap: Record<string, { name: string; color: string }> = {
          human: { name: 'Homo sapiens', color: 'green' },
          mouse: { name: 'Mus musculus', color: 'blue' },
          rat: { name: 'Rattus norvegicus', color: 'cyan' },
        };
        const config = orgMap[organism?.toLowerCase()] || { name: organism, color: 'default' };
        return <Tag color={config.color}>{config.name || organism}</Tag>;
      },
    },
    {
      key: 'geneFamily',
      title: 'Gene Family',
      dataIndex: 'geneFamily',
      width: 150,
      filterable: true,
      render: (family: string) => (family ? <Tag color="purple">{family}</Tag> : '-'),
    },
    {
      key: 'compounds',
      title: 'Compounds',
      dataIndex: 'compounds',
      width: 100,
      align: 'center' as const,
      render: (compounds: any[]) => <Text>{compounds?.length || 0}</Text>,
    },
    {
      key: 'pathways',
      title: 'Pathways',
      dataIndex: 'pathways',
      width: 100,
      align: 'center' as const,
      render: (pathways: any[]) => <Text>{pathways?.length || 0}</Text>,
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
                Protein Targets
              </Title>
              <Button icon={<ExportOutlined />}>Export</Button>
            </Space>
            <Text type="secondary">
              Browse and search protein targets with associated compounds and pathways
            </Text>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Total Targets</Text>
              <Title level={3} style={{ margin: 0 }}>
                {data?.total || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Human Targets</Text>
              <Title level={3} style={{ margin: 0, color: '#52c41a' }}>
                -
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Druggable Targets</Text>
              <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                -
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Avg. Compounds/Target</Text>
              <Title level={3} style={{ margin: 0 }}>
                -
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
              placeholder="Search by target name, UniProt ID, or gene symbol..."
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
              <Col span={8}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Organism</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select organisms"
                    style={{ width: '100%' }}
                    value={filters.organism}
                    onChange={(values) => setFilters({ ...filters, organism: values })}
                  >
                    <Option value="human">Homo sapiens</Option>
                    <Option value="mouse">Mus musculus</Option>
                    <Option value="rat">Rattus norvegicus</Option>
                    <Option value="other">Other</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={8}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Protein Type</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select protein types"
                    style={{ width: '100%' }}
                    value={filters.proteinType}
                    onChange={(values) => setFilters({ ...filters, proteinType: values })}
                  >
                    <Option value="receptor">Receptor</Option>
                    <Option value="enzyme">Enzyme</Option>
                    <Option value="transporter">Transporter</Option>
                    <Option value="ion_channel">Ion Channel</Option>
                    <Option value="transcription_factor">Transcription Factor</Option>
                    <Option value="other">Other</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={8}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Gene Family</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select gene families"
                    style={{ width: '100%' }}
                    value={filters.geneFamily}
                    onChange={(values) => setFilters({ ...filters, geneFamily: values })}
                  >
                    <Option value="kinase">Kinase</Option>
                    <Option value="gpcr">GPCR</Option>
                    <Option value="ion_channel">Ion Channel</Option>
                    <Option value="nuclear_receptor">Nuclear Receptor</Option>
                    <Option value="protease">Protease</Option>
                    <Option value="phosphatase">Phosphatase</Option>
                  </Select>
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
      {error && (
        <Alert
          message="Error loading targets"
          description={error.message}
          type="error"
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Data Table */}
      <DataTable<Target>
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
    </Container>
  );
};

export default TargetsPage;
