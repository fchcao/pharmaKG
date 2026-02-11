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
  Descriptions,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { DataTable, TableColumn } from '@/shared/components';
import { useAssays } from './hooks';
import { Assay } from './types';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface FilterState {
  search: string;
  assayType: string[];
  assayFormat: string[];
  targetIds: string[];
}

const AssaysPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedAssay, setSelectedAssay] = useState<Assay | null>(null);

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    assayType: [],
    assayFormat: [],
    targetIds: [],
  });

  const [showFilters, setShowFilters] = useState(false);

  // Build API params from filters
  const apiParams = {
    page: currentPage,
    page_size: pageSize,
    ...(filters.search && { search: filters.search }),
    ...(filters.assayType.length > 0 && { assay_type: filters.assayType.join(',') }),
    ...(filters.assayFormat.length > 0 && { assay_format: filters.assayFormat.join(',') }),
  };

  const { data, isLoading, error, refetch } = useAssays(apiParams);

  const handleRowClick = (record: Assay) => {
    setSelectedAssay(record);
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      assayType: [],
      assayFormat: [],
      targetIds: [],
    });
    setCurrentPage(1);
  };

  // Define table columns
  const columns: TableColumn<Assay>[] = [
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
      key: 'assayType',
      title: 'Assay Type',
      dataIndex: 'assayType',
      width: 150,
      filterable: true,
      render: (type: string) => {
        const typeConfig: Record<string, { text: string; color: string }> = {
          binding: { text: 'Binding', color: 'blue' },
          functional: { text: 'Functional', color: 'green' },
          adme: { text: 'ADME', color: 'orange' },
          toxicity: { text: 'Toxicity', color: 'red' },
          panel: { text: 'Panel', color: 'purple' },
        };
        const config = typeConfig[type?.toLowerCase()] || {
          text: type,
          color: 'default',
        };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      key: 'assayFormat',
      title: 'Format',
      dataIndex: 'assayFormat',
      width: 120,
      filterable: true,
      render: (format: string) =>
        format ? <Tag color="cyan">{format}</Tag> : '-',
    },
    {
      key: 'description',
      title: 'Description',
      dataIndex: 'description',
      render: (desc: string) => (
        <Text ellipsis style={{ maxWidth: 400 }}>
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
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1400px' }}>
      {/* Header */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Title level={2} style={{ margin: 0 }}>
                Bioassays
              </Title>
              <Button icon={<ExportOutlined />}>Export</Button>
            </Space>
            <Text type="secondary">
              Browse and search bioassays from ChEMBL database
            </Text>
          </Space>
        </Col>
      </Row>

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Total Assays</Text>
              <Title level={3} style={{ margin: 0 }}>
                {data?.total || '-'}
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Binding Assays</Text>
              <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                -
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">Functional Assays</Text>
              <Title level={3} style={{ margin: 0, color: '#52c41a' }}>
                -
              </Title>
            </Space>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space direction="vertical" size="small">
              <Text type="secondary">ADME/Tox Assays</Text>
              <Title level={3} style={{ margin: 0, color: '#faad14' }}>
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
              placeholder="Search by assay description, ChEMBL ID, or target..."
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
                  <Text strong>Assay Type</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select assay types"
                    style={{ width: '100%' }}
                    value={filters.assayType}
                    onChange={(values) => setFilters({ ...filters, assayType: values })}
                  >
                    <Option value="binding">Binding</Option>
                    <Option value="functional">Functional</Option>
                    <Option value="adme">ADME</Option>
                    <Option value="toxicity">Toxicity</Option>
                    <Option value="panel">Panel</Option>
                  </Select>
                </Space>
              </Col>

              <Col span={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Assay Format</Text>
                  <Select
                    mode="multiple"
                    placeholder="Select assay formats"
                    style={{ width: '100%' }}
                    value={filters.assayFormat}
                    onChange={(values) => setFilters({ ...filters, assayFormat: values })}
                  >
                    <Option value="biochemical">Biochemical</Option>
                    <Option value="cell_based">Cell-based</Option>
                    <Option value="in_vitro">In vitro</Option>
                    <Option value="in_vivo">In vivo</Option>
                    <Option value="organism">Organism</Option>
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
          message="Error loading assays"
          description={error.message}
          type="error"
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={16}>
        {/* Assay List */}
        <Col span={selectedAssay ? 16 : 24}>
          <DataTable<Assay>
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

        {/* Assay Detail Panel */}
        {selectedAssay && (
          <Col span={8}>
            <Card
              title="Assay Details"
              extra={
                <Button
                  type="text"
                  onClick={() => setSelectedAssay(null)}
                >
                  Close
                </Button>
              }
              style={{ position: 'sticky', top: 24 }}
            >
              <Descriptions column={1} size="small" bordered>
                <Descriptions.Item label="ChEMBL ID">
                  <Text code copyable={{ text: selectedAssay.chemblId }}>
                    {selectedAssay.chemblId}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="Assay Type">
                  <Tag color="blue">{selectedAssay.assayType}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Assay Format">
                  <Tag color="cyan">{selectedAssay.assayFormat}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Description" span={1}>
                  <Paragraph style={{ marginBottom: 0 }}>
                    {selectedAssay.description}
                  </Paragraph>
                </Descriptions.Item>
                {selectedAssay.targets && selectedAssay.targets.length > 0 && (
                  <Descriptions.Item label="Targets">
                    <Space direction="vertical" size="small">
                      {selectedAssay.targets.map((target: any) => (
                        <Tag key={target.id} color="purple">
                          {target.name}
                        </Tag>
                      ))}
                    </Space>
                  </Descriptions.Item>
                )}
              </Descriptions>

              <Button
                type="primary"
                block
                style={{ marginTop: 16 }}
                onClick={() =>
                  navigate(`/rd/assays/${selectedAssay.id}`)
                }
              >
                View Full Details
              </Button>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default AssaysPage;
