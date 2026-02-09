/**
 * DocumentsPage.tsx - Regulatory Documents Browser
 * Displays searchable/filterable catalog of regulatory documents including FDA CRLs and PDA reports
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Space,
  Button,
  Tag,
  Input,
  Select,
  DatePicker,
  Row,
  Col,
  Statistic,
  Tooltip,
  List,
  Typography,
  Divider,
  Modal
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  EyeOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  BankOutlined,
  CalendarOutlined,
  LockOutlined,
  UnlockOutlined
} from '@ant-design/icons';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import dayjs from 'dayjs';
import { useDocuments, useAgencies } from './hooks';
import { Document, DocumentFilters, Agency, ApiError, PaginatedResponse } from './types';
import { LoadingSpinner, EmptyState } from '@/shared/components';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text, Paragraph } = Typography;

interface FilterState extends DocumentFilters {
  search?: string;
}

const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<FilterState>({
    page: 1,
    pageSize: 20,
  });
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewDocument, setPreviewDocument] = useState<Document | null>(null);

  // Queries
  const {
    data: documentsData,
    isLoading: documentsLoading,
    error: documentsError,
    refetch: refetchDocuments
  } = useDocuments(filters, {
    enabled: true,
  });

  const {
    data: agenciesData,
    isLoading: agenciesLoading
  } = useAgencies({}, {
    enabled: true,
  });

  const agencies = agenciesData?.items || [];
  const documents = documentsData?.items || [];
  const total = documentsData?.total || 0;

  // Handle filter changes
  const handleFilterChange = useCallback((key: string, value: unknown) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: 1,
    }));
  }, []);

  // Handle date range change
  const handleDateRangeChange = useCallback((dates: null | [dayjs.Dayjs, dayjs.Dayjs]) => {
    setDateRange(dates);
    if (dates && dates[0] && dates[1]) {
      setFilters(prev => ({
        ...prev,
        startDate: dates[0].format('YYYY-MM-DD'),
        endDate: dates[1].format('YYYY-MM-DD'),
        page: 1,
      }));
    } else {
      setFilters(prev => ({
        ...prev,
        startDate: undefined,
        endDate: undefined,
        page: 1,
      }));
    }
  }, []);

  // Handle search
  const handleSearch = useCallback((value: string) => {
    setFilters(prev => ({
      ...prev,
      search: value,
      page: 1,
    }));
  }, []);

  // Handle pagination change
  const handleTableChange = useCallback((pagination: TablePaginationConfig) => {
    setFilters(prev => ({
      ...prev,
      page: pagination.current,
      pageSize: pagination.pageSize,
    }));
  }, []);

  // Reset filters
  const handleResetFilters = useCallback(() => {
    setFilters({
      page: 1,
      pageSize: filters.pageSize,
    });
    setDateRange(null);
  }, [filters.pageSize]);

  // Export documents
  const handleExport = useCallback(() => {
    console.log('Export documents');
  }, []);

  // Navigate to document detail
  const handleViewDocument = useCallback((documentId: string) => {
    navigate(`/regulatory/documents/${documentId}`);
  }, [navigate]);

  // Preview document
  const handlePreviewDocument = useCallback((document: Document) => {
    setPreviewDocument(document);
    setPreviewVisible(true);
  }, []);

  // Download document
  const handleDownloadDocument = useCallback((document: Document) => {
    if (document.url) {
      window.open(document.url, '_blank');
    }
  }, []);

  // Get document type icon
  const getDocumentTypeIcon = (type?: string) => {
    if (type?.toLowerCase().includes('pdf')) {
      return <FilePdfOutlined style={{ color: '#ff4d4f' }} />;
    }
    return <FileTextOutlined />;
  };

  // Get confidentiality icon
  const getConfidentialityIcon = (level?: string) => {
    if (level === 'public') {
      return <UnlockOutlined style={{ color: '#52c41a' }} />;
    }
    return <LockOutlined style={{ color: '#faad14' }} />;
  };

  // Table columns
  const columns: ColumnsType<Document> = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      sorter: true,
      render: (text: string, record: Document) => (
        <Button
          type="link"
          onClick={() => handleViewDocument(record.id)}
          style={{ padding: 0, textAlign: 'left', width: '100%' }}
        >
          <Space>
            {getDocumentTypeIcon(record.format)}
            <Text ellipsis style={{ maxWidth: 300 }}>{text || 'N/A'}</Text>
          </Space>
        </Button>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'documentType',
      key: 'documentType',
      width: 200,
      filterIcon: <FilterOutlined />,
      render: (type: string) => (
        <Tag color="blue">{type || 'N/A'}</Tag>
      ),
    },
    {
      title: 'Agency',
      dataIndex: 'agencyId',
      key: 'agencyId',
      width: 150,
      render: (agencyId: string) => {
        const agency = agencies.find(a => a.id === agencyId);
        return (
          <Tooltip title={agency?.country}>
            <Space>
              <BankOutlined />
              {agency?.name || 'N/A'}
            </Space>
          </Tooltip>
        );
      },
    },
    {
      title: 'Date',
      dataIndex: 'documentDate',
      key: 'documentDate',
      width: 130,
      sorter: true,
      render: (date: string) => (
        <Space>
          <CalendarOutlined />
          {date ? dayjs(date).format('YYYY-MM-DD') : 'N/A'}
        </Space>
      ),
    },
    {
      title: 'Pages',
      dataIndex: 'pages',
      key: 'pages',
      width: 100,
      render: (pages?: number) => pages ? `${pages} p` : '-',
    },
    {
      title: 'Size',
      dataIndex: 'fileSize',
      key: 'fileSize',
      width: 100,
      render: (size?: number) => {
        if (!size) return '-';
        const mb = (size / (1024 * 1024)).toFixed(2);
        return `${mb} MB`;
      },
    },
    {
      title: 'Confidentiality',
      dataIndex: 'confidentiality',
      key: 'confidentiality',
      width: 150,
      render: (level: string) => (
        <Space>
          {getConfidentialityIcon(level)}
          <Tag color={level === 'public' ? 'success' : 'warning'}>
            {level || 'Unknown'}
          </Tag>
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record: Document) => (
        <Space size="small">
          <Tooltip title="Preview">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handlePreviewDocument(record)}
              disabled={!record.summary}
            />
          </Tooltip>
          <Tooltip title="Download">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={() => handleDownloadDocument(record)}
              disabled={!record.url}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  if (documentsError) {
    return (
      <Card>
        <EmptyState
          title="Error Loading Documents"
          description={(documentsError as ApiError).message || 'An error occurred while fetching documents'}
          action={{
            label: 'Retry',
            onClick: () => refetchDocuments(),
          }}
        />
      </Card>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <Card>
          <Row justify="space-between" align="middle">
            <Col>
              <Space direction="vertical" size={0}>
                <h2 style={{ margin: 0 }}>Regulatory Documents</h2>
                <span style={{ color: '#8c8c8c' }}>
                  Browse and search regulatory documents including FDA CRLs and PDA technical reports
                </span>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => refetchDocuments()}
                  loading={documentsLoading}
                >
                  Refresh
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={handleExport}
                >
                  Export
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Statistics */}
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Documents"
                value={total}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Public Documents"
                value={documents.filter(d => d.confidentiality === 'public').length}
                valueStyle={{ color: '#52c41a' }}
                prefix={<UnlockOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="FDA CRLs"
                value={documents.filter(d => d.documentType?.toLowerCase().includes('crl')).length}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="PDA Reports"
                value={documents.filter(d => d.documentType?.toLowerCase().includes('pda')).length}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Filters */}
        <Card title={<><FilterOutlined /> Filters</>}>
          <Row gutter={16}>
            <Col span={6}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Search</small>
                <Input
                  placeholder="Search by title, content..."
                  prefix={<SearchOutlined />}
                  onChange={(e) => handleSearch(e.target.value)}
                  allowClear
                />
              </Space>
            </Col>
            <Col span={4}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Document Type</small>
                <Select
                  placeholder="All Types"
                  allowClear
                  onChange={(value) => handleFilterChange('type', value)}
                  value={filters.type}
                  style={{ width: '100%' }}
                >
                  <Option value="CRL">Complete Response Letter</Option>
                  <Option value="PDA">PDA Technical Report</Option>
                  <Option value="Submission">Submission Document</Option>
                  <Option value="Approval">Approval Document</Option>
                  <Option value="Compliance">Compliance Report</Option>
                  <Option value="Guidance">Regulatory Guidance</Option>
                </Select>
              </Space>
            </Col>
            <Col span={4}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Agency</small>
                <Select
                  placeholder="All Agencies"
                  allowClear
                  loading={agenciesLoading}
                  onChange={(value) => handleFilterChange('agency', value)}
                  value={filters.agency}
                  style={{ width: '100%' }}
                >
                  {agencies.map((agency: Agency) => (
                    <Option key={agency.id} value={agency.id}>
                      {agency.name}
                    </Option>
                  ))}
                </Select>
              </Space>
            </Col>
            <Col span={4}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Confidentiality</small>
                <Select
                  placeholder="All Levels"
                  allowClear
                  onChange={(value) => handleFilterChange('confidentiality', value)}
                  value={filters.confidentiality}
                  style={{ width: '100%' }}
                >
                  <Option value="public">Public</Option>
                  <Option value="confidential">Confidential</Option>
                  <Option value="secret">Secret</Option>
                </Select>
              </Space>
            </Col>
            <Col span={6}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Date Range</small>
                <RangePicker
                  style={{ width: '100%' }}
                  value={dateRange}
                  onChange={handleDateRangeChange}
                />
              </Space>
            </Col>
          </Row>
          <Row style={{ marginTop: 16 }}>
            <Col span={24}>
              <Button onClick={handleResetFilters}>Reset Filters</Button>
            </Col>
          </Row>
        </Card>

        {/* Documents Table */}
        <Card
          title={`Documents (${total} total)`}
          extra={
            <Space>
              <span>Page {filters.page} of {Math.ceil(total / (filters.pageSize || 20))}</span>
            </Space>
          }
        >
          <LoadingSpinner loading={documentsLoading}>
            <Table
              columns={columns}
              dataSource={documents}
              rowKey="id"
              pagination={{
                current: filters.page,
                pageSize: filters.pageSize,
                total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `Total ${total} documents`,
                pageSizeOptions: ['10', '20', '50', '100'],
              }}
              onChange={handleTableChange}
              scroll={{ x: 1400 }}
            />
          </LoadingSpinner>
        </Card>

        {/* Document Preview Modal */}
        <Modal
          title={
            <Space>
              {getDocumentTypeIcon(previewDocument?.format)}
              {previewDocument?.title}
            </Space>
          }
          open={previewVisible}
          onCancel={() => setPreviewVisible(false)}
          footer={[
            <Button key="close" onClick={() => setPreviewVisible(false)}>
              Close
            </Button>,
            <Button
              key="download"
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => {
                if (previewDocument) {
                  handleDownloadDocument(previewDocument);
                }
              }}
              disabled={!previewDocument?.url}
            >
              Download
            </Button>,
          ]}
          width={800}
        >
          {previewDocument && (
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Descriptions column={2}>
                <Descriptions.Item label="Type">
                  <Tag>{previewDocument.documentType}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Date">
                  {previewDocument.documentDate ? dayjs(previewDocument.documentDate).format('YYYY-MM-DD') : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Pages">
                  {previewDocument.pages || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Size">
                  {previewDocument.fileSize ? `${(previewDocument.fileSize / (1024 * 1024)).toFixed(2)} MB` : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Confidentiality">
                  <Space>
                    {getConfidentialityIcon(previewDocument.confidentiality)}
                    {previewDocument.confidentiality}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Format">
                  {previewDocument.format || 'N/A'}
                </Descriptions.Item>
              </Descriptions>

              <Divider />

              <div>
                <Text strong>Summary</Text>
                <Paragraph style={{ marginTop: 8 }}>
                  {previewDocument.summary || 'No summary available for this document.'}
                </Paragraph>
              </div>
            </Space>
          )}
        </Modal>
      </Space>
    </div>
  );
};

// Helper component for descriptions
const Descriptions: React.FC<{
  column?: number;
  children: React.ReactNode;
}> = ({ column = 2, children }) => {
  return (
    <Row gutter={[16, 16]}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return (
            <Col span={24 / column}>
              {child}
            </Col>
          );
        }
        return null;
      })}
    </Row>
  );
};

const DescriptionsItem: React.FC<{
  label: string;
  children: React.ReactNode;
}> = ({ label, children }) => {
  return (
    <div>
      <Text type="secondary" style={{ fontSize: 12 }}>
        {label}
      </Text>
      <br />
      <div>{children}</div>
    </div>
  );
};

export default DocumentsPage;
