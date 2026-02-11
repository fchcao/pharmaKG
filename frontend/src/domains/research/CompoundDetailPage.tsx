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
  Tooltip,
} from 'antd';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  ApiOutlined,
  ExperimentOutlined,
  NodeIndexOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons';
import { useCompound, useCompoundTargets, useBioactivities } from './hooks';
import { Compound, BioactivityData } from './types';
import { GraphViewer } from '@/shared/graphs';
import { DataTable, TableColumn, MoleculeViewer } from '@/shared/components';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const CompoundDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [graphKey, setGraphKey] = useState(0);

  const {
    data: compound,
    isLoading: loadingCompound,
    error: compoundError,
  } = useCompound(id!);

  const {
    data: targets,
    isLoading: loadingTargets,
  } = useCompoundTargets(id!);

  const {
    data: bioactivities,
    isLoading: loadingBioactivities,
  } = useBioactivities(id!);

  if (loadingCompound) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" tip="Loading compound details..." />
      </div>
    );
  }

  if (compoundError || !compound) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Error"
          description={compoundError?.message || 'Compound not found'}
          type="error"
          showIcon
        />
      </div>
    );
  }

  // Calculate drug-likeness (Lipinski's Rule of Five)
  const lipinskiViolations = [
    compound.molecularWeight && compound.molecularWeight > 500,
    compound.logp && compound.logp > 5,
    compound.hbondDonors && compound.hbondDonors > 5,
    compound.hbondAcceptors && compound.hbondAcceptors > 10,
  ].filter(Boolean).length;

  const isDrugLike = lipinskiViolations <= 1;

  // Bioactivity columns
  const bioactivityColumns: TableColumn<BioactivityData>[] = [
    {
      key: 'targetId',
      title: 'Target',
      dataIndex: 'targetId',
      width: 150,
      render: (targetId: string) => (
        <a onClick={() => navigate(`/rd/targets/${targetId}`)}>{targetId}</a>
      ),
    },
    {
      key: 'activityType',
      title: 'Activity Type',
      dataIndex: 'activityType',
      width: 120,
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      key: 'activityValue',
      title: 'Value',
      dataIndex: 'activityValue',
      width: 100,
      align: 'right' as const,
      render: (value: number, record) => (
        <Text>
          {value?.toFixed(2)} {record.activityUnit}
        </Text>
      ),
    },
    {
      key: 'confidenceScore',
      title: 'Confidence',
      dataIndex: 'confidenceScore',
      width: 100,
      align: 'center' as const,
      render: (score: number) => {
        if (!score) return '-';
        const color = score > 0.8 ? 'green' : score > 0.5 ? 'orange' : 'red';
        return <Tag color={color}>{(score * 100).toFixed(0)}%</Tag>;
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
                onClick={() => navigate('/rd/compounds')}
              >
                Back to Compounds
              </Button>
              <Title level={2} style={{ margin: 0 }}>
                {compound.name}
              </Title>
            </Space>
            <Space>
              <Button icon={<ShareAltOutlined />}>Share</Button>
              <Button icon={<DownloadOutlined />}>Export</Button>
            </Space>
          </Space>
          <Space wrap style={{ marginTop: 8 }}>
            <Tag color="blue">{compound.chemblId}</Tag>
            {compound.maxPhase === 4 && (
              <Tag color="green">Approved Drug</Tag>
            )}
            {compound.drugType && (
              <Tag color="purple">{compound.drugType}</Tag>
            )}
          </Space>
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Overview Tab */}
        <TabPane tab="Overview" key="overview">
          <Row gutter={[16, 16]}>
            {/* Compound Structure */}
            <Col span={10}>
              <Card title="Molecular Structure" extra={
                compound.smiles && (
                  <Button size="small" icon={<DownloadOutlined />}>
                    Download
                  </Button>
                )
              }>
                {compound.smiles ? (
                  <MoleculeViewer
                    smiles={compound.smiles}
                    name={compound.name}
                    width={300}
                    height={300}
                    showControls={true}
                  />
                ) : (
                  <Alert
                    message="No structure data available"
                    type="info"
                    showIcon
                  />
                )}
                {compound.smiles && (
                  <div style={{ marginTop: 16 }}>
                    <Text strong>SMILES:</Text>
                    <Paragraph code copyable style={{ marginTop: 4 }}>
                      {compound.smiles}
                    </Paragraph>
                  </div>
                )}
              </Card>
            </Col>

            {/* Basic Properties */}
            <Col span={14}>
              <Card title="Basic Properties">
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="Molecular Weight"
                      value={compound.molecularWeight}
                      precision={2}
                      suffix="Da"
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="LogP"
                      value={compound.logp}
                      precision={2}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="Rotatable Bonds"
                      value={compound.rotatableBonds || '-'}
                    />
                  </Col>
                </Row>
                <Divider />
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="H-Bond Donors">
                    {compound.hbondDonors || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="H-Bond Acceptors">
                    {compound.hbondAcceptors || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="InChI Key">
                    <Text code copyable={{ text: compound.inchikey }}>
                      {compound.inchikey?.slice(0, 20)}...
                    </Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="Drug-Likeness">
                    <Tag color={isDrugLike ? 'green' : 'orange'}>
                      {isDrugLike ? 'Yes' : 'No'}
                    </Tag>
                    <Text type="secondary" style={{ marginLeft: 8 }}>
                      ({lipinskiViolations} Lipinski violations)
                    </Text>
                  </Descriptions.Item>
                </Descriptions>

                {compound.description && (
                  <>
                    <Divider />
                    <Text strong>Description</Text>
                    <Paragraph style={{ marginTop: 8 }}>
                      {compound.description}
                    </Paragraph>
                  </>
                )}
              </Card>

              {/* Drug Repurposing Opportunities */}
              <Card
                title="Drug Repurposing Opportunities"
                style={{ marginTop: 16 }}
                extra={<Tooltip title="AI-suggested therapeutic areas"><MedicineBoxOutlined /></Tooltip>}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Alert
                    message="Potential for Oncology Applications"
                    description="This compound shows activity against kinases involved in cancer pathways"
                    type="info"
                    showIcon
                  />
                  <Alert
                    message="Anti-inflammatory Potential"
                    description="Structural similarity to known NSAIDs suggests possible use in inflammatory conditions"
                    type="success"
                    showIcon
                  />
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Bioactivity Tab */}
        <TabPane
          tab={
            <span>
              <ExperimentOutlined />
              Bioactivity ({bioactivities?.length || 0})
            </span>
          }
          key="bioactivity"
        >
          <Card>
            <DataTable<BioactivityData>
              columns={bioactivityColumns}
              data={bioactivities || []}
              loading={loadingBioactivities}
              pagination={{
                page: 1,
                pageSize: 20,
                total: bioactivities?.length || 0,
                onPageChange: () => {},
              }}
            />
          </Card>
        </TabPane>

        {/* Targets Tab */}
        <TabPane
          tab={
            <span>
              <ApiOutlined />
              Targets ({targets?.length || 0})
            </span>
          }
          key="targets"
        >
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="Target Graph" extra={
                <Button
                  size="small"
                  onClick={() => setGraphKey(graphKey + 1)}
                >
                  Refresh Layout
                </Button>
              }>
                {targets && targets.length > 0 ? (
                  <CompoundTargetGraph
                    compound={compound}
                    targets={targets}
                    key={graphKey}
                    onTargetClick={(targetId) => navigate(`/rd/targets/${targetId}`)}
                  />
                ) : (
                  <Alert
                    message="No target data available"
                    type="info"
                    showIcon
                  />
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Pathways Tab */}
        <TabPane
          tab={
            <span>
              <NodeIndexOutlined />
              Pathways
            </span>
          }
          key="pathways"
        >
          <Card>
            <Alert
              message="Pathway analysis"
              description="View biological pathways this compound participates in"
              type="info"
              showIcon
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

// Compound-Target Graph Component
interface CompoundTargetGraphProps {
  compound: Compound;
  targets: any[];
  onTargetClick: (targetId: string) => void;
}

const CompoundTargetGraph: React.FC<CompoundTargetGraphProps> = ({
  compound,
  targets,
  onTargetClick,
}) => {
  // Convert data to graph format
  const graphData = {
    nodes: [
      {
        id: compound.id,
        label: compound.name,
        type: 'Compound' as const,
        properties: compound,
      },
      ...targets.map((target) => ({
        id: target.id,
        label: target.name,
        type: 'Target' as const,
        properties: target,
      })),
    ],
    edges: targets.map((target) => ({
      id: `${compound.id}-${target.id}`,
      source: compound.id,
      target: target.id,
      label: 'TARGETS',
      type: 'TARGETS' as const,
    })),
  };

  return (
    <GraphViewer
      data={graphData}
      height="500px"
      onNodeClick={(node) => {
        if (node.type === 'Target') {
          onTargetClick(node.id);
        }
      }}
    />
  );
};

export default CompoundDetailPage;
