import React, { useState } from 'react';
import {
  Container,
  Row,
  Col,
  Card,
  Space,
  Typography,
  Tag,
  Button,
  Descriptions,
  Timeline,
  Table,
  Alert,
  Tabs,
  Divider,
  Statistic,
  Progress,
  Badge,
} from 'antd';
import {
  ArrowLeftOutlined,
  EnvironmentOutlined,
  TeamOutlined,
  CalendarOutlined,
  MedicineBoxOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  ShareAltOutlined,
  StarOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useTrial, useTrialLocations, useTrialInterventions, useTrialOutcomes } from './hooks';
import { ClinicalTrial, Location, Intervention, Outcome } from './types';
import { mockTrialDetail, mockLocations, mockInterventions, mockOutcomes } from './mockData';
import { TimelineChart } from '@/shared/graphs/TimelineChart';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const TrialDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [useMockData, setUseMockData] = useState(true);

  // Fetch trial data
  const { data: trial, isLoading, error } = useTrial(id!, { enabled: !useMockData });
  const { data: locations } = useTrialLocations(id!, { enabled: !useMockData });
  const { data: interventions } = useTrialInterventions(id!, { enabled: !useMockData });
  const { data: outcomes } = useTrialOutcomes(id!, { enabled: !useMockData });

  // Use mock data if enabled or API returns empty
  const trialData: ClinicalTrial = useMockData || !trial ? mockTrialDetail : trial;
  const locationsData: Location[] = useMockData || !locations?.length
    ? mockLocations.filter(l => l.trialId === id)
    : locations;
  const interventionsData: Intervention[] = useMockData || !interventions?.length
    ? mockInterventions.filter(i => i.trialId === id)
    : interventions;
  const outcomesData: Outcome[] = useMockData || !outcomes?.length
    ? mockOutcomes.filter(o => o.trialId === id)
    : outcomes;

  // Calculate progress
  const calculateProgress = () => {
    if (!trialData.startDate) return 0;
    const startDate = new Date(trialData.startDate);
    const completionDate = trialData.completionDate ? new Date(trialData.completionDate) : new Date();
    const now = new Date();
    const totalDuration = completionDate.getTime() - startDate.getTime();
    const elapsed = now.getTime() - startDate.getTime();
    return Math.min(100, Math.max(0, (elapsed / totalDuration) * 100));
  };

  const progress = calculateProgress();

  // Timeline events
  const timelineEvents = [
    {
      date: trialData.startDate,
      event: 'Study Start',
      description: 'Trial begins recruitment',
      category: 'start' as const,
    },
    ...(trialData.completionDate ? [{
      date: trialData.completionDate,
      event: 'Expected Completion',
      description: 'Anticipated trial completion',
      category: 'completion' as const,
    }] : []),
  ];

  // Locations columns
  const locationColumns = [
    {
      title: 'Facility',
      dataIndex: 'facility',
      key: 'facility',
      render: (text: string) => <Space><EnvironmentOutlined /> {text}</Space>,
    },
    {
      title: 'Location',
      key: 'location',
      render: (_: any, record: Location) => `${record.city || ''}${record.city && record.state ? ', ' : ''}${record.state || ''} ${record.country || ''}`,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'Recruiting' ? 'green' : status === 'Active, not recruiting' ? 'blue' : 'default';
        return <Badge status={color as any} text={status} />;
      },
    },
  ];

  return (
    <Container style={{ padding: '24px', maxWidth: '1200px' }}>
      {/* Header */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Space style={{ width: '100%' }} direction="vertical" size="middle">
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/clinical/trials')}
              >
                Back to Trials
              </Button>
              <Space>
                {useMockData && <Tag color="warning">Mock Data</Tag>}
                <Button icon={<StarOutlined />}>Save</Button>
                <Button icon={<ShareAltOutlined />}>Share</Button>
                <Button icon={<LinkOutlined />}>External Link</Button>
              </Space>
            </Space>

            <Space direction="vertical" size="small">
              <Space>
                <Title level={2} style={{ margin: 0 }}>
                  {trialData.title}
                </Title>
              </Space>
              <Space wrap>
                <Tag color="blue">{trialData.phase || 'N/A'}</Tag>
                <Tag color={
                  trialData.status === 'Recruiting' ? 'green' :
                  trialData.status === 'Active, not recruiting' ? 'blue' :
                  trialData.status === 'Completed' ? 'default' : 'orange'
                }>
                  {trialData.status}
                </Tag>
                <Tag>{trialData.studyType}</Tag>
                {trialData.nctId && (
                  <Text code copyable={{ text: trialData.nctId }}>
                    {trialData.nctId}
                  </Text>
                )}
              </Space>
            </Space>
          </Space>
        </Col>
      </Row>

      {/* Error Alert */}
      {error && !useMockData && (
        <Alert
          message="Error loading trial details"
          description={error.message}
          type="error"
          closable
          action={
            <Button size="small" onClick={() => setUseMockData(true)}>
              Use Mock Data
            </Button>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic
              title="Enrollment"
              value={trialData.enrollment || 0}
              prefix={<TeamOutlined />}
              suffix="participants"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Locations"
              value={locationsData.length}
              prefix={<EnvironmentOutlined />}
              suffix="sites"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Interventions"
              value={interventionsData.length}
              prefix={<MedicineBoxOutlined />}
              suffix="arms"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="Outcomes"
              value={outcomesData.length}
              prefix={<FileTextOutlined />}
              suffix="measures"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Trial Progress">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Progress
                percent={progress.toFixed(1)}
                status={progress >= 100 ? 'success' : 'active'}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Text type="secondary">Start: {trialData.startDate ? new Date(trialData.startDate).toLocaleDateString() : '-'}</Text>
                <Text type="secondary">End: {trialData.completionDate ? new Date(trialData.completionDate).toLocaleDateString() : '-'}</Text>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Main Content Tabs */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="Overview" key="overview">
            <Row gutter={[24, 24]}>
              <Col span={16}>
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  {/* Study Description */}
                  <Card title="Study Design" size="small">
                    <Descriptions column={2} size="small" bordered>
                      <Descriptions.Item label="Allocation">
                        {trialData.allocation || 'N/A'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Masking">
                        {trialData.masking || 'N/A'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Purpose" span={2}>
                        {trialData.purpose || 'N/A'}
                      </Descriptions.Item>
                    </Descriptions>
                  </Card>

                  {/* Conditions */}
                  {trialData.conditions && trialData.conditions.length > 0 && (
                    <Card title="Conditions Studied" size="small">
                      <Space wrap>
                        {trialData.conditions.map((condition, i) => (
                          <Tag key={i} color="orange" style={{ fontSize: 13, padding: '4px 12px' }}>
                            {condition}
                          </Tag>
                        ))}
                      </Space>
                    </Card>
                  )}

                  {/* Timeline */}
                  <Card title="Trial Timeline" size="small">
                    <Timeline
                      items={timelineEvents.map(e => ({
                        color: e.category === 'start' ? 'green' : 'blue',
                        children: (
                          <Space direction="vertical" size="small">
                            <Text strong>{e.event}</Text>
                            <Text type="secondary">{new Date(e.date).toLocaleDateString()}</Text>
                            <Text type="secondary">{e.description}</Text>
                          </Space>
                        ),
                      }))}
                    />
                  </Card>
                </Space>
              </Col>

              <Col span={8}>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {/* Sponsor & Collaborators */}
                  <Card title="Sponsor & Collaborators" size="small">
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <div>
                        <Text strong>Sponsor:</Text>
                        <Paragraph>{trialData.sponsors?.join(', ') || 'N/A'}</Paragraph>
                      </div>
                      {trialData.collaborators && trialData.collaborators.length > 0 && (
                        <div>
                          <Text strong>Collaborators:</Text>
                          <Paragraph>{trialData.collaborators.join(', ')}</Paragraph>
                        </div>
                      )}
                    </Space>
                  </Card>

                  {/* Quick Actions */}
                  <Card title="Actions" size="small">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Button block icon={<ExperimentOutlined />}>
                        View Related Compounds
                      </Button>
                      <Button block icon={<EnvironmentOutlined />}>
                        View Locations Map
                      </Button>
                      <Button block icon={<FileTextOutlined />}>
                        View Protocol
                      </Button>
                      <Button block icon={<TeamOutlined />}>
                        View Participants
                      </Button>
                    </Space>
                  </Card>
                </Space>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab={`Interventions (${interventionsData.length})`} key="interventions">
            <Row gutter={[16, 16]}>
              {interventionsData.map((intervention) => (
                <Col key={intervention.id} span={12}>
                  <Card
                    title={
                      <Space>
                        <MedicineBoxOutlined />
                        {intervention.name}
                      </Space>
                    }
                    size="small"
                  >
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="Type">
                        <Tag color="blue">{intervention.interventionType}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="Arm Group">
                        {intervention.armGroupLabel || 'N/A'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Dosage">
                        {intervention.dosage || 'N/A'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Frequency">
                        {intervention.frequency || 'N/A'}
                      </Descriptions.Item>
                      {intervention.description && (
                        <Descriptions.Item label="Description">
                          {intervention.description}
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  </Card>
                </Col>
              ))}
            </Row>
          </TabPane>

          <TabPane tab={`Outcomes (${outcomesData.length})`} key="outcomes">
            <Card>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {outcomesData.map((outcome, index) => (
                  <Card
                    key={outcome.id}
                    type="inner"
                    title={
                      <Space>
                        <Tag color={
                          outcome.outcomeType === 'Primary' ? 'red' :
                          outcome.outcomeType === 'Secondary' ? 'blue' : 'default'
                        }>
                          {outcome.outcomeType}
                        </Tag>
                        {outcome.title}
                      </Space>
                    }
                  >
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="Description">
                        {outcome.description || 'N/A'}
                      </Descriptions.Item>
                      <Descriptions.Item label="Time Frame">
                        {outcome.timeFrame || 'N/A'}
                      </Descriptions.Item>
                      {outcome.category && (
                        <Descriptions.Item label="Category">
                          <Tag>{outcome.category}</Tag>
                        </Descriptions.Item>
                      )}
                    </Descriptions>
                  </Card>
                ))}
              </Space>
            </Card>
          </TabPane>

          <TabPane tab={`Locations (${locationsData.length})`} key="locations">
            <Card>
              <Table
                columns={locationColumns}
                dataSource={locationsData}
                rowKey="id"
                size="small"
                pagination={{ pageSize: 10 }}
              />
            </Card>
          </TabPane>

          <TabPane tab="Timeline Chart" key="timeline-chart">
            <Card>
              <TimelineChart
                events={timelineEvents}
                title="Trial Timeline Visualization"
              />
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </Container>
  );
};

export default TrialDetailPage;
