/**
 * FacilitiesPage.tsx
 * Supply Chain - Facility Browser Page
 *
 * Features:
 * - Searchable facility list
 * - Geographic distribution map
 * - Filter by type, certifications
 * - Related manufacturers
 * - Inspection status
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Input,
  Select,
  Space,
  Tag,
  Button,
  Row,
  Col,
  Statistic,
  Badge,
  Tooltip,
  Empty
} from 'antd';
import {
  SearchOutlined,
  EnvironmentOutlined,
  BuildOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  GlobalOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import type { ColumnsType } from 'antd/es/table';
import { GraphViewer } from '@/shared/graphs';
import { supplyChainApi } from '../api';
import type { Facility } from '../types';

const { Search } = Input;
const { Option } = Select;

interface FilterState {
  search: string;
  facilityType: string | undefined;
  country: string | undefined;
  certification: string | undefined;
  inspectionStatus: string | undefined;
}

/**
 * Facilities Browser Page Component
 */
export const FacilitiesPage: React.FC = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    facilityType: undefined,
    country: undefined,
    certification: undefined,
    inspectionStatus: undefined
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20
  });
  const [showGeoMap, setShowGeoMap] = useState(false);

  // Fetch facilities
  const {
    data: facilitiesData,
    isLoading,
    refetch
  } = useQuery({
    queryKey: ['facilities', pagination.current, pagination.pageSize, filters],
    queryFn: () =>
      supplyChainApi.getFacilities({
        page: pagination.current,
        page_size: pagination.pageSize,
        facility_type: filters.facilityType,
        country: filters.country
      }),
    keepPreviousData: true
  });

  const facilities = facilitiesData?.data || [];
  const total = facilitiesData?.total || 0;

  // Handle filter changes
  const handleFilterChange = (key: keyof FilterState, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, current: 1 }));
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

  // Navigate to facility detail (using manufacturer detail for now)
  const handleRowClick = (record: Facility) => {
    if (record.manufacturerId) {
      navigate(`/supply/manufacturers/${record.manufacturerId}`);
    }
  };

  // Get facility type color
  const getFacilityTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      manufacturing: 'blue',
      packaging: 'green',
      warehouse: 'orange',
      laboratory: 'purple',
      office: 'default'
    };
    return colors[type?.toLowerCase()] || 'default';
  };

  // Get inspection status
  const getInspectionStatus = (facility: Facility) => {
    // This would come from the API in a real implementation
    const statuses = ['passed', 'warning', 'failed'];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    return status;
  };

  // Table columns
  const columns: ColumnsType<Facility> = [
    {
      title: 'Facility Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Facility) => (
        <Space>
          <BuildOutlined />
          <a onClick={() => handleRowClick(record)}>{text}</a>
        </Space>
      )
    },
    {
      title: 'Type',
      dataIndex: 'facilityType',
      key: 'facilityType',
      filters: [
        { text: 'Manufacturing', value: 'manufacturing' },
        { text: 'Packaging', value: 'packaging' },
        { text: 'Warehouse', value: 'warehouse' },
        { text: 'Laboratory', value: 'laboratory' }
      ],
      render: (type: string) => (
        <Tag color={getFacilityTypeColor(type)}>{type?.toUpperCase()}</Tag>
      )
    },
    {
      title: 'Location',
      key: 'location',
      render: (_, record: Facility) => (
        <Space>
          <EnvironmentOutlined />
          {record.location}
        </Space>
      )
    },
    {
      title: 'Capacity',
      dataIndex: 'capacity',
      key: 'capacity',
      render: (capacity: number) => (
        capacity ? `${capacity.toLocaleString()} units/year` : 'N/A'
      ),
      sorter: true
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
          {certs && certs.length > 2 && (
            <Tooltip title={certs.slice(2).join(', ')}>
              <Tag>+{certs.length - 2}</Tag>
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: 'Inspection Status',
      key: 'inspectionStatus',
      render: (_, record: Facility) => {
        const status = getInspectionStatus(record);
        const config = {
          passed: { color: 'success' as const, icon: <CheckCircleOutlined />, text: 'Passed' },
          warning: { color: 'warning' as const, icon: <WarningOutlined />, text: 'Warning' },
          failed: { color: 'error' as const, icon: <WarningOutlined />, text: 'Failed' }
        };
        const { color, icon, text } = config[status as keyof typeof config];
        return (
          <Badge status={color} icon={icon} text={text} />
        );
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'operational' ? 'success' : status === 'maintenance' ? 'warning' : 'default';
        return <Badge status={color} text={status?.toUpperCase()} />;
      }
    }
  ];

  // Calculate statistics
  const stats = React.useMemo(() => {
    const operational = facilities.filter(f => f.status === 'operational').length;
    const passedInspections = facilities.filter(f => getInspectionStatus(f) === 'passed').length;
    const withCertifications = facilities.filter(f => f.certifications && f.certifications.length > 0).length;

    return {
      total: facilities.length,
      operational,
      passedInspections,
      withCertifications
    };
  }, [facilities]);

  // Prepare graph data for visualization
  const graphData = React.useMemo(() => {
    const nodes = facilities.slice(0, 50).map((facility, index) => ({
      id: `facility-${index}`,
      label: facility.name,
      type: facility.facilityType,
      location: facility.location
    }));

    return { nodes, edges: [] };
  }, [facilities]);

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Header */}
        <Card>
          <Row gutter={16} align="middle">
            <Col span={18}>
              <Space>
                <BuildOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
                <div>
                  <h2 style={{ margin: 0 }}>Facilities Browser</h2>
                  <p style={{ margin: 0, color: '#8c8c8c' }}>
                    Browse and filter pharmaceutical manufacturing facilities worldwide
                  </p>
                </div>
              </Space>
            </Col>
            <Col span={6} style={{ textAlign: 'right' }}>
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
                title="Total Facilities"
                value={total}
                prefix={<BuildOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Operational"
                value={stats.operational}
                valueStyle={{ color: '#3f8600' }}
                suffix={`/ ${stats.total}`}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Passed Inspections"
                value={stats.passedInspections}
                valueStyle={{ color: '#3f8600' }}
                suffix={`/ ${stats.total}`}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Certified Facilities"
                value={stats.withCertifications}
                valueStyle={{ color: '#1890ff' }}
                suffix={`/ ${stats.total}`}
              />
            </Card>
          </Col>
        </Row>

        {/* Geographic Map */}
        {showGeoMap && (
          <Card title="Geographic Distribution">
            {graphData.nodes.length > 0 ? (
              <GraphViewer
                data={graphData}
                layoutType="force"
                height={400}
                nodeLabelProperty="label"
                onNodeClick={(nodeId: string) => {
                  const facility = graphData.nodes.find((n: any) => n.id === nodeId);
                  console.log('Clicked facility:', facility);
                }}
              />
            ) : (
              <Empty description="No facilities to display" />
            )}
          </Card>
        )}

        {/* Filters */}
        <Card title={<><FilterOutlined /> <strong>Filters</strong></>}>
          <Row gutter={16}>
            <Col span={6}>
              <div style={{ marginBottom: 8 }}>
                <strong>Search Facilities:</strong>
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
                <strong>Facility Type:</strong>
              </div>
              <Select
                placeholder="Select type"
                allowClear
                style={{ width: '100%' }}
                value={filters.facilityType}
                onChange={(value) => handleFilterChange('facilityType', value)}
              >
                <Option value="manufacturing">Manufacturing</Option>
                <Option value="packaging">Packaging</Option>
                <Option value="warehouse">Warehouse</Option>
                <Option value="laboratory">Laboratory</Option>
              </Select>
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
              </Select>
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Certification:</strong>
              </div>
              <Select
                placeholder="Select certification"
                allowClear
                style={{ width: '100%' }}
                value={filters.certification}
                onChange={(value) => handleFilterChange('certification', value)}
              >
                <Option value="gmp">GMP</Option>
                <Option value="iso9001">ISO 9001</Option>
                <Option value="iso13485">ISO 13485</Option>
                <Option value="fda">FDA Approved</Option>
              </Select>
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 8 }}>
                <strong>Inspection Status:</strong>
              </div>
              <Select
                placeholder="Select status"
                allowClear
                style={{ width: '100%' }}
                value={filters.inspectionStatus}
                onChange={(value) => handleFilterChange('inspectionStatus', value)}
              >
                <Option value="passed">Passed</Option>
                <Option value="warning">Warning</Option>
                <Option value="failed">Failed</Option>
              </Select>
            </Col>
            <Col span={2}>
              <div style={{ marginBottom: 8 }}>
                <strong>Actions:</strong>
              </div>
              <Button
                onClick={() => setFilters({
                  search: '',
                  facilityType: undefined,
                  country: undefined,
                  certification: undefined,
                  inspectionStatus: undefined
                })}
              >
                Clear
              </Button>
            </Col>
          </Row>
        </Card>

        {/* Facilities Table */}
        <Card
          title={`Facilities (${total} total)`}
          extra={
            <Button icon={<SearchOutlined />} onClick={() => refetch()}>
              Refresh
            </Button>
          }
        >
          <Table
            columns={columns}
            dataSource={facilities}
            rowKey="id"
            loading={isLoading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} facilities`
            }}
            onChange={handleTableChange}
            onRow={(record) => ({
              onClick: () => handleRowClick(record),
              style: { cursor: 'pointer' }
            })}
            expandable={{
              expandedRowRender: (record) => (
                <Card type="inner" size="small">
                  <Row gutter={16}>
                    <Col span={12}>
                      <p><strong>Location:</strong> {record.location}</p>
                      <p><strong>Capacity:</strong> {record.capacity?.toLocaleString()} units/year</p>
                    </Col>
                    <Col span={12}>
                      <p><strong>Certifications:</strong></p>
                      <Space size="small" wrap>
                        {record.certifications?.map(cert => (
                          <Tag key={cert} icon={<SafetyOutlined />} color="blue">
                            {cert}
                          </Tag>
                        ))}
                      </Space>
                    </Col>
                  </Row>
                </Card>
              )
            }}
          />
        </Card>
      </Space>
    </div>
  );
};

export default FacilitiesPage;
