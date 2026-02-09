/**
 * ApprovalsPage.tsx - Regulatory Approvals Catalog
 * Displays searchable/filterable table of regulatory approvals with statistics
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
  Progress
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  EyeOutlined,
  DownloadOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  CalendarOutlined,
  BankOutlined,
  MedicineBoxOutlined
} from '@ant-design/icons';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import dayjs from 'dayjs';
import { useApprovals, useAgencies, useRegulatoryStatistics } from './hooks';
import { Approval, ApprovalFilters, Agency, ApiError, PaginatedResponse, RegulatoryStatistics } from './types';
import { LoadingSpinner, EmptyState } from '@/shared/components';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface FilterState extends ApprovalFilters {
  search?: string;
}

const ApprovalsPage: React.FC = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<FilterState>({
    page: 1,
    pageSize: 20,
  });
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);

  // Queries
  const {
    data: approvalsData,
    isLoading: approvalsLoading,
    error: approvalsError,
    refetch: refetchApprovals
  } = useApprovals(filters, {
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
  const approvals = approvalsData?.items || [];
  const total = approvalsData?.total || 0;
  const stats = statistics as RegulatoryStatistics | undefined;

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

  // Export approvals
  const handleExport = useCallback(() => {
    // Implement export functionality
    console.log('Export approvals');
  }, []);

  // Navigate to approval detail
  const handleViewApproval = useCallback((approvalId: string) => {
    navigate(`/regulatory/approvals/${approvalId}`);
  }, [navigate]);

  // Get approval type color
  const getApprovalTypeColor = (type?: string) => {
    const colorMap: Record<string, string> = {
      'Full Approval': 'success',
      'Accelerated Approval': 'blue',
      'Conditional Approval': 'warning',
      'Emergency Use Authorization': 'purple',
      'Orphan Drug': 'orange',
    };
    return colorMap[type || ''] || 'default';
  };

  // Table columns
  const columns: ColumnsType<Approval> = [
    {
      title: 'Approval Number',
      dataIndex: 'approvalNumber',
      key: 'approvalNumber',
      sorter: true,
      width: 180,
      render: (text: string, record: Approval) => (
        <Button
          type="link"
          onClick={() => handleViewApproval(record.id)}
          style={{ padding: 0 }}
        >
          {text || 'N/A'}
        </Button>
      ),
    },
    {
      title: 'Drug',
      dataIndex: 'drugName',
      key: 'drugName',
      width: 200,
      render: (drugName: string) => (
        <Space>
          <MedicineBoxOutlined />
          {drugName || 'N/A'}
        </Space>
      ),
    },
    {
      title: 'Agency',
      dataIndex: 'agencyName',
      key: 'agencyName',
      width: 150,
      render: (agencyName: string) => (
        <Space>
          <BankOutlined />
          {agencyName || 'N/A'}
        </Space>
      ),
    },
    {
      title: 'Approval Type',
      dataIndex: 'approvalType',
      key: 'approvalType',
      width: 200,
      render: (type: string) => (
        <Tag color={getApprovalTypeColor(type)}>{type || 'N/A'}</Tag>
      ),
    },
    {
      title: 'Therapeutic Area',
      dataIndex: 'therapeuticArea',
      key: 'therapeuticArea',
      width: 180,
      render: (area: string) => area ? <Tag color="cyan">{area}</Tag> : 'N/A',
    },
    {
      title: 'Approval Date',
      dataIndex: 'approvalDate',
      key: 'approvalDate',
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
      title: 'Expiry Date',
      dataIndex: 'expiryDate',
      key: 'expiryDate',
      width: 130,
      render: (date?: string) => {
        if (!date) return 'N/A';
        const expiryDate = dayjs(date);
        const today = dayjs();
        const daysUntilExpiry = expiryDate.diff(today, 'days');

        let color = 'default';
        if (daysUntilExpiry < 0) color = 'error';
        else if (daysUntilExpiry < 180) color = 'warning';
        else if (daysUntilExpiry < 365) color = 'processing';

        return (
          <Tag color={color}>
            {expiryDate.format('YYYY-MM-DD')}
          </Tag>
        );
      },
    },
    {
      title: 'Conditions',
      dataIndex: 'conditions',
      key: 'conditions',
      width: 120,
      render: (conditions?: string[]) => {
        if (!conditions || conditions.length === 0) return '-';
        return (
          <Tooltip title={conditions.join(', ')}>
            <Tag color="orange">{conditions.length} conditions</Tag>
          </Tooltip>
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render: (_, record: Approval) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewApproval(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  if (approvalsError) {
    return (
      <Card>
        <EmptyState
          title="Error Loading Approvals"
          description={(approvalsError as ApiError).message || 'An error occurred while fetching approvals'}
          action={{
            label: 'Retry',
            onClick: () => refetchApprovals(),
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
                <h2 style={{ margin: 0 }}>Regulatory Approvals</h2>
                <span style={{ color: '#8c8c8c' }}>
                  Browse and search regulatory approvals across agencies
                </span>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => refetchApprovals()}
                  loading={approvalsLoading}
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
                title="Total Approvals"
                value={stats?.totalApprovals || total}
                prefix={<TrophyOutlined />}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="This Year"
                value={stats?.approvalsByYear?.[new Date().getFullYear().toString()] || 0}
                prefix={<CheckCircleOutlined />}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="With Conditions"
                value={approvals.filter(a => a.conditions && a.conditions.length > 0).length}
                loading={approvalsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Statistic
                  title="Approval Rate"
                  value={stats?.complianceRate || 0}
                  suffix="%"
                  loading={statsLoading}
                />
                <Progress
                  percent={Math.round(stats?.complianceRate || 0)}
                  size="small"
                  status="active"
                />
              </Space>
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
                <small>Approval Type</small>
                <Select
                  placeholder="All Types"
                  allowClear
                  onChange={(value) => handleFilterChange('approvalType', value)}
                  value={filters.approvalType}
                  style={{ width: '100%' }}
                >
                  <Option value="Full Approval">Full Approval</Option>
                  <Option value="Accelerated Approval">Accelerated Approval</Option>
                  <Option value="Conditional Approval">Conditional Approval</Option>
                  <Option value="Emergency Use Authorization">Emergency Use Authorization</Option>
                  <Option value="Orphan Drug">Orphan Drug</Option>
                </Select>
              </Space>
            </Col>
            <Col span={4}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <small>Therapeutic Area</small>
                <Select
                  placeholder="All Areas"
                  allowClear
                  onChange={(value) => handleFilterChange('therapeuticArea', value)}
                  value={filters.therapeuticArea}
                  style={{ width: '100%' }}
                >
                  <Option value="Oncology">Oncology</Option>
                  <Option value="Cardiology">Cardiology</Option>
                  <Option value="Neurology">Neurology</Option>
                  <Option value="Infectious Diseases">Infectious Diseases</Option>
                  <Option value="Respiratory">Respiratory</Option>
                  <Option value="Gastroenterology">Gastroenterology</Option>
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

        {/* Approvals Table */}
        <Card
          title={`Approvals (${total} total)`}
          extra={
            <Space>
              <span>Page {filters.page} of {Math.ceil(total / (filters.pageSize || 20))}</span>
            </Space>
          }
        >
          <LoadingSpinner loading={approvalsLoading}>
            <Table
              columns={columns}
              dataSource={approvals}
              rowKey="id"
              pagination={{
                current: filters.page,
                pageSize: filters.pageSize,
                total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `Total ${total} approvals`,
                pageSizeOptions: ['10', '20', '50', '100'],
              }}
              onChange={handleTableChange}
              scroll={{ x: 1400 }}
            />
          </LoadingSpinner>
        </Card>
      </Space>
    </div>
  );
};

export default ApprovalsPage;
