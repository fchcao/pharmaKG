/**
 * ManufacturersPage.tsx
 * Supply Chain - Manufacturers Catalog Page
 *
 * Features:
 * - Searchable/filterable table of manufacturers
 * - Filters: location, certifications, quality score
 * - Geographic distribution view
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
import { useQuery, keepAliveManager } from '@tanstack/react-query';
import type { ColumnsType } from 'antd/es/table';
import { GraphViewer } from '@/shared/graphs';
import { supplyChainApi } from '../api';
import type { Manufacturer } from '../types';

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

  // Prepare graph data for geographic distribution
  const graphData = React.useMemo(() => {
    if (!geoData?.data) return { nodes: [], edges: [] };

    const nodes = geoData.data.map((item: any, index: number) => ({
      id: `country-${index}`,
      label: item.country,
      data: { count: item.count, manufacturers: item.manufacturers }
    }));

    return { nodes, edges: [] };
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
                onClick={() => keepAliveManager.invalidateQueries(['manufacturers-geo'])}
              >
                Refresh
              </Button>
            }
          >
            <GraphViewer
              data={graphData}
              layoutType="force"
              height={400}
              nodeLabelProperty="label"
              onNodeClick={(nodeId: string) => {
                const country = graphData.nodes.find((n: any) => n.id === nodeId)?.data?.country;
                if (country) {
                  handleFilterChange('country', country);
                }
              }}
            />
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
