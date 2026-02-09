/**
 * SubmissionsPage.tsx - Regulatory Submissions Catalog
 * Displays searchable/filterable table of regulatory submissions with status indicators
 */

import React, { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Badge,
  message
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  EyeOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import dayjs from 'dayjs';
import { useSubmissions, useAgencies, useRegulatoryStatistics } from './hooks';
import { Submission, SubmissionFilters, Agency, ApiError, PaginatedResponse, RegulatoryStatistics } from './types';
import { LoadingSpinner, EmptyState } from '@/shared/components';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface FilterState extends SubmissionFilters {
  search?: string;
}

const SubmissionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<FilterState>({
    page: 1,
    pageSize: 20,
  });
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

  // Queries
  const {
    data: submissionsData,
    isLoading: submissionsLoading,
    error: submissionsError,
    refetch: refetchSubmissions
  } = useSubmissions(filters, {
    enabled: true,
  });

  const {
    data: agenciesData,
    isLoading: agenciesLoading
  } = useAgencies({}, {
    enabled: true,
  });

  const {
    data: statistics,
    isLoading: statsLoading
  } = useRegulatoryStatistics();

  const agencies = agenciesData?.items || [];
  const submissions = submissionsData?.items || [];
  const total = submissionsData?.total || 0;
  const stats = statistics as RegulatoryStatistics | undefined;

  // Handle filter changes
  const handleFilterChange = useCallback((key: string, value: unknown) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: 1, // Reset to first page on filter change
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

  // Export submissions
  const handleExport = useCallback(() => {
    message.info('Export functionality will be implemented');
  }, []);

  // Navigate to submission detail
  const handleViewSubmission = useCallback((submissionId: string) => {
    navigate(`/regulatory/submissions/${submissionId}`);
  }, [navigate]);

  // Get status icon and color
  const getStatusConfig = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'approved':
        return { icon: <CheckCircleOutlined />, color: 'success', text: 'Approved' };
      case 'pending':
      case 'under review':
        return { icon: <ClockCircleOutlined />, color: 'processing', text: 'Under Review' };
      case 'rejected':
      case 'withdrawn':
        return { icon: <CloseCircleOutlined />, color: 'error', text: status };
      case 'in progress':
        return { icon: <SyncOutlined spin />, color: 'processing', text: 'In Progress' };
      default:
        return { icon: <FileTextOutlined />, color: 'default', text: status || 'Unknown' };
    }
  };

  // Table columns
  const columns: ColumnsType<Submission> = [
    {
      title: 'Submission Number',
      dataIndex: 'submissionNumber',
      key: 'submissionNumber',
      sorter: true,
      width: 180,
      render: (text: string, record: Submission) => (
        <Button
          type="link"
          onClick={() => handleViewSubmission(record.id)}
          style={{ padding: 0 }}
        >
          {text || 'N/A'}
        </Button>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'submissionType',
      key: 'submissionType',
      width: 150,
      filterIcon: <FilterOutlined />,
      render: (type: string) => (
        <Tag color="blue">{type || 'N/A'}</Tag>
      ),
    },
    {
      title: 'Agency',
      dataIndex: ['agency', 'name'],
      key: 'agency',
      width: 150,
      render: (agencyName: string, record: Submission) => (
        <Tooltip title={record.agency?.country}>
          <span>{agencyName || 'N/A'}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Drug',
      dataIndex: 'drugName',
      key: 'drugName',
      width: 200,
      render: (drugName: string) => drugName || 'N/A',
    },
    {
      title: 'Submission Date',
      dataIndex: 'submissionDate',
      key: 'submissionDate',
      width: 130,
      sorter: true,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD') : 'N/A',
    },
    {
      title: 'Review Date',
      dataIndex: 'reviewDate',
      key: 'reviewDate',
      width: 130,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD') : 'N/A',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      filterIcon: <FilterOutlined />,
      render: (status: string) => {
        const config = getStatusConfig(status);
        return (
          <Badge
            status={config.color as any}
            text={
              <span>
                {config.icon} {config.text}
              </span>
            }
          />
        );
      },
    },
    {
      title: 'Compliance',
      key: 'compliance',
      width: 120,
      render: (_, record: Submission) => {
        const compliance = record.complianceStatus;
        if (!compliance) return <Tag>Unknown</Tag>;

        const colorMap: Record<string, string> = {
          compliant: 'success',
          warning: 'warning',
          'non-compliant': 'error',
          pending: 'default',
        };

        return (
          <Tag color={colorMap[compliance.status] || 'default'}>
            {compliance.status}
          </Tag>
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render: (_, record: Submission) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewSubmission(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  if (submissionsError) {
    return (
      <Card>
        <EmptyState
          title="Error Loading Submissions"
          description={(submissionsError as ApiError).message || 'An error occurred while fetching submissions'}
          action={{
            label: 'Retry',
            onClick: () => refetchSubmissions(),
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
                <h2 style={{ margin: 0 }}>Regulatory Submissions</h2>
                <span style={{ color: '#8c8c8c' }}>
                  Browse and search regulatory submissions across agencies
                </span>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => refetchSubmissions()}
                  loading={submissionsLoading}
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
                title="Total Submissions"
                value={stats?.totalSubmissions || total}
                prefix={<FileTextOutlined />}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Pending Review"
                value={stats?.pendingSubmissions || 0}
                valueStyle={{ color: '#faad14' }}
                prefix={<ClockCircleOutlined />}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Approved"
                value={stats?.approvedSubmissions || 0}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Avg. Review Time"
                value={stats?.averageReviewTime || 0}
                suffix="days"
                loading={statsLoading}
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
                  placeholder="Search by drug, number..."
                  prefix={<SearchOutlined />}
                  onChange={(e) => handleSearch(e.target.value)}
                  allowClear
                />
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
                <small>Submission Type</small>
                <Select
                  placeholder="All Types"
                  allowClear
                  onChange={(value) => handleFilterChange('type', value)}
                  value={filters.type}
                  style={{ width: '100%' }}
                >
                  <Option value="NDA">NDA</Option>
                  <Option value="BLA">BLA</Option>
                  <Option value="ANDA">ANDA</Option>
                  <Option value="sNDA">sNDA</Option>
                  <Option value="510(k)">510(k)</Option>
                  <Option value="PMA">PMA</Option>
                </Select>
              </Space>
            </Col>
            <Col span={4}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Status</small>
                <Select
                  placeholder="All Statuses"
                  allowClear
                  onChange={(value) => handleFilterChange('status', value)}
                  value={filters.status}
                  style={{ width: '100%' }}
                >
                  <Option value="approved">Approved</Option>
                  <Option value="pending">Pending</Option>
                  <Option value="under review">Under Review</Option>
                  <Option value="rejected">Rejected</Option>
                  <Option value="withdrawn">Withdrawn</Option>
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

        {/* Submissions Table */}
        <Card
          title={`Submissions (${total} total)`}
          extra={
            <Space>
              <span>Page {filters.page} of {Math.ceil(total / (filters.pageSize || 20))}</span>
            </Space>
          }
        >
          <LoadingSpinner loading={submissionsLoading}>
            <Table
              columns={columns}
              dataSource={submissions}
              rowKey="id"
              pagination={{
                current: filters.page,
                pageSize: filters.pageSize,
                total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `Total ${total} submissions`,
                pageSizeOptions: ['10', '20', '50', '100'],
              }}
              onChange={handleTableChange}
              scroll={{ x: 1200 }}
            />
          </LoadingSpinner>
        </Card>
      </Space>
    </div>
  );
};

export default SubmissionsPage;
