/**
 * CRLsPage.tsx - FDA Complete Response Letters Catalog
 * Displays searchable/filterable table of FDA Complete Response Letters
 */

import React, { useState, useCallback } from 'react';
import {
  Card,
  Table,
  Space,
  Button,
  Tag,
  Input,
  Select,
  Row,
  Col,
  Statistic,
  Tooltip,
  Modal,
  Typography,
  Descriptions,
  Badge
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  EyeOutlined,
  DownloadOutlined,
  ReloadOutlined,
  MailOutlined,
  BankOutlined,
  CalendarOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import dayjs from 'dayjs';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import { useCRLs, useCRL } from './hooks';
import { CRL, CRLFilters, ApiError, PaginatedResponse } from './types';
import { LoadingSpinner, EmptyState } from '@/shared/components';

const { Option } = Select;
const { Text, Paragraph } = Typography;

interface FilterState extends CRLFilters {
  search?: string;
}

const CRLsPage: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    page: 1,
    pageSize: 20,
  });
  const [selectedCRLId, setSelectedCRLId] = useState<string | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  // Queries
  const {
    data: crlsData,
    isLoading: crlsLoading,
    error: crlsError,
    refetch: refetchCRLs
  } = useCRLs(filters, {
    enabled: true,
  });

  // Fetch CRL statistics separately for accurate counts
  const { data: crlStats } = useQuery({
    queryKey: ['crls-statistics'],
    queryFn: async () => {
      return await apiClient.get('/regulatory/crls/statistics');
    },
    enabled: true,
  });

  const {
    data: selectedCRL,
    isLoading: crlLoading
  } = useCRL(selectedCRLId || '', {
    enabled: !!selectedCRLId && detailModalVisible,
  });

  const crls = crlsData?.items || [];
  const total = crlsData?.total || 0;

  // Use API statistics for accurate counts
  const approvedCount = crlStats?.approved || 0;
  const unapprovedCount = crlStats?.unapproved || 0;

  // Handle filter changes
  const handleFilterChange = useCallback((key: string, value: unknown) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: 1,
    }));
  }, []);

  // Handle search
  const handleSearch = useCallback((value: string) => {
    setFilters(prev => ({
      ...prev,
      company_name: value || undefined,
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
  }, [filters.pageSize]);

  // Export CRLs
  const handleExport = useCallback(() => {
    console.log('Export CRLs');
  }, []);

  // View CRL detail
  const handleViewCRL = useCallback((crlId: string) => {
    setSelectedCRLId(crlId);
    setDetailModalVisible(true);
  }, []);

  // Get approval status badge
  const getApprovalStatusBadge = (status?: string) => {
    const statusMap: Record<string, { status: 'success' | 'error' | 'warning' | 'default'; icon: React.ReactNode }> = {
      'Approved': { status: 'success', icon: <CheckCircleOutlined /> },
      'Unapproved': { status: 'error', icon: <CloseCircleOutlined /> },
      'Pending': { status: 'warning', icon: <ClockCircleOutlined /> },
    };
    const config = statusMap[status || ''] || { status: 'default', icon: null };
    return (
      <Badge
        status={config.status}
        text={
          <Space>
            {config.icon}
            {status || 'Unknown'}
          </Space>
        }
      />
    );
  };

  // Table columns
  const columns: ColumnsType<CRL> = [
    {
      title: 'Company',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 250,
      render: (companyName: string) => (
        <Space>
          <BankOutlined />
          <Text strong>{companyName || 'N/A'}</Text>
        </Space>
      ),
    },
    {
      title: 'Application Number',
      dataIndex: 'application_number',
      key: 'application_number',
      width: 180,
      render: (appNum: string) => (
        <Tag color="blue">{appNum || 'N/A'}</Tag>
      ),
    },
    {
      title: 'Letter Type',
      dataIndex: 'letter_type',
      key: 'letter_type',
      width: 180,
      render: (type: string) => (
        <Tag color="purple">{type || 'N/A'}</Tag>
      ),
    },
    {
      title: 'Approval Status',
      dataIndex: 'approval_status',
      key: 'approval_status',
      width: 150,
      render: (status: string) => getApprovalStatusBadge(status),
    },
    {
      title: 'Letter Date',
      dataIndex: 'letter_date',
      key: 'letter_date',
      width: 130,
      sorter: true,
      render: (date: string) => (
        <Space>
          <CalendarOutlined />
          {date || 'N/A'}
        </Space>
      ),
    },
    {
      title: 'Approver Center',
      dataIndex: 'approver_center',
      key: 'approver_center',
      width: 300,
      ellipsis: true,
      render: (center: string) => (
        <Tooltip title={center}>
          {center || 'N/A'}
        </Tooltip>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render: (_, record: CRL) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewCRL(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  if (crlsError) {
    return (
      <Card>
        <EmptyState
          title="Error Loading CRLs"
          description={(crlsError as ApiError).message || 'An error occurred while fetching CRLs'}
          action={{
            label: 'Retry',
            onClick: () => refetchCRLs(),
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
                <h2 style={{ margin: 0 }}>
                  <MailOutlined style={{ marginRight: 8 }} />
                  FDA Complete Response Letters
                </h2>
                <span style={{ color: '#8c8c8c' }}>
                  Browse FDA Complete Response Letters (CRLs) sent to pharmaceutical companies
                </span>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => refetchCRLs()}
                  loading={crlsLoading}
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
                title="Total CRLs"
                value={total}
                prefix={<FileTextOutlined />}
                loading={crlsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Subsequently Approved"
                value={approvedCount}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a' }}
                loading={crlsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Not Approved"
                value={unapprovedCount}
                prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                valueStyle={{ color: '#ff4d4f' }}
                loading={crlsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Approval Rate"
                value={total > 0 ? Math.round((approvedCount / total) * 100) : 0}
                suffix="%"
                loading={crlsLoading}
              />
            </Card>
          </Col>
        </Row>

        {/* Filters */}
        <Card title={<><FilterOutlined /> Filters</>}>
          <Row gutter={16}>
            <Col span={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Search by Company</small>
                <Input
                  placeholder="Search company name..."
                  prefix={<SearchOutlined />}
                  onChange={(e) => handleSearch(e.target.value)}
                  allowClear
                />
              </Space>
            </Col>
            <Col span={6}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Approval Status</small>
                <Select
                  placeholder="All Statuses"
                  allowClear
                  onChange={(value) => handleFilterChange('approval_status', value)}
                  value={filters.approval_status}
                  style={{ width: '100%' }}
                >
                  <Option value="Approved">Approved</Option>
                  <Option value="Unapproved">Unapproved</Option>
                  <Option value="Pending">Pending</Option>
                </Select>
              </Space>
            </Col>
            <Col span={6}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Letter Type</small>
                <Select
                  placeholder="All Types"
                  allowClear
                  onChange={(value) => handleFilterChange('letter_type', value)}
                  value={filters.letter_type}
                  style={{ width: '100%' }}
                >
                  <Option value="COMPLETE RESPONSE">Complete Response</Option>
                  <Option value="PARTIAL RESPONSE">Partial Response</Option>
                </Select>
              </Space>
            </Col>
            <Col span={4}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>&nbsp;</small>
                <Button onClick={handleResetFilters}>Reset Filters</Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* CRLs Table */}
        <Card
          title={`Complete Response Letters (${total} total)`}
          extra={
            <Space>
              <span>Page {filters.page} of {Math.ceil(total / (filters.pageSize || 20))}</span>
            </Space>
          }
        >
          <LoadingSpinner loading={crlsLoading}>
            <Table
              columns={columns}
              dataSource={crls}
              rowKey="id"
              pagination={{
                current: filters.page,
                pageSize: filters.pageSize,
                total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `Total ${total} CRLs`,
                pageSizeOptions: ['10', '20', '50', '100'],
              }}
              onChange={handleTableChange}
              scroll={{ x: 1300 }}
            />
          </LoadingSpinner>
        </Card>
      </Space>

      {/* CRL Detail Modal */}
      <Modal
        title={
          <Space>
            <MailOutlined />
            CRL Details
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setSelectedCRLId(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            Close
          </Button>
        ]}
        width={800}
        loading={crlLoading}
      >
        {selectedCRL && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="Company" span={2}>
              <Text strong>{selectedCRL.company_name}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Application Number">
              <Tag color="blue">{selectedCRL.application_number}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Letter Type">
              <Tag color="purple">{selectedCRL.letter_type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Letter Date">
              {selectedCRL.letter_date || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Approval Status">
              {getApprovalStatusBadge(selectedCRL.approval_status)}
            </Descriptions.Item>
            <Descriptions.Item label="Company Address" span={2}>
              {selectedCRL.company_address || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Company Representative">
              {selectedCRL.company_rep || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Approver Name">
              {selectedCRL.approver_name || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Approver Title" span={2}>
              {selectedCRL.approver_title || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Approver Center" span={2}>
              {selectedCRL.approver_center || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="Content Preview" span={2}>
              <Paragraph
                ellipsis={{ rows: 4, expandable: true, symbol: 'more' }}
                style={{ marginBottom: 0 }}
              >
                {selectedCRL.text_preview || 'No preview available'}
              </Paragraph>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default CRLsPage;
