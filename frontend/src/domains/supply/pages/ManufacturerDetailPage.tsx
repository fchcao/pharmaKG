/**
 * ManufacturerDetailPage.tsx
 * Supply Chain - Manufacturer Detail Page
 *
 * Features:
 * - Company information and certifications
 * - Quality scores and compliance status
 * - Related facilities
 * - Supply chain network visualization
 * - Products manufactured
 * - Inspection history
 */

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Descriptions,
  Tag,
  Space,
  Tabs,
  Table,
  Badge,
  Statistic,
  Button,
  Spin,
  Alert,
  Timeline,
  Progress
} from 'antd';
import {
  SafetyOutlined,
  EnvironmentOutlined,
  GlobalOutlined,
  StarOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ShopOutlined,
  FileTextOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import type { ColumnsType } from 'antd/es/table';
import { GraphViewer } from '@/shared/graphs';
import { TimelineChart } from '@/shared/graphs';
import { supplyChainApi } from '../api';
import type { Manufacturer, Facility, Product } from '../types';

const { TabPane } = Tabs;

/**
 * Manufacturer Detail Page Component
 */
export const ManufacturerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch manufacturer details
  const {
    data: manufacturerData,
    isLoading: isLoadingManufacturer,
    isError: isManufacturerError
  } = useQuery({
    queryKey: ['manufacturer', id],
    queryFn: () => supplyChainApi.getManufacturerById(id!),
    enabled: !!id
  });

  // Fetch manufacturer products
  const { data: productsData, isLoading: isLoadingProducts } = useQuery({
    queryKey: ['manufacturer-products', id],
    queryFn: () => supplyChainApi.getManufacturerProducts(id!),
    enabled: !!id && activeTab === 'products'
  });

  // Fetch manufacturer facilities
  const { data: facilitiesData, isLoading: isLoadingFacilities } = useQuery({
    queryKey: ['manufacturer-facilities', id],
    queryFn: () => supplyChainApi.getManufacturerFacilities(id!),
    enabled: !!id && activeTab === 'facilities'
  });

  // Fetch inspection history
  const { data: inspectionsData, isLoading: isLoadingInspections } = useQuery({
    queryKey: ['manufacturer-inspections', id],
    queryFn: () => supplyChainApi.getManufacturerInspections(id!),
    enabled: !!id && activeTab === 'compliance'
  });

  // Fetch compliance actions
  const { data: complianceData, isLoading: isLoadingCompliance } = useQuery({
    queryKey: ['manufacturer-compliance', id],
    queryFn: () => supplyChainApi.getManufacturerCompliance(id!),
    enabled: !!id && activeTab === 'compliance'
  });

  // Fetch supply chain network
  const { data: networkData } = useQuery({
    queryKey: ['manufacturer-network', id],
    queryFn: () => supplyChainApi.getManufacturerNetwork(id!),
    enabled: !!id && activeTab === 'network'
  });

  const manufacturer = manufacturerData?.data;
  const products = productsData?.data || [];
  const facilities = facilitiesData?.data || [];
  const inspections = inspectionsData?.data || [];
  const complianceActions = complianceData?.data || [];

  if (isLoadingManufacturer) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (isManufacturerError || !manufacturer) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Error"
          description="Manufacturer not found or failed to load"
          type="error"
          showIcon
        />
      </div>
    );
  }

  // Calculate compliance score
  const complianceScore = manufacturer.qualityScore || 0;
  const complianceLevel =
    complianceScore >= 90 ? 'Excellent' : complianceScore >= 75 ? 'Good' : complianceScore >= 60 ? 'Fair' : 'Poor';

  // Products table columns
  const productColumns: ColumnsType<Product> = [
    {
      title: 'Product Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <a>{text}</a>
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => <Tag>{category}</Tag>
    },
    {
      title: 'Dosage Form',
      dataIndex: 'dosageForm',
      key: 'dosageForm'
    },
    {
      title: 'Strength',
      dataIndex: 'strength',
      key: 'strength'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'approved' ? 'green' : status === 'pending' ? 'orange' : 'red';
        return <Badge status={color as any} text={status?.toUpperCase()} />;
      }
    }
  ];

  // Facilities table columns
  const facilityColumns: ColumnsType<Facility> = [
    {
      title: 'Facility Name',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: 'Type',
      dataIndex: 'facilityType',
      key: 'facilityType',
      render: (type: string) => <Tag color="blue">{type}</Tag>
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
      render: (location: string) => (
        <Space>
          <EnvironmentOutlined />
          {location}
        </Space>
      )
    },
    {
      title: 'Capacity',
      dataIndex: 'capacity',
      key: 'capacity',
      render: (capacity: number) => `${capacity?.toLocaleString()} units/year`
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'operational' ? 'green' : status === 'maintenance' ? 'orange' : 'red';
        return <Badge status={color as any} text={status?.toUpperCase()} />;
      }
    }
  ];

  // Inspections table columns
  const inspectionColumns: ColumnsType<any> = [
    {
      title: 'Date',
      dataIndex: 'inspection_date',
      key: 'inspection_date',
      sorter: true
    },
    {
      title: 'Facility',
      dataIndex: 'facility_name',
      key: 'facility_name'
    },
    {
      title: 'Type',
      dataIndex: 'inspection_type',
      key: 'inspection_type',
      render: (type: string) => <Tag>{type}</Tag>
    },
    {
      title: 'Result',
      dataIndex: 'result',
      key: 'result',
      render: (result: string) => {
        const color = result === 'Pass' ? 'green' : result === 'Fail' ? 'red' : 'orange';
        return <Tag color={color}>{result}</Tag>;
      }
    },
    {
      title: 'Agency',
      dataIndex: 'agency',
      key: 'agency'
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Header */}
        <Card>
          <Row gutter={16} align="middle">
            <Col span={18}>
              <Space size="large">
                <ShopOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
                <div>
                  <h1 style={{ margin: 0 }}>{manufacturer.name}</h1>
                  <p style={{ margin: 0, color: '#8c8c8c' }}>
                    {manufacturer.type?.toUpperCase()} • {manufacturer.location}
                  </p>
                </div>
              </Space>
            </Col>
            <Col span={6} style={{ textAlign: 'right' }}>
              <Space>
                <Tag icon={<CheckCircleOutlined />} color="green">
                  Active
                </Tag>
                <Button>Export Profile</Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Statistics */}
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Quality Score"
                value={complianceScore}
                suffix="/ 100"
                prefix={<StarOutlined />}
                valueStyle={{
                  color:
                    complianceScore >= 80 ? '#3f8600' : complianceScore >= 60 ? '#faad14' : '#f5222d'
                }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Products"
                value={products.length}
                prefix={<ShopOutlined />}
                suffix="items"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Facilities"
                value={facilities.length}
                prefix={<EnvironmentOutlined />}
                suffix="sites"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Compliance Level"
                value={complianceLevel}
                prefix={<SafetyOutlined />}
                valueStyle={{
                  color:
                    complianceLevel === 'Excellent'
                      ? '#3f8600'
                      : complianceLevel === 'Good'
                        ? '#52c41a'
                        : complianceLevel === 'Fair'
                          ? '#faad14'
                          : '#f5222d'
                }}
              />
            </Card>
          </Col>
        </Row>

        {/* Main Content Tabs */}
        <Card>
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane tab="Overview" key="overview">
              <Row gutter={16}>
                <Col span={12}>
                  <Card title="Company Information" type="inner">
                    <Descriptions column={1} bordered>
                      <Descriptions.Item label="Manufacturer ID">
                        {manufacturer.id}
                      </Descriptions.Item>
                      <Descriptions.Item label="Company Name">
                        {manufacturer.name}
                      </Descriptions.Item>
                      <Descriptions.Item label="Type">
                        <Tag color="blue">{manufacturer.type?.toUpperCase()}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="Location">
                        <Space>
                          <EnvironmentOutlined />
                          {manufacturer.location}
                        </Space>
                      </Descriptions.Item>
                      {manufacturer.website && (
                        <Descriptions.Item label="Website">
                          <a
                            href={manufacturer.website}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {manufacturer.website}
                          </a>
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card title="Compliance & Quality" type="inner">
                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                      <div>
                        <div style={{ marginBottom: 8 }}>
                          <strong>Overall Quality Score:</strong>
                        </div>
                        <Progress
                          percent={complianceScore}
                          status={
                            complianceScore >= 80 ? 'success' : complianceScore >= 60 ? 'normal' : 'exception'
                          }
                        />
                      </div>
                      <div>
                        <div style={{ marginBottom: 8 }}>
                          <strong>Certifications:</strong>
                        </div>
                        <Space size="small" wrap>
                          {manufacturer.certifications?.map(cert => (
                            <Tag key={cert} icon={<SafetyOutlined />} color="blue">
                              {cert}
                            </Tag>
                          )) || <span>No certifications recorded</span>}
                        </Space>
                      </div>
                      {manufacturer.facilities && manufacturer.facilities.length > 0 && (
                        <Alert
                          message={`${manufacturer.facilities.length} facilities worldwide`}
                          type="info"
                          showIcon
                        />
                      )}
                    </Space>
                  </Card>
                </Col>
              </Row>
            </TabPane>

            <TabPane tab="Products" key="products">
              <Card
                title={`Products Manufactured (${products.length})`}
                extra={<Button>Download List</Button>}
              >
                <Table
                  columns={productColumns}
                  dataSource={products}
                  rowKey="id"
                  loading={isLoadingProducts}
                  pagination={{ pageSize: 10 }}
                />
              </Card>
            </TabPane>

            <TabPane tab="Facilities" key="facilities">
              <Card
                title={`Manufacturing Facilities (${facilities.length})`}
                extra={<Button>View Map</Button>}
              >
                <Table
                  columns={facilityColumns}
                  dataSource={facilities}
                  rowKey="id"
                  loading={isLoadingFacilities}
                  pagination={{ pageSize: 10 }}
                  expandable={{
                    expandedRowRender: (record) => (
                      <Descriptions column={2} size="small">
                        <Descriptions.Item label="Capacity">
                          {record.capacity?.toLocaleString()} units/year
                        </Descriptions.Item>
                        <Descriptions.Item label="Certifications">
                          {record.certifications?.join(', ') || 'N/A'}
                        </Descriptions.Item>
                      </Descriptions>
                    )
                  }}
                />
              </Card>
            </TabPane>

            <TabPane tab="Compliance" key="compliance">
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Card title="Recent Inspections" type="inner">
                  <Table
                    columns={inspectionColumns}
                    dataSource={inspections}
                    rowKey="inspection_id"
                    loading={isLoadingInspections}
                    pagination={{ pageSize: 5 }}
                  />
                </Card>

                {complianceActions.length > 0 && (
                  <Card title="Compliance Actions" type="inner">
                    <Timeline
                      items={complianceActions.map((action: any) => ({
                        color: action.severity === 'high' ? 'red' : action.severity === 'medium' ? 'orange' : 'blue',
                        dot:
                          action.severity === 'high' ? (
                            <WarningOutlined style={{ fontSize: '16px' }} />
                          ) : (
                            <SafetyOutlined style={{ fontSize: '16px' }} />
                          ),
                        children: (
                          <div>
                            <p style={{ fontWeight: 'bold', margin: 0 }}>
                              {action.action_type}
                            </p>
                            <p style={{ margin: 0 }}>{action.reason}</p>
                            <p style={{ margin: 0, color: '#8c8c8c', fontSize: '12px' }}>
                              {action.action_date} • {action.agency}
                            </p>
                          </div>
                        )
                      }))}
                    />
                  </Card>
                )}
              </Space>
            </TabPane>

            <TabPane tab="Supply Network" key="network">
              <Card title="Supply Chain Network Visualization">
                {networkData ? (
                  <>
                    {networkData.data?.nodes && networkData.data.nodes.length > 0 ? (
                      <>
                        <Row gutter={16} style={{ marginBottom: 16 }}>
                          <Col span={8}>
                            <Statistic
                              title="Connected Entities"
                              value={networkData.data.nodes.length}
                              suffix="nodes"
                            />
                          </Col>
                          <Col span={8}>
                            <Statistic
                              title="Relationships"
                              value={networkData.data.edges?.length || 0}
                              suffix="links"
                            />
                          </Col>
                          <Col span={8}>
                            <Statistic
                              title="CRL Documents"
                              value={networkData.data.nodes.filter(n => n.type === 'CRL').length}
                              suffix="letters"
                            />
                          </Col>
                        </Row>
                        <GraphViewer
                          data={networkData.data}
                          layoutType="force"
                          height={500}
                          nodeLabelProperty="label"
                        />
                      </>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '60px 0' }}>
                        <FileTextOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                        <p style={{ color: '#8c8c8c', marginTop: 16 }}>
                          No network data available for this manufacturer.
                          The company may not have any associated CRL documents.
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <Spin size="large" />
                )}
              </Card>
            </TabPane>
          </Tabs>
        </Card>
      </Space>
    </div>
  );
};

export default ManufacturerDetailPage;
