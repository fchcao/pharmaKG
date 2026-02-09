/**
 * SubmissionDetailPage.tsx - Regulatory Submission Detail View
 * Displays comprehensive information about a regulatory submission including timeline, approvals, and compliance
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
  Timeline,
  Tabs,
  Table,
  Badge,
  Statistic,
  Alert,
  Tooltip,
  Spin
} from 'antd';
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  DownloadOutlined,
  LinkOutlined,
  CalendarOutlined,
  BankOutlined,
  MedicineBoxOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useSubmission, useSubmissionTimeline, useSubmissionApprovals, useSubmissionDocuments } from './hooks';
import { Submission, SubmissionTimeline, Approval, Document, ApiError } from './types';
import { LoadingSpinner, EmptyState } from '@/shared/components';
import { TimelineChart } from '@/shared/graphs';

const SubmissionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Queries
  const {
    data: submission,
    isLoading: submissionLoading,
    error: submissionError
  } = useSubmission(id!, {});

  const {
    data: timelineEvents,
    isLoading: timelineLoading
  } = useSubmissionTimeline(id!, {});

  const {
    data: approvals,
    isLoading: approvalsLoading
  } = useSubmissionApprovals(id!, {});

  const {
    data: documents,
    isLoading: documentsLoading
  } = useSubmissionDocuments(id!, {});

  const timeline = timelineEvents || [];
  const relatedApprovals = approvals || [];
  const relatedDocuments = documents || [];

  // Handle navigation
  const handleBack = () => {
    navigate('/regulatory/submissions');
  };

  // Navigate to approval detail
  const handleViewApproval = (approvalId: string) => {
    navigate(`/regulatory/approvals/${approvalId}`);
  };

  // Navigate to document detail
  const handleViewDocument = (documentId: string) => {
    navigate(`/regulatory/documents/${documentId}`);
  };

  // Get status configuration
  const getStatusConfig = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'approved':
        return { color: 'success', icon: <CheckCircleOutlined />, text: 'Approved' };
      case 'pending':
      case 'under review':
        return { color: 'processing', icon: <ClockCircleOutlined />, text: 'Under Review' };
      case 'rejected':
        return { color: 'error', icon: <WarningOutlined />, text: 'Rejected' };
      default:
        return { color: 'default', icon: <FileTextOutlined />, text: status || 'Unknown' };
    }
  };

  // Get compliance status
  const getComplianceStatus = (submission?: Submission) => {
    const compliance = submission?.complianceStatus;
    if (!compliance) return null;

    const colorMap: Record<string, string> = {
      compliant: 'success',
      warning: 'warning',
      'non-compliant': 'error',
      pending: 'default',
    };

    return (
      <Alert
        message={`Compliance Status: ${compliance.status}`}
        description={
          compliance.findingsCount
            ? `${compliance.findingsCount} findings requiring attention`
            : 'No compliance issues detected'
        }
        type={colorMap[compliance.status] as any}
        showIcon
        style={{ marginBottom: 16 }}
      />
    );
  };

  // Timeline table columns
  const timelineColumns: ColumnsType<SubmissionTimeline> = [
    {
      title: 'Date',
      dataIndex: 'eventDate',
      key: 'eventDate',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: 'Event',
      dataIndex: 'eventType',
      key: 'eventType',
      width: 200,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => status ? <Tag color="blue">{status}</Tag> : '-',
    },
    {
      title: 'Decision',
      dataIndex: 'decision',
      key: 'decision',
      width: 150,
      render: (decision: string) => decision ? <Tag color={decision === 'approved' ? 'success' : 'error'}>{decision}</Tag> : '-',
    },
  ];

  // Approvals table columns
  const approvalColumns: ColumnsType<Approval> = [
    {
      title: 'Approval Number',
      dataIndex: 'approvalNumber',
      key: 'approvalNumber',
      render: (text: string, record: Approval) => (
        <Button
          type="link"
          onClick={() => handleViewApproval(record.id)}
          style={{ padding: 0 }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'approvalType',
      key: 'approvalType',
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: 'Approval Date',
      dataIndex: 'approvalDate',
      key: 'approvalDate',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: 'Expiry Date',
      dataIndex: 'expiryDate',
      key: 'expiryDate',
      render: (date?: string) => date ? dayjs(date).format('YYYY-MM-DD') : 'N/A',
    },
  ];

  // Documents table columns
  const documentColumns: ColumnsType<Document> = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Document) => (
        <Button
          type="link"
          onClick={() => handleViewDocument(record.id)}
          style={{ padding: 0 }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'documentType',
      key: 'documentType',
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: 'Date',
      dataIndex: 'documentDate',
      key: 'documentDate',
      render: (date?: string) => date ? dayjs(date).format('YYYY-MM-DD') : 'N/A',
    },
    {
      title: 'Confidentiality',
      dataIndex: 'confidentiality',
      key: 'confidentiality',
      render: (level?: string) => level ? <Tag color={level === 'public' ? 'green' : 'orange'}>{level}</Tag> : '-',
    },
    {
      title: 'Format',
      dataIndex: 'format',
      key: 'format',
      width: 100,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record: Document) => (
        <Space size="small">
          {record.url && (
            <Tooltip title="Download">
              <Button
                type="text"
                icon={<DownloadOutlined />}
                onClick={() => window.open(record.url, '_blank')}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  if (submissionError) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <EmptyState
            title="Error Loading Submission"
            description={(submissionError as ApiError).message || 'An error occurred while fetching the submission'}
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
      <LoadingSpinner loading={submissionLoading}>
        {submission && (
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
                        Back to Submissions
                      </Button>
                    </Space>
                    <h2 style={{ margin: '8px 0' }}>
                      Submission {submission.submissionNumber || 'N/A'}
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

            {/* Status Overview */}
            <Row gutter={16}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Status"
                    value={getStatusConfig(submission.status).text}
                    prefix={getStatusConfig(submission.status).icon}
                    valueStyle={{ color: getStatusConfig(submission.status).color === 'success' ? '#52c41a' : undefined }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Submission Type"
                    value={submission.submissionType || 'N/A'}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Days Since Submission"
                    value={submission.submissionDate ? dayjs().diff(dayjs(submission.submissionDate), 'days') : 'N/A'}
                    suffix="days"
                    prefix={<CalendarOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Related Approvals"
                    value={relatedApprovals.length}
                    prefix={<CheckCircleOutlined />}
                  />
                </Card>
              </Col>
            </Row>

            {/* Compliance Alert */}
            {getComplianceStatus(submission)}

            {/* Submission Information */}
            <Card title={<><FileTextOutlined /> Submission Information</>}>
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
                    status={getStatusConfig(submission.status).color as any}
                    text={getStatusConfig(submission.status).text}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="Submission Date">
                  {submission.submissionDate ? dayjs(submission.submissionDate).format('YYYY-MM-DD') : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Review Date">
                  {submission.reviewDate ? dayjs(submission.reviewDate).format('YYYY-MM-DD') : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Approval Date">
                  {submission.approvalDate ? dayjs(submission.approvalDate).format('YYYY-MM-DD') : 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Drug">
                  <Space>
                    <MedicineBoxOutlined />
                    {submission.drugName || 'N/A'}
                  </Space>
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Related Drugs */}
            {submission.relatedDrugs && submission.relatedDrugs.length > 0 && (
              <Card title={<><MedicineBoxOutlined /> Related Drugs</>}>
                <Row gutter={16}>
                  {submission.relatedDrugs.map((drug) => (
                    <Col span={8} key={drug.id}>
                      <Card size="small">
                        <Space direction="vertical" size={0}>
                          <strong>{drug.name}</strong>
                          <small>{drug.type}</small>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>
            )}

            {/* Tabs for detailed information */}
            <Card>
              <Tabs
                defaultActiveKey="timeline"
                items={[
                  {
                    key: 'timeline',
                    label: (
                      <span>
                        <CalendarOutlined /> Timeline
                      </span>
                    ),
                    children: (
                      <Spin spinning={timelineLoading}>
                        {timeline.length > 0 ? (
                          <Timeline
                            mode="left"
                            items={timeline.map((event) => ({
                              color: event.status === 'completed' ? 'green' : 'blue',
                              dot: event.decision === 'approved' ? <CheckCircleOutlined /> : <ClockCircleOutlined />,
                              children: (
                                                                <Card size="small" style={{ marginBottom: 16 }}>
                                  <Row justify="space-between">
                                                                    <Col>
                                                                      <Space direction="vertical" size={0}>
                                                                        <strong>{event.eventType}</strong>
                                                                        <small>{dayjs(event.eventDate).format('YYYY-MM-DD')}</small>
                                                                      </Space>
                                                                    </Col>
                                                                    <Col>
                                                                      {event.status && <Tag>{event.status}</Tag>}
                                                                      {event.decision && (
                                                                        <Tag color={event.decision === 'approved' ? 'success' : 'error'}>
                                                                          {event.decision}
                                                                        </Tag>
                                                                      )}
                                                                    </Col>
                                                                  </Row>
                                                                  <p style={{ marginTop: 8, marginBottom: 0 }}>
                                                                    {event.description}
                                                                  </p>
                                                                  {event.nextSteps && event.nextSteps.length > 0 && (
                                                                    <div style={{ marginTop: 8 }}>
                                                                      <strong>Next Steps:</strong>
                                                                      <ul style={{ marginBottom: 0 }}>
                                                                        {event.nextSteps.map((step, idx) => (
                                                                          <li key={idx}>{step}</li>
                                                                        ))}
                                                                      </ul>
                                                                    </div>
                                                                  )}
                                                                </Card>
                              ),
                            }))}
                          />
                        ) : (
                          <EmptyState
                            title="No Timeline Events"
                            description="No timeline events are available for this submission"
                          />
                        )}
                      </Spin>
                    ),
                  },
                  {
                    key: 'approvals',
                    label: (
                      <span>
                        <CheckCircleOutlined /> Approvals ({relatedApprovals.length})
                      </span>
                    ),
                    children: (
                      <Spin spinning={approvalsLoading}>
                        {relatedApprovals.length > 0 ? (
                          <Table
                            columns={approvalColumns}
                            dataSource={relatedApprovals}
                            rowKey="id"
                            pagination={false}
                          />
                        ) : (
                          <EmptyState
                            title="No Approvals"
                            description="This submission has not yet received any approvals"
                          />
                        )}
                      </Spin>
                    ),
                  },
                  {
                    key: 'documents',
                    label: (
                      <span>
                        <FileTextOutlined /> Documents ({relatedDocuments.length})
                      </span>
                    ),
                    children: (
                      <Spin spinning={documentsLoading}>
                        {relatedDocuments.length > 0 ? (
                          <Table
                            columns={documentColumns}
                            dataSource={relatedDocuments}
                            rowKey="id"
                            pagination={false}
                          />
                        ) : (
                          <EmptyState
                            title="No Documents"
                            description="No documents are associated with this submission"
                          />
                        )}
                      </Spin>
                    ),
                  },
                  {
                    key: 'visual',
                    label: (
                      <span>
                        <LinkOutlined /> Visual Timeline
                      </span>
                    ),
                    children: (
                      <TimelineChart
                        height={300}
                      />
                    ),
                  },
                ]}
              />
            </Card>
          </Space>
        )}
      </LoadingSpinner>
    </div>
  );
};

export default SubmissionDetailPage;
