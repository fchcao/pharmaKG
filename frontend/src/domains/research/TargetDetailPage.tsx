import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Tabs,
  Descriptions,
  Tag,
  Space,
  Button,
  Typography,
  Alert,
  Spin,
  Statistic,
  Table,
  Divider,
  List,
} from 'antd';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  LinkOutlined,
  ExperimentOutlined,
  NodeIndexOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons';
import { useTarget, useTargetCompounds, useTargetPathways } from './hooks';
import { Target, Compound } from './types';
import { GraphViewer } from '@/shared/graphs';
import { DataTable, TableColumn } from '@/shared/components';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const TargetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [graphKey, setGraphKey] = useState(0);

  const {
    data: target,
    isLoading: loadingTarget,
    error: targetError,
  } = useTarget(id!);

  const {
    data: compounds,
    isLoading: loadingCompounds,
  } = useTargetCompounds(id!);

  const {
    data: pathways,
    isLoading: loadingPathways,
  } = useTargetPathways(id!);

  if (loadingTarget) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" tip="Loading target details..." />
      </div>
    );
  }

  if (targetError || !target) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Error"
          description={targetError?.message || 'Target not found'}
          type="error"
          showIcon
        />
      </div>
    );
  }

  // Compound columns
  const compoundColumns: TableColumn<Compound>[] = [
    {
      key: 'chemblId',
      title: 'ChEMBL ID',
      dataIndex: 'chemblId',
      width: 120,
      render: (chemblId: string, record: Compound) => (
        <a onClick={() => navigate(`/rd/compounds/${record.id}`)}>{chemblId}</a>
      ),
    },
    {
      key: 'name',
      title: 'Name',
      dataIndex: 'name',
      width: 200,
      render: (name: string, record: Compound) => (
        <a onClick={() => navigate(`/rd/compounds/${record.id}`)}>{name}</a>
      ),
    },
    {
      key: 'molecularWeight',
      title: 'MW (Da)',
      dataIndex: 'molecularWeight',
      width: 100,
      align: 'right' as const,
      render: (mw: number) => (mw ? mw.toFixed(2) : '-'),
    },
    {
      key: 'logp',
      title: 'LogP',
      dataIndex: 'logp',
      width: 80,
      align: 'right' as const,
      render: (logp: number) => (logp !== undefined ? logp.toFixed(2) : '-'),
    },
    {
      key: 'maxPhase',
      title: 'Max Phase',
      dataIndex: 'maxPhase',
      width: 100,
      align: 'center' as const,
      render: (phase: number) => {
        if (!phase) return <Text type="secondary">-</Text>;
        const phaseConfig: Record<number, { text: string; color: string }> = {
          0: { text: 'Research', color: 'default' },
          1: { text: 'Phase I', color: 'cyan' },
          2: { text: 'Phase II', color: 'blue' },
          3: { text: 'Phase III', color: 'geekblue' },
          4: { text: 'Approved', color: 'green' },
        };
        const config = phaseConfig[phase] || phaseConfig[0];
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1400px' }}>
      {/* Header */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/rd/targets')}
              >
                Back to Targets
              </Button>
              <Title level={2} style={{ margin: 0 }}>
                {target.name}
              </Title>
            </Space>
            <Space>
              <Button
                icon={<LinkOutlined />}
                href={`https://www.uniprot.org/uniprot/${target.uniprotId}`}
                target="_blank"
              >
                View in UniProt
              </Button>
              <Button icon={<ShareAltOutlined />}>Share</Button>
              <Button icon={<DownloadOutlined />}>Export</Button>
            </Space>
          </Space>
          <Space wrap style={{ marginTop: 8 }}>
            <Tag color="blue">{target.uniprotId}</Tag>
            {target.proteinType && (
              <Tag color="purple">{target.proteinType}</Tag>
            )}
            {target.organism && (
              <Tag color="green">{target.organism}</Tag>
            )}
            {target.geneFamily && (
              <Tag color="orange">{target.geneFamily}</Tag>
            )}
          </Space>
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Overview Tab */}
        <TabPane tab="Overview" key="overview">
          <Row gutter={[16, 16]}>
            {/* Basic Info */}
            <Col span={16}>
              <Card title="Target Information">
                <Descriptions column={2} bordered>
                  <Descriptions.Item label="UniProt ID" span={2}>
                    <Space>
                      <Text code>{target.uniprotId}</Text>
                      <Button
                        size="small"
                        type="link"
                        href={`https://www.uniprot.org/uniprot/${target.uniprotId}`}
                        target="_blank"
                        icon={<LinkOutlined />}
                      >
                        View in UniProt
                      </Button>
                    </Space>
                  </Descriptions.Item>
                  <Descriptions.Item label="Target Name" span={2}>
                    {target.name}
                  </Descriptions.Item>
                  <Descriptions.Item label="Protein Type" span={1}>
                    {target.proteinType || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Organism" span={1}>
                    {target.organism || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Gene Family" span={1}>
                    {target.geneFamily || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Gene Symbol" span={1}>
                    {target.geneSymbol || '-'}
                  </Descriptions.Item>
                </Descriptions>

                {target.description && (
                  <>
                    <Divider />
                    <Text strong>Description</Text>
                    <Paragraph style={{ marginTop: 8 }}>
                      {target.description}
                    </Paragraph>
                  </>
                )}
              </Card>

              {/* Associated Compounds */}
              <Card
                title={`Active Compounds (${compounds?.length || 0})`}
                style={{ marginTop: 16 }}
              >
                <DataTable<Compound>
                  columns={compoundColumns}
                  data={compounds || []}
                  loading={loadingCompounds}
                  pagination={{
                    page: 1,
                    pageSize: 10,
                    total: compounds?.length || 0,
                    onPageChange: () => {},
                  }}
                />
              </Card>
            </Col>

            {/* Quick Stats */}
            <Col span={8}>
              <Card title="Statistics">
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Statistic
                    title="Active Compounds"
                    value={compounds?.length || 0}
                    prefix={<MedicineBoxOutlined />}
                  />
                  <Statistic
                    title="Pathways"
                    value={pathways?.length || 0}
                    prefix={<NodeIndexOutlined />}
                  />
                  <Statistic
                    title="Approved Drugs"
                    value={compounds?.filter((c) => c.maxPhase === 4).length || 0}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Space>
              </Card>

              {/* External Links */}
              <Card title="External Resources" style={{ marginTop: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button
                    block
                    icon={<LinkOutlined />}
                    href={`https://www.uniprot.org/uniprot/${target.uniprotId}`}
                    target="_blank"
                  >
                    UniProt
                  </Button>
                  <Button
                    block
                    icon={<LinkOutlined />}
                    href={`https://www.ebi.ac.uk/chembl/g/targets/${target.chemblId}`}
                    target="_blank"
                  >
                    ChEMBL
                  </Button>
                  <Button
                    block
                    icon={<LinkOutlined />}
                    href={`https://www.genecards.org/cgi-bin/carddisp.pl?gene=${target.geneSymbol}`}
                    target="_blank"
                  >
                    GeneCards
                  </Button>
                </Space>
              </Card>

              {/* Disease Associations */}
              <Card
                title="Disease Associations"
                style={{ marginTop: 16 }}
                extra={<ExperimentOutlined />}
              >
                <List
                  size="small"
                  dataSource={[
                    { disease: 'Cancer', association: 'Strong' },
                    { disease: 'Inflammation', association: 'Moderate' },
                    { disease: 'Metabolic Disorders', association: 'Weak' },
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                        <Text>{item.disease}</Text>
                        <Tag
                          color={
                            item.association === 'Strong'
                              ? 'red'
                              : item.association === 'Moderate'
                              ? 'orange'
                              : 'default'
                          }
                        >
                          {item.association}
                        </Tag>
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Compounds Tab */}
        <TabPane
          tab={
            <span>
              <MedicineBoxOutlined />
              Compounds ({compounds?.length || 0})
            </span>
          }
          key="compounds"
        >
          <Card>
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Statistic
                  title="Total Compounds"
                  value={compounds?.length || 0}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Approved Drugs"
                  value={compounds?.filter((c) => c.maxPhase === 4).length || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Clinical Candidates"
                  value={
                    compounds?.filter((c) => c.maxPhase && c.maxPhase > 0 && c.maxPhase < 4)
                      .length || 0
                  }
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
            </Row>
            <DataTable<Compound>
              columns={compoundColumns}
              data={compounds || []}
              loading={loadingCompounds}
              pagination={{
                page: 1,
                pageSize: 20,
                total: compounds?.length || 0,
                onPageChange: () => {},
              }}
            />
          </Card>
        </TabPane>

        {/* Pathways Tab */}
        <TabPane
          tab={
            <span>
              <NodeIndexOutlined />
              Pathways ({pathways?.length || 0})
            </span>
          }
          key="pathways"
        >
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="Pathway Network" extra={
                <Button
                  size="small"
                  onClick={() => setGraphKey(graphKey + 1)}
                >
                  Refresh Layout
                </Button>
              }>
                {pathways && pathways.length > 0 ? (
                  <TargetPathwayGraph
                    target={target}
                    pathways={pathways}
                    key={graphKey}
                    onPathwayClick={(pathwayId) => navigate(`/rd/pathways/${pathwayId}`)}
                  />
                ) : (
                  <Alert
                    message="No pathway data available"
                    type="info"
                    showIcon
                  />
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
};

// Target-Pathway Graph Component
interface TargetPathwayGraphProps {
  target: Target;
  pathways: any[];
  onPathwayClick: (pathwayId: string) => void;
}

const TargetPathwayGraph: React.FC<TargetPathwayGraphProps> = ({
  target,
  pathways,
  onPathwayClick,
}) => {
  // Convert data to graph format
  const graphData = {
    nodes: [
      {
        id: target.id,
        label: target.name,
        type: 'Target' as const,
        properties: target,
      },
      ...pathways.map((pathway) => ({
        id: pathway.id,
        label: pathway.name,
        type: 'Pathway' as const,
        properties: pathway,
      })),
    ],
    edges: pathways.map((pathway) => ({
      id: `${target.id}-${pathway.id}`,
      source: target.id,
      target: pathway.id,
      label: 'PARTICIPATES_IN',
      type: 'PARTICIPATES_IN' as const,
    })),
  };

  return (
    <GraphViewer
      data={graphData}
      height="500px"
      onNodeClick={(node) => {
        if (node.type === 'Pathway') {
          onPathwayClick(node.id);
        }
      }}
    />
  );
};

export default TargetDetailPage;
