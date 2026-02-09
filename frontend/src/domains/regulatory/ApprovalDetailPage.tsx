/**
 * ApprovalDetailPage.tsx - Regulatory Approval Detail View
 * Displays comprehensive information about a regulatory approval including related submission and requirements
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Descriptions,
  Tag,
  Button,
  Space,
  List,
  Alert,
  Badge,
  Statistic,
  Timeline,
  Tooltip
} from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  FileTextOutlined,
  BankOutlined,
  MedicineBoxOutlined,
  CalendarOutlined,
  DownloadOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useApproval, useApprovalSubmission } from './hooks';
import { Approval, Submission, ApiError } from './types';
import { LoadingSpinner, EmptyState } from '@/shared/components';

const ApprovalDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Queries
  const {
    data: approval,
    isLoading: approvalLoading,
    error: approvalError
  } = useApproval(id!, {});

  const {
    data: submission,
    isLoading: submissionLoading
  } = useApprovalSubmission(id!, {});

  // Handle navigation
  const handleBack = () => {
    navigate('/regulatory/approvals');
  };

  // Navigate to submission detail
  const handleViewSubmission = () => {
    if (submission) {
      navigate(`/regulatory/submissions/${submission.id}`);
    }
  };

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

  // Get requirement status
  const getRequirementStatus = (status: string) => {
    const config: Record<string, { icon: React.ReactNode; color: string }> = {
      pending: { icon: <ClockCircleOutlined />, color: 'default' },
      in_progress: { icon: <ExclamationCircleOutlined />, color: 'processing' },
      completed: { icon: <CheckCircleOutlined />, color: 'success' },
      overdue: { icon: <WarningOutlined />, color: 'error' },
    };
    return config[status] || config.pending;
  };

  // Check if approval is expiring soon
  const isExpiringSoon = (approval?: Approval) => {
    if (!approval?.expiryDate) return false;
    const daysUntilExpiry = dayjs(approval.expiryDate).diff(dayjs(), 'days');
    return daysUntilExpiry > 0 && daysUntilExpiry < 180;
  };

  // Check if approval is expired
  const isExpired = (approval?: Approval) => {
    if (!approval?.expiryDate) return false;
    return dayjs(approval.expiryDate).isBefore(dayjs());
  };

  if (approvalError) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <EmptyState
            title="Error Loading Approval"
            description={(approvalError as ApiError).message || 'An error occurred while fetching the approval'}
            action={{
              label: 'Go Back',
              onClick: handleBack,
            }}
          />
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <LoadingSpinner loading={approvalLoading}>
        {approval && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* Header */}
            <Card>
              <Row justify="space-between" align="middle">
                <Col>
                  <Space direction="vertical" size={0}>
                    <Space>
                      <Button
                        icon={<ArrowLeftOutlined />}
                        onClick={handleBack}
                      >
                        Back to Approvals
                      </Button>
                    </Space>
                    <h2 style={{ margin: '8px 0' }}>
                      Approval {approval.approvalNumber || 'N/A'}
                    </h2>
                  </Space>
                </Col>
                <Col>
                  <Space>
                    <Button icon={<DownloadOutlined />}>
                      Export
                    </Button>
                  </Space>
                </Col>
              </Row>
            </Card>

            {/* Expiration Warning */}
            {(isExpired(approval) || isExpiringSoon(approval)) && (
              <Alert
                message={isExpired(approval) ? 'Approval Expired' : 'Approval Expiring Soon'}
                description={
                  isExpired(approval)
                    ? `This approval expired on ${dayjs(approval.expiryDate).format('YYYY-MM-DD')}`
                    : `This approval will expire on ${dayjs(approval.expiryDate).format('YYYY-MM-DD')}`
                }
                type={isExpired(approval) ? 'error' : 'warning'}
                showIcon
              />
            )}

            {/* Status Overview */}
            <Row gutter={16}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Approval Type"
                    value={approval.approvalType || 'N/A'}
                    valueStyle={{ color: getApprovalTypeColor(approval.approvalType) === 'success' ? '#52c41a' : undefined }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Approval Date"
                    value={approval.approvalDate ? dayjs(approval.approvalDate).format('YYYY-MM-DD') : 'N/A'}
                    prefix={<CalendarOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Days Since Approval"
                    value={approval.approvalDate ? dayjs().diff(dayjs(approval.approvalDate), 'days') : 'N/A'}
                    suffix="days"
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Post-Approval Requirements"
                    value={approval.postApprovalRequirements?.length || 0}
                    prefix={<ExclamationCircleOutlined />}
                  />
                </Card>
              </Col>
            </Row>

            {/* Approval Information */}
            <Card title={<><CheckCircleOutlined /> Approval Information</>}>
              <Descriptions column={2} bordered>
                <Descriptions.Item label="Approval Number">
                  {approval.approvalNumber || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Approval Type">
                  <Tag color={getApprovalTypeColor(approval.approvalType)}>
                    {approval.approvalType || 'N/A'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Drug">
                  <Space>
                    <MedicineBoxOutlined />
                    {approval.drugName || 'N/A'}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Therapeutic Area">
                  {approval.therapeuticArea ? <Tag color="cyan">{approval.therapeuticArea}</Tag> : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Agency">
                  <Space>
                    <BankOutlined />
                    {approval.agencyName || 'N/A'}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Approval Date">
                  {approval.approvalDate ? dayjs(approval.approvalDate).format('YYYY-MM-DD') : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Expiry Date" span={2}>
                  {approval.expiryDate ? (
                    <Space>
                      <CalendarOutlined />
                      {dayjs(approval.expiryDate).format('YYYY-MM-DD')}
                      {isExpired(approval) && <Tag color="error">Expired</Tag>}
                      {isExpiringSoon(approval) && !isExpired(approval) && <Tag color="warning">Expiring Soon</Tag>}
                    </Space>
                  ) : 'N/A'}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Conditions */}
            {approval.conditions && approval.conditions.length > 0 && (
              <Card title={<><ExclamationCircleOutlined /> Approval Conditions</>}>
                <List
                  dataSource={approval.conditions}
                  renderItem={(condition, index) => (
                    <List.Item>
                      <Space>
                        <Tag color="orange">{index + 1}</Tag>
                        {condition}
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* Post-Approval Requirements */}
            {approval.postApprovalRequirements && approval.postApprovalRequirements.length > 0 && (
              <Card
                title={
                  <Space>
                    <ExclamationCircleOutlined /> Post-Approval Requirements
                    <Badge count={approval.postApprovalRequirements.length} />
                  </Space>
                }
              >
                <List
                  dataSource={approval.postApprovalRequirements}
                  renderItem={(requirement) => {
                    const status = getRequirementStatus(requirement.status);
                    return (
                      <List.Item
                        actions={[
                          requirement.dueDate && (
                            <Space>
                              <CalendarOutlined />
                              {dayjs(requirement.dueDate).format('YYYY-MM-DD')}
                            </Space>
                          ),
                        ]}
                      >
                        <List.Item.Meta
                          avatar={
                            <Badge status={status.color as any} icon={status.icon} />
                          }
                          title={requirement.requirement}
                          description={
                            <Space>
                              <Tag color={status.color}>{requirement.status}</Tag>
                              {requirement.dueDate && (
                                <span>
                                  Due: {dayjs(requirement.dueDate).format('YYYY-MM-DD')}
                                </span>
                              )}
                            </Space>
                          }
                        />
                      </List.Item>
                    );
                  }}
                />
              </Card>
            )}

            {/* Related Submission */}
            {submission && (
              <Card
                title={<><FileTextOutlined /> Related Submission</>}
                extra={
                  <Button onClick={handleViewSubmission}>
                    View Full Submission
                  </Button>
                }
              >
                <LoadingSpinner loading={submissionLoading}>
                  <Descriptions column={2} bordered>
                    <Descriptions.Item label="Submission Number">
                      {submission.submissionNumber || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Submission Type">
                      <Tag color="blue">{submission.submissionType || 'N/A'}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Agency">
                      <Space>
                        <BankOutlined />
                        {submission.agency?.name || 'N/A'}
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label="Status">
                      <Badge
                        status={submission.status === 'approved' ? 'success' : 'processing'}
                        text={submission.status || 'N/A'}
                      />
                    </Descriptions.Item>
                    <Descriptions.Item label="Submission Date">
                      {submission.submissionDate ? dayjs(submission.submissionDate).format('YYYY-MM-DD') : 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Review Date">
                      {submission.reviewDate ? dayjs(submission.reviewDate).format('YYYY-MM-DD') : 'N/A'}
                    </Descriptions.Item>
                  </Descriptions>
                </LoadingSpinner>
              </Card>
            )}

            {/* Timeline Visualization */}
            <Card title={<><CalendarOutlined /> Approval Timeline</>}>
              <Timeline
                mode="left"
                items={[
                  {
                    color: 'green',
                    children: (
                      <div>
                        <strong>Submission</strong>
                        <br />
                        {submission?.submissionDate && dayjs(submission.submissionDate).format('YYYY-MM-DD')}
                      </div>
                    ),
                  },
                  {
                    color: 'blue',
                    children: (
                      <div>
                        <strong>Review</strong>
                        <br />
                        {submission?.reviewDate && dayjs(submission.reviewDate).format('YYYY-MM-DD')}
                      </div>
                    ),
                  },
                  {
                    color: 'green',
                    children: (
                      <div>
                        <strong>Approval</strong>
                        <br />
                        {approval.approvalDate && dayjs(approval.approvalDate).format('YYYY-MM-DD')}
                      </div>
                    ),
                  },
                  ...(approval.expiryDate ? [{
                    color: 'orange',
                    children: (
                      <div>
                        <strong>Expiry</strong>
                        <br />
                        {dayjs(approval.expiryDate).format('YYYY-MM-DD')}
                      </div>
                    ),
                  }] : []),
                ]}
              />
            </Card>
          </Space>
        )}
      </LoadingSpinner>
    </div>
  );
};

export default ApprovalDetailPage;
