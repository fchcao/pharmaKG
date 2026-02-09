/**
 * RegulatoryDashboardPage.tsx - Regulatory Domain Dashboard
 * Provides an overview of regulatory domain with key statistics and quick navigation
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Space,
  List,
  Tag,
  Progress,
  Typography
} from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  BankOutlined,
  TrophyOutlined,
  WarningOutlined,
  ArrowRightOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useRegulatoryStatistics, useSubmissions, useApprovals } from './hooks';
import { RegulatoryStatistics } from './types';
import { LoadingSpinner } from '@/shared/components';

const { Title, Text } = Typography;

const RegulatoryDashboardPage: React.FC = () => {
  const navigate = useNavigate();

  // Queries
  const {
    data: statistics,
    isLoading: statsLoading
  } = useRegulatoryStatistics();

  const {
    data: recentSubmissions
  } = useSubmissions({ page: 1, pageSize: 5 }, { enabled: true });

  const {
    data: recentApprovals
  } = useApprovals({ page: 1, pageSize: 5 }, { enabled: true });

  const stats = statistics as RegulatoryStatistics | undefined;

  const recentSubs = recentSubmissions?.items || [];
  const recentApps = recentApprovals?.items || [];

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <Card>
          <Title level={2} style={{ margin: 0 }}>Regulatory Domain</Title>
          <Text type="secondary">
            Comprehensive view of regulatory submissions, approvals, and compliance
          </Text>
        </Card>

        {/* Key Statistics */}
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Submissions"
                value={stats?.totalSubmissions || 0}
                prefix={<FileTextOutlined />}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Approvals"
                value={stats?.totalApprovals || 0}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#52c41a' }}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Pending Review"
                value={stats?.pendingSubmissions || 0}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text type="secondary">Approval Rate</Text>
                <Progress
                  type="circle"
                  percent={Math.round(stats?.complianceRate || 0)}
                  size={80}
                />
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Agency Breakdown */}
        <Card title={<><BankOutlined /> Submissions by Agency</>}>
          <Row gutter={16}>
            {stats?.submissionsByAgency && Object.entries(stats.submissionsByAgency).map(([agency, count]) => (
              <Col span={8} key={agency}>
                <Card size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>{agency}</Text>
                    <Statistic value={count} />
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>

        {/* Quick Actions */}
        <Card title="Quick Actions">
          <Row gutter={16}>
            <Col span={6}>
              <Button
                type="primary"
                block
                size="large"
                icon={<FileTextOutlined />}
                onClick={() => navigate('/regulatory/submissions')}
              >
                Browse Submissions
              </Button>
            </Col>
            <Col span={6}>
              <Button
                type="default"
                block
                size="large"
                icon={<TrophyOutlined />}
                onClick={() => navigate('/regulatory/approvals')}
              >
                View Approvals
              </Button>
            </Col>
            <Col span={6}>
              <Button
                type="default"
                block
                size="large"
                icon={<CalendarOutlined />}
                onClick={() => navigate('/regulatory/documents')}
              >
                Documents
              </Button>
            </Col>
            <Col span={6}>
              <Button
                type="default"
                block
                size="large"
                icon={<WarningOutlined />}
                onClick={() => navigate('/regulatory/compliance')}
              >
                Compliance
              </Button>
            </Col>
          </Row>
        </Card>

        {/* Recent Activity */}
        <Row gutter={16}>
          <Col span={12}>
            <Card
              title={<><FileTextOutlined /> Recent Submissions</>}
              extra={
                <Button
                  type="link"
                  icon={<ArrowRightOutlined />}
                  onClick={() => navigate('/regulatory/submissions')}
                >
                  View All
                </Button>
              }
            >
              <List
                dataSource={recentSubs}
                renderItem={(item: any) => (
                  <List.Item
                    onClick={() => navigate(`/regulatory/submissions/${item.id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <List.Item.Meta
                      title={item.submissionNumber || 'N/A'}
                      description={
                        <Space>
                          <Tag>{item.submissionType}</Tag>
                          <Text type="secondary">{item.drugName}</Text>
                        </Space>
                      }
                    />
                    <Tag color={item.status === 'approved' ? 'success' : 'processing'}>
                      {item.status}
                    </Tag>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card
              title={<><TrophyOutlined /> Recent Approvals</>}
              extra={
                <Button
                  type="link"
                  icon={<ArrowRightOutlined />}
                  onClick={() => navigate('/regulatory/approvals')}
                >
                  View All
                </Button>
              }
            >
              <List
                dataSource={recentApps}
                renderItem={(item: any) => (
                  <List.Item
                    onClick={() => navigate(`/regulatory/approvals/${item.id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <List.Item.Meta
                      title={item.approvalNumber || 'N/A'}
                      description={
                        <Space>
                          <Tag color="blue">{item.approvalType}</Tag>
                          <Text type="secondary">{item.drugName}</Text>
                        </Space>
                      }
                    />
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>

        {/* Submission Types */}
        <Card title={<><FileTextOutlined /> Submissions by Type</>}>
          <Row gutter={16}>
            {stats?.submissionsByType && Object.entries(stats.submissionsByType).map(([type, count]) => (
              <Col span={6} key={type}>
                <Card size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Tag color="blue">{type}</Tag>
                    <Statistic value={count} />
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>

        {/* Yearly Trends */}
        <Card title={<><CalendarOutlined /> Approval Trends by Year</>}>
          <List
            dataSource={stats?.approvalsByYear ? Object.entries(stats.approvalsByYear).sort((a, b) => b[0].localeCompare(a[0])) : []}
            renderItem={(item: [string, number]) => {
              const [year, count] = item;
              return (
                <List.Item>
                  <List.Item.Meta
                    title={year}
                    description={`${count} approvals`}
                  />
                  <Progress
                    percent={Math.round((count / (stats?.totalApprovals || 1)) * 100)}
                    showInfo={false}
                    style={{ width: 200 }}
                  />
                  <Text strong>{count}</Text>
                </List.Item>
              );
            }}
          />
        </Card>
      </Space>
    </div>
  );
};

export default RegulatoryDashboardPage;
