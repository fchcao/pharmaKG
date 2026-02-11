/**
 * ManufacturersPage.tsx
 * Supply Chain - Manufacturers Catalog Page
 *
 * Features:
 * - Searchable/filterable table of manufacturers
 * - Filters: location, certifications, quality score
 * - Geographic distribution view (bar chart)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Input,
  Select,
  Slider,
  Space,
  Tag,
  Button,
  Row,
  Col,
  Statistic,
  Tooltip,
  Badge,
  message
} from 'antd';
import {
  SearchOutlined,
  EnvironmentOutlined,
  SafetyOutlined,
  StarOutlined,
  GlobalOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { ColumnsType } from 'antd/es/table';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend
} from 'chart.js';
import { supplyChainApi } from '../api';
import type { Manufacturer } from '../types';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend
);

const { Search } = Input;
const { Option } = Select;

interface FilterState {
  search: string;
  country: string | undefined;
  manufacturerType: string | undefined;
  qualityScoreMin: number;
  status: string | undefined;
}

/**
 * Manufacturers Catalog Page Component
 */
export const ManufacturersPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    country: undefined,
    manufacturerType: undefined,
    qualityScoreMin: 0,
    status: undefined
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20
  });
  const [showGeoMap, setShowGeoMap] = useState(false);

  // Fetch manufacturers with React Query
  const {
    data: manufacturersData,
    isLoading,
    refetch,
    isError
  } = useQuery({
    queryKey: ['manufacturers', pagination.current, pagination.pageSize, filters],
    queryFn: () =>
      supplyChainApi.getManufacturers({
        page: pagination.current,
        page_size: pagination.pageSize,
        search: filters.search || undefined,
        country: filters.country,
        manufacturer_type: filters.manufacturerType,
        quality_score_min: filters.qualityScoreMin > 0 ? filters.qualityScoreMin : undefined,
        status: filters.status
      }),
    keepPreviousData: true
  });

  // Fetch geographic distribution
  const { data: geoData } = useQuery({
    queryKey: ['manufacturers-geo'],
    queryFn: () => supplyChainApi.getGeographicDistribution(),
    enabled: showGeoMap
  });

  const manufacturers = manufacturersData?.data || [];
  const total = manufacturersData?.total || 0;

  // Handle filter changes
  const handleFilterChange = (key: keyof FilterState, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, current: 1 })); // Reset to first page
  };

  // Handle search
  const handleSearch = (value: string) => {
    handleFilterChange('search', value);
  };

  // Handle table change
  const handleTableChange = (newPagination: any) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize
    });
  };

  // Navigate to manufacturer detail
  const handleRowClick = (record: Manufacturer) => {
    navigate(`/supply/manufacturers/${record.id}`);
  };

  // Table columns
  const columns: ColumnsType<Manufacturer> = [
    {
      title: 'Manufacturer',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (text: string, record: Manufacturer) => (
        <Space>
          <a onClick={() => navigate(`/supply/manufacturers/${record.id}`)}>{text}</a>
          {record.status === 'active' && (
            <Badge status="success" />
          )}
        </Space>
      )
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      filters: [
        { text: 'Innovator', value: 'innovator' },
        { text: 'Generic', value: 'generic' },
        { text: 'Biotech', value: 'biotech' },
        { text: 'CDMO', value: 'cdmo' }
      ],
      render: (type: string) => (
        <Tag color={getTypeColor(type)}>{type?.toUpperCase()}</Tag>
      )
    },
    {
      title: 'Location',
      key: 'location',
      render: (_, record: Manufacturer) => (
        <Space>
          <EnvironmentOutlined />
          <span>{record.location || 'N/A'}</span>
        </Space>
      )
    },
    {
      title: 'Quality Score',
      dataIndex: 'qualityScore',
      key: 'qualityScore',
      sorter: true,
      render: (score: number) => (
        <Space>
          <StarOutlined style={{ color: score >= 80 ? '#52c41a' : score >= 60 ? '#faad14' : '#f5222d' }} />
          <span>{score || 'N/A'}</span>
        </Space>
      )
    },
    {
      title: 'Certifications',
      dataIndex: 'certifications',
      key: 'certifications',
      render: (certs: string[]) => (
        <Space size="small">
          {certs?.slice(0, 2).map(cert => (
            <Tag key={cert} icon={<SafetyOutlined />} color="blue">
              {cert}
            </Tag>
          ))}
          {certs?.length > 2 && (
            <Tooltip title={certs.slice(2).join(', ')}>
              <Tag>+{certs.length - 2}</Tag>
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'active' ? 'green' : status === 'inactive' ? 'red' : 'default';
        return <Badge status={color as any} text={status?.toUpperCase()} />;
      }
    }
  ];

  const getTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      innovator: 'blue',
      generic: 'green',
      biotech: 'purple',
      cdmo: 'orange'
    };
    return colors[type?.toLowerCase()] || 'default';
  };

  // Prepare chart data for geographic distribution
  const chartData = React.useMemo(() => {
    if (!geoData?.data) return null;

    // Take top 20 locations by count
    const topLocations = geoData.data.slice(0, 20);

    return {
      labels: topLocations.map((item: any) => {
        // Extract state from location like "Princeton, NJ 08540" -> "NJ"
        const parts = item.country.split(', ');
        if (parts.length >= 2) {
          // Get state code (e.g., "NJ 08540" -> "NJ")
          const statePart = parts[parts.length - 1].split(' ')[0];
          return `${parts[parts.length - 2]}, ${statePart}`;
        }
        return item.country;
      }),
      datasets: [{
        label: 'Manufacturers',
        data: topLocations.map((item: any) => item.count),
        backgroundColor: 'rgba(24, 144, 255, 0.6)',
        borderColor: 'rgba(24, 144, 255, 1)',
        borderWidth: 1
      }]
    };
  }, [geoData]);

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Header */}
        <Card>
          <Row gutter={16} align="middle">
            <Col span={12}>
              <Space>
                <SafetyOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
                <div>
                  <h2 style={{ margin: 0 }}>Manufacturers Catalog</h2>
                  <p style={{ margin: 0, color: '#8c8c8c' }}>
                    Browse and filter pharmaceutical manufacturers worldwide
                  </p>
                </div>
              </Space>
            </Col>
            <Col span={12} style={{ textAlign: 'right' }}>
              <Button
                icon={<GlobalOutlined />}
                onClick={() => setShowGeoMap(!showGeoMap)}
              >
                {showGeoMap ? 'Hide' : 'Show'} Geographic View
              </Button>
            </Col>
          </Row>
        </Card>

        {/* Statistics */}
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Manufacturers"
                value={total}
                prefix={<SafetyOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Active Manufacturers"
                value={manufacturers.filter(m => m.status === 'active').length}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Countries Represented"
                value={new Set(manufacturers.map(m => m.location?.split(',').pop())).size}
                prefix={<EnvironmentOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Avg Quality Score"
                value={
                  manufacturers.length > 0
                    ? (
                        manufacturers.reduce((sum, m) => sum + (m.qualityScore || 0), 0) /
                        manufacturers.length
                      ).toFixed(1)
                    : 0
                }
                suffix="/ 100"
                prefix={<StarOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Geographic Distribution Map */}
        {showGeoMap && (
          <Card
            title="Geographic Distribution"
            extra={
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={() => queryClient.invalidateQueries(['manufacturers-geo'])}
              >
                Refresh
              </Button>
            }
          >
            {chartData && (
              <div style={{ height: 400 }}>
                <Bar
                  data={chartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: false
                      },
                      title: {
                        display: true,
                        text: 'Top 20 Locations by Manufacturer Count',
                        font: { size: 16 }
                      },
                      tooltip: {
                        callbacks: {
                          label: (context) => {
                            return `${context.parsed.y} manufacturers`;
                          }
                        }
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: 'Number of Manufacturers'
                        }
                      },
                      x: {
                        ticks: {
                          maxRotation: 45,
                          minRotation: 45
                        }
                      }
                    }
                  }}
                />
              </div>
            )}
          </Card>
        )}

        {/* Filters */}
        <Card title="Filters">
          <Row gutter={16}>
            <Col span={8}>
              <div style={{ marginBottom: 8 }}>
                <strong>Search Manufacturers:</strong>
              </div>
              <Search
                placeholder="Search by name..."
                allowClear
                onSearch={handleSearch}
                style={{ width: '100%' }}
                prefix={<SearchOutlined />}
              />
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Country:</strong>
              </div>
              <Select
                placeholder="Select country"
                allowClear
                style={{ width: '100%' }}
                value={filters.country}
                onChange={(value) => handleFilterChange('country', value)}
              >
                <Option value="USA">United States</Option>
                <Option value="China">China</Option>
                <Option value="Germany">Germany</Option>
                <Option value="India">India</Option>
                <Option value="Japan">Japan</Option>
                <Option value="UK">United Kingdom</Option>
              </Select>
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Manufacturer Type:</strong>
              </div>
              <Select
                placeholder="Select type"
                allowClear
                style={{ width: '100%' }}
                value={filters.manufacturerType}
                onChange={(value) => handleFilterChange('manufacturerType', value)}
              >
                <Option value="innovator">Innovator</Option>
                <Option value="generic">Generic</Option>
                <Option value="biotech">Biotech</Option>
                <Option value="cdmo">CDMO</Option>
              </Select>
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Quality Score:</strong>
              </div>
              <Slider
                min={0}
                max={100}
                value={filters.qualityScoreMin}
                onChange={(value) => handleFilterChange('qualityScoreMin', value)}
                marks={{ 0: '0', 50: '50', 100: '100' }}
              />
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Status:</strong>
              </div>
              <Select
                placeholder="Select status"
                allowClear
                style={{ width: '100%' }}
                value={filters.status}
                onChange={(value) => handleFilterChange('status', value)}
              >
                <Option value="active">Active</Option>
                <Option value="inactive">Inactive</Option>
                <Option value="under-review">Under Review</Option>
              </Select>
            </Col>
          </Row>
        </Card>

        {/* Manufacturers Table */}
        <Card
          title={`Manufacturers (${total} total)`}
          extra={
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              Refresh
            </Button>
          }
        >
          <Table
            columns={columns}
            dataSource={manufacturers}
            rowKey="id"
            loading={isLoading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} manufacturers`
            }}
            onChange={handleTableChange}
            onRow={(record) => ({
              onClick: () => handleRowClick(record),
              style: { cursor: 'pointer' }
            })}
          />
        </Card>
      </Space>
    </div>
  );
};

export default ManufacturersPage;
