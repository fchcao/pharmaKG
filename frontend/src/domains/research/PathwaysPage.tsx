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
  Alert,
  List,
  Statistic,
  Tree,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  ExportOutlined,
  NodeIndexOutlined,
  ApartmentOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { DataTable, TableColumn } from '@/shared/components';
import { usePathways } from './hooks';
import { Pathway } from './types';
import { GraphViewer } from '@/shared/graphs';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface FilterState {
  search: string;
  category: string[];
  organism: string[];
}

interface TreeNode {
  title: string;
  key: string;
  children?: TreeNode[];
}

const PathwaysPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedPathway, setSelectedPathway] = useState<Pathway | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'tree' | 'graph'>('list');

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    category: [],
    organism: [],
  });

  const [showFilters, setShowFilters] = useState(false);

  // Build API params from filters
  const apiParams = {
    page: currentPage,
    page_size: pageSize,
    ...(filters.search && { search: filters.search }),
    ...(filters.category.length > 0 && { category: filters.category.join(',') }),
    ...(filters.organism.length > 0 && { organism: filters.organism.join(',') }),
  };

  const { data, isLoading, error, refetch } = usePathways(apiParams);

  const handleRowClick = (record: Pathway) => {
    setSelectedPathway(record);
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      category: [],
      organism: [],
    });
    setCurrentPage(1);
  };

  // Define table columns
  const columns: TableColumn<Pathway>[] = [
    {
      key: 'keggId',
      title: 'KEGG ID',
      dataIndex: 'keggId',
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
      title: 'Pathway Name',
      dataIndex: 'name',
      width: 300,
      sorter: true,
      filterable: true,
      render: (name: string, record: Pathway) => (
        <a
          onClick={() => navigate(`/rd/pathways/${record.id}`)}
          style={{ fontWeight: 500 }}
        >
          {name}
        </a>
      ),
    },
    {
      key: 'category',
      title: 'Category',
      dataIndex: 'category',
      width: 150,
      filterable: true,
      render: (category: string) => {
        const categoryConfig: Record<string, { text: string; color: string }> = {
          metabolism: { text: 'Metabolism', color: 'green' },
          genetic: { text: 'Genetic Information', color: 'blue' },
          environmental: { text: 'Environmental', color: 'cyan' },
          cellular: { text: 'Cellular Processes', color: 'purple' },
          organismal: { text: 'Organismal Systems', color: 'orange' },
          disease: { text: 'Human Diseases', color: 'red' },
        };
        const config = categoryConfig[category?.toLowerCase()] || {
          text: category,
          color: 'default',
        };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      key: 'description',
      title: 'Description',
      dataIndex: 'description',
      render: (desc: string) => (
        <Text ellipsis style={{ maxWidth: 300 }}>
          {desc}
        </Text>
      ),
    },
    {
      key: 'targets',
      title: 'Targets',
      dataIndex: 'targets',
      width: 100,
      align: 'center' as const,
      render: (targets: any[]) => <Text>{targets?.length || 0}</Text>,
    },
    {
      key: 'compounds',
      title: 'Compounds',
      dataIndex: 'compounds',
      width: 100,
      align: 'center' as const,
      render: (compounds: any[]) => <Text>{compounds?.length || 0}</Text>,
    },
  ];

  // Build category tree
  const pathwayTreeData: TreeNode[] = [
    {
      title: 'Metabolism',
      key: 'metabolism',
      children: [
        { title: 'Carbohydrate Metabolism', key: 'carbohydrate' },
        { title: 'Lipid Metabolism', key: 'lipid' },
        { title: 'Amino Acid Metabolism', key: 'amino_acid' },
        { title: 'Nucleotide Metabolism', key: 'nucleotide' },
      ],
    },
    {
      title: 'Genetic Information',
      key: 'genetic',
      children: [
        { title: 'Transcription', key: 'transcription' },
        { title: 'Translation', key: 'translation' },
        { title: 'DNA Replication', key: 'dna_replication' },
      ],
    },
    {
      title: 'Cellular Processes',
      key: 'cellular',
      children: [
        { title: 'Cell Growth', key: 'cell_growth' },
        { title: 'Cell Death', key: 'cell_death' },
        { title: 'Cell Communication', key: 'cell_communication' },
      ],
    },
    {
      title: 'Organismal Systems',
      key: 'organismal',
      children: [
        { title: 'Immune System', key: 'immune' },
        { title: 'Nervous System', key: 'nervous' },
        { title: 'Circulatory System', key: 'circulatory' },
      ],
    },
    {
      title: 'Human Diseases',
      key: 'disease',
      children: [
        { title: 'Cancer', key: 'cancer' },
        { title: 'Immune Diseases', key: 'immune_diseases' },
        { title: 'Metabolic Diseases', key: 'metabolic_diseases' },
      ],
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
                Biological Pathways
              </Title>
              <Space>
                <Button
                  icon={viewMode === 'list' ? <ApartmentOutlined /> : <NodeIndexOutlined />}
                  onClick={() =>
                    setViewMode(viewMode === 'list' ? 'tree' : 'list')
                  }
                >
                  {viewMode === 'list' ? 'Tree View' : 'List View'}
                </Button>
                <Button icon={<ExportOutlined />}>Export</Button>
              </Space>
            </Space>
            <Text type="secondary">
              Browse and search biological pathways from KEGG database
            </Text>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Total Pathways</Text>
              <Title level={3} style={{ margin: 0 }}>
                {data?.total || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Metabolic Pathways</Text>
              <Title level={3} style={{ margin: 0, color: '#52c41a' }}>
                -
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Disease Pathways</Text>
              <Title level={3} style={{ margin: 0, color: '#f5222d' }}>
                -
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Signaling Pathways</Text>
              <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
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
              placeholder="Search by pathway name, KEGG ID, or description..."
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
                  <Text strong>Category</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select categories"
                    style={{ width: '100%' }}
                    value={filters.category}
                    onChange={(values) => setFilters({ ...filters, category: values })}
                  >
                    <Option value="metabolism">Metabolism</Option>
                    <Option value="genetic">Genetic Information</Option>
                    <Option value="environmental">Environmental</Option>
                    <Option value="cellular">Cellular Processes</Option>
                    <Option value="organismal">Organismal Systems</Option>
                    <Option value="disease">Human Diseases</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Organism</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select organisms"
                    style={{ width: '100%' }}
                    value={filters.organism}
                    onChange={(values) => setFilters({ ...filters, organism: values })}
                  >
                    <Option value="hsa">Homo sapiens (human)</Option>
                    <Option value="mmu">Mus musculus (mouse)</Option>
                    <Option value="rno">Rattus norvegicus (rat)</Option>
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
          message="Error loading pathways"
          description={error.message}
          type="error"
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* View Modes */}
      {viewMode === 'list' ? (
        <Row gutter={16}>
          {/* Pathway List */}
          <Col span={selectedPathway ? 16 : 24}>
            <DataTable<Pathway>
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
          </Col>

          {/* Pathway Detail Panel */}
          {selectedPathway && (
            <Col span={8}>
              <Card
                title="Pathway Details"
                extra={
                  <Button
                    type="text"
                    onClick={() => setSelectedPathway(null)}
                  >
                    Close
                  </Button>
                }
                style={{ position: 'sticky', top: 24 }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>KEGG ID:</Text>
                    <br />
                    <Text code copyable={{ text: selectedPathway.keggId }}>
                      {selectedPathway.keggId}
                    </Text>
                  </div>

                  <div>
                    <Text strong>Category:</Text>
                    <br />
                    <Tag color="purple">{selectedPathway.category}</Tag>
                  </div>

                  <div>
                    <Text strong>Description:</Text>
                    <Paragraph
                      style={{ marginTop: 4, marginBottom: 0 }}
                      ellipsis={{ rows: 4 }}
                    >
                      {selectedPathway.description}
                    </Paragraph>
                  </div>

                  <Divider />

                  <Statistic
                    title="Related Targets"
                    value={selectedPathway.targets?.length || 0}
                    prefix={<NodeIndexOutlined />}
                  />

                  <Statistic
                    title="Related Compounds"
                    value={selectedPathway.compounds?.length || 0}
                    style={{ marginTop: 16 }}
                  />

                  {selectedPathway.targets && selectedPathway.targets.length > 0 && (
                    <>
                      <Divider />
                      <Text strong>Top Targets:</Text>
                      <List
                        size="small"
                        dataSource={selectedPathway.targets.slice(0, 5)}
                        renderItem={(target: any) => (
                          <List.Item>
                            <a
                              onClick={() => navigate(`/rd/targets/${target.id}`)}
                            >
                              {target.name}
                            </a>
                          </List.Item>
                        )}
                      />
                    </>
                  )}

                  <Button
                    type="primary"
                    block
                    style={{ marginTop: 16 }}
                    onClick={() =>
                      navigate(`/rd/pathways/${selectedPathway.id}`)
                    }
                  >
                    View Full Details
                  </Button>
                </Space>
              </Card>
            </Col>
          )}
        </Row>
      ) : (
        <Card>
          <Row gutter={16}>
            <Col span={8}>
              <Title level={4}>Browse by Category</Title>
              <Tree
                showLine
                defaultExpandAll
                treeData={pathwayTreeData}
                onSelect={(keys) => {
                  if (keys.length > 0) {
                    const category = keys[0];
                    setFilters({ ...filters, category: [category as string] });
                  }
                }}
              />
            </Col>
            <Col span={16}>
              <Title level={4}>Pathway Network</Title>
              <Alert
                message="Network visualization"
                description="Select a category to see pathway relationships"
                type="info"
                showIcon
              />
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

export default PathwaysPage;
