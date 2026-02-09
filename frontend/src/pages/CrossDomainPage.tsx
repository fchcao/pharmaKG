/**
 * CrossDomainPage.tsx - Cross-domain query builder for PharmaKG
 * Visual query interface for multi-hop cross-domain queries
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  Button,
  Form,
  InputNumber,
  Checkbox,
  Space,
  Divider,
  Tag,
  Tabs,
  Table,
  Alert,
  Tooltip,
  message,
  Modal,
  Input,
  Empty,
  Spin,
  Badge
} from 'antd';
import {
  SearchOutlined,
  NodeIndexOutlined,
  BranchesOutlined,
  SaveOutlined,
  HistoryOutlined,
  ShareAltOutlined,
  DownloadOutlined,
  ClearOutlined,
  ThunderboltOutlined,
  ExperimentOutlined,
  SafetyCertificateOutlined,
  WarningOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { GraphViewer, GraphData, GraphNode, GraphEdge } from '@/shared/graphs/GraphViewer';
import api from '@/services/api';

const { TabPane } = Tabs;
const { Option } = Select;

// Domain entity types
const DOMAINS = {
  research: {
    name: 'R&D',
    color: '#4CAF50',
    entities: ['Compound', 'Target', 'Assay', 'Pathway', 'Disease']
  },
  clinical: {
    name: 'Clinical',
    color: '#E91E63',
    entities: ['ClinicalTrial', 'Condition', 'Intervention', 'Outcome', 'AdverseEvent']
  },
  supply: {
    name: 'Supply Chain',
    color: '#795548',
    entities: ['Manufacturer', 'Supplier', 'Facility', 'DrugProduct', 'DrugShortage']
  },
  regulatory: {
    name: 'Regulatory',
    color: '#FF5722',
    entities: ['Submission', 'Approval', 'RegulatoryAgency', 'ComplianceAction', 'Document']
  }
};

// Relationship types for filtering
const RELATIONSHIP_TYPES = [
  'TARGETS', 'BINDS_TO', 'INHIBITS', 'ACTIVATES', 'MODULATES',
  'TREATS', 'PREVENTS', 'ASSOCIATED_WITH_DISEASE', 'BIOMARKER_FOR',
  'PARTICIPATES_IN', 'REGULATES_PATHWAY',
  'TESTED_IN_CLINICAL_TRIAL', 'REPORTED_ADVERSE_EVENT',
  'MANUFACTURES', 'PRODUCES_ACTIVE_INGREDIENT', 'SUPPLIES_TO',
  'EXPERIENCES_SHORTAGE', 'COMPETES_WITH',
  'SUBMITTED_TO', 'APPROVED_BY', 'REQUIRES_INSPECTION',
  'HAS_SAFETY_SIGNAL', 'CAUSES_ADVERSE_EVENT', 'WARNED_ABOUT'
];

// Pre-built query templates
const QUERY_TEMPLATES = [
  {
    id: 'drug-to-approval',
    name: 'Drug to Approval',
    description: 'Trace the complete journey from compound to regulatory approval',
    icon: <SafetyCertificateOutlined />,
    domains: ['research', 'clinical', 'regulatory'],
    path: 'Compound → ClinicalTrial → Submission → Approval',
    defaultConfig: {
      startEntityType: 'Compound',
      endEntityType: 'Approval',
      maxHops: 4,
      relationshipTypes: ['TESTED_IN_CLINICAL_TRIAL', 'SUBMITTED_TO', 'APPROVED_BY']
    }
  },
  {
    id: 'supply-chain-risk',
    name: 'Supply Chain Risk',
    description: 'Analyze manufacturing risks and potential shortages',
    icon: <WarningOutlined />,
    domains: ['supply', 'regulatory'],
    path: 'Manufacturer → Facility → Inspection → ComplianceAction → Shortage',
    defaultConfig: {
      startEntityType: 'Manufacturer',
      endEntityType: 'DrugShortage',
      maxHops: 4,
      relationshipTypes: ['OPERATES', 'REQUIRES_INSPECTION', 'FAILED_INSPECTION', 'EXPERIENCES_SHORTAGE']
    }
  },
  {
    id: 'target-discovery',
    name: 'Target Discovery',
    description: 'Find compounds targeting specific proteins and their clinical outcomes',
    icon: <ExperimentOutlined />,
    domains: ['research', 'clinical'],
    path: 'Target → Compound → ClinicalTrial → Outcome',
    defaultConfig: {
      startEntityType: 'Target',
      endEntityType: 'ClinicalTrial',
      maxHops: 3,
      relationshipTypes: ['INHIBITS', 'ACTIVATES', 'TESTED_IN_CLINICAL_TRIAL']
    }
  },
  {
    id: 'competitive-analysis',
    name: 'Competitive Analysis',
    description: 'Compare competing drugs and their development status',
    icon: <BranchesOutlined />,
    domains: ['research', 'regulatory'],
    path: 'Company → Compound → Trial → Submission → Approval',
    defaultConfig: {
      startEntityType: 'Company',
      endEntityType: 'Approval',
      maxHops: 4,
      relationshipTypes: ['DEVELOPS', 'TESTED_IN_CLINICAL_TRIAL', 'SUBMITTED_TO', 'APPROVED_BY']
    }
  },
  {
    id: 'safety-propagation',
    name: 'Safety Signal Analysis',
    description: 'Track safety signals across compounds, trials, and regulatory actions',
    icon: <WarningOutlined />,
    domains: ['research', 'clinical', 'regulatory'],
    path: 'Compound → AdverseEvent → SafetySignal → ComplianceAction',
    defaultConfig: {
      startEntityType: 'Compound',
      endEntityType: 'ComplianceAction',
      maxHops: 4,
      relationshipTypes: ['CAUSES_ADVERSE_EVENT', 'HAS_SAFETY_SIGNAL', 'WARNED_ABOUT']
    }
  }
];

interface QueryConfig {
  startEntityType: string;
  startEntityId?: string;
  endEntityType: string;
  endEntityId?: string;
  maxHops: number;
  relationshipTypes: string[];
  selectedDomains: string[];
}

interface PathResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  length: number;
  path: string[];
}

interface QueryHistory {
  id: string;
  name: string;
  config: QueryConfig;
  timestamp: number;
  resultCount: number;
}

const CrossDomainPage: React.FC = () => {
  const [form] = Form.useForm();
  const graphViewerRef = useRef<any>(null);

  // State
  const [queryConfig, setQueryConfig] = useState<QueryConfig>({
    startEntityType: 'Compound',
    endEntityType: 'ClinicalTrial',
    maxHops: 3,
    relationshipTypes: [],
    selectedDomains: ['research', 'clinical']
  });
  const [loading, setLoading] = useState(false);
  const [paths, setPaths] = useState<PathResult[]>([]);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [shareModalVisible, setShareModalVisible] = useState(false);
  const [shareUrl, setShareUrl] = useState<string>('');
  const [activeTab, setActiveTab] = useState('builder');

  // Load query history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('crossDomainQueryHistory');
    if (savedHistory) {
      try {
        setQueryHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('Failed to parse query history:', e);
      }
    }
  }, []);

  // Save query to history
  const saveQueryToHistory = (config: QueryConfig, resultCount: number) => {
    const newHistory: QueryHistory = {
      id: Date.now().toString(),
      name: `${config.startEntityType} → ${config.endEntityType}`,
      config,
      timestamp: Date.now(),
      resultCount
    };

    const updatedHistory = [newHistory, ...queryHistory].slice(0, 20); // Keep last 20
    setQueryHistory(updatedHistory);
    localStorage.setItem('crossDomainQueryHistory', JSON.stringify(updatedHistory));
  };

  // Execute cross-domain query
  const executeQuery = async (config: QueryConfig) => {
    setLoading(true);
    setPaths([]);
    setGraphData({ nodes: [], edges: [] });

    try {
      // Call the advanced query API
      const response = await api.get('/advanced/path/shortest', {
        params: {
          start_entity_type: config.startEntityType,
          start_entity_id: config.startEntityId,
          end_entity_type: config.endEntityType,
          end_entity_id: config.endEntityId,
          max_path_length: config.maxHops,
          relationship_types: config.relationshipTypes.length > 0 ? config.relationshipTypes.join(',') : undefined
        }
      });

      if (response.data && response.data.paths) {
        const pathResults: PathResult[] = response.data.paths.map((path: any) => ({
          nodes: path.nodes.map((node: any) => ({
            id: node.id,
            label: node.name || node.id,
            type: node.type,
            properties: node
          })),
          edges: path.edges.map((edge: any, idx: number) => ({
            id: `edge-${idx}`,
            source: edge.source,
            target: edge.target,
            type: edge.type,
            label: edge.type,
            properties: edge
          })),
          length: path.length,
          path: path.path_types || []
        }));

        setPaths(pathResults);

        // Convert to graph data for visualization
        const allNodes = new Map<string, GraphNode>();
        const allEdges = new Map<string, GraphEdge>();

        pathResults.forEach(path => {
          path.nodes.forEach(node => {
            if (!allNodes.has(node.id)) {
              allNodes.set(node.id, node);
            }
          });
          path.edges.forEach(edge => {
            if (!allEdges.has(edge.id)) {
              allEdges.set(edge.id, edge);
            }
          });
        });

        setGraphData({
          nodes: Array.from(allNodes.values()),
          edges: Array.from(allEdges.values())
        });

        saveQueryToHistory(config, pathResults.length);
        message.success(`Found ${pathResults.length} path(s)`);
      } else {
        message.info('No paths found between the specified entities');
      }
    } catch (error: any) {
      console.error('Query execution error:', error);
      message.error(error.response?.data?.message || 'Failed to execute query');
    } finally {
      setLoading(false);
    }
  };

  // Apply query template
  const applyTemplate = (template: typeof QUERY_TEMPLATES[0]) => {
    setSelectedTemplate(template.id);
    form.setFieldsValue(template.defaultConfig);
    setQueryConfig(template.defaultConfig);
    message.success(`Applied template: ${template.name}`);
  };

  // Handle form submission
  const handleSubmit = () => {
    form.validateFields().then((values) => {
      const config: QueryConfig = {
        ...values,
        relationshipTypes: values.relationshipTypes || []
      };
      setQueryConfig(config);
      executeQuery(config);
    });
  };

  // Load query from history
  const loadQueryFromHistory = (historyItem: QueryHistory) => {
    form.setFieldsValue(historyItem.config);
    setQueryConfig(historyItem.config);
    setHistoryModalVisible(false);
    message.success('Loaded query from history');
  };

  // Share query
  const shareQuery = () => {
    const queryParams = new URLSearchParams();
    Object.entries(queryConfig).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        queryParams.append(key, value.join(','));
      } else if (value !== undefined && value !== null) {
        queryParams.append(key, String(value));
      }
    });

    const url = `${window.location.origin}/cross-domain?${queryParams.toString()}`;
    setShareUrl(url);
    setShareModalVisible(true);
  };

  // Export results
  const exportResults = (format: 'csv' | 'json' | 'png') => {
    if (format === 'png' && graphViewerRef.current) {
      const pngData = graphViewerRef.current.exportAs('png');
      const link = document.createElement('a');
      link.download = `cross-domain-query-${Date.now()}.png`;
      link.href = pngData as string;
      link.click();
    } else if (format === 'json') {
      const dataStr = JSON.stringify({ paths, graphData }, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `cross-domain-query-${Date.now()}.json`;
      link.href = url;
      link.click();
    } else if (format === 'csv') {
      // Convert paths to CSV
      const headers = ['Path ID', 'Length', 'Nodes', 'Edges'];
      const rows = paths.map((path, idx) => [
        idx + 1,
        path.length,
        path.nodes.map(n => n.label).join(' → '),
        path.edges.map(e => e.type).join(' → ')
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `cross-domain-query-${Date.now()}.csv`;
      link.href = url;
      link.click();
    }
    message.success(`Exported as ${format.toUpperCase()}`);
  };

  // Table columns for path results
  const pathColumns: ColumnsType<PathResult> = [
    {
      title: 'Path',
      dataIndex: 'path',
      key: 'path',
      render: (path: string[], record: PathResult) => (
        <Space size="small" wrap>
          {record.nodes.map((node, idx) => (
            <React.Fragment key={node.id}>
              <Tag color={DOMAINS[Object.entries(DOMAINS).find(([_, d]) =>
                d.entities.includes(node.type))?.[0] as keyof typeof DOMAINS || 'research']?.color}>
                {node.label}
              </Tag>
              {idx < record.edges.length && (
                <span style={{ color: '#999' }}>{record.edges[idx].type}</span>
              )}
            </React.Fragment>
          ))}
        </Space>
      )
    },
    {
      title: 'Length',
      dataIndex: 'length',
      key: 'length',
      width: 100,
      render: (length: number) => <Badge count={length} style={{ backgroundColor: '#52c41a' }} />
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record: PathResult) => (
        <Button
          type="link"
          size="small"
          onClick={() => {
            setGraphData({
              nodes: record.nodes,
              edges: record.edges
            });
            setTimeout(() => {
              graphViewerRef.current?.fit();
            }, 100);
          }}
        >
          View Path
        </Button>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[24, 24]}>
        {/* Header */}
        <Col span={24}>
          <Card>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space>
                  <BranchesOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                  <div>
                    <h2 style={{ margin: 0 }}>Cross-Domain Query Builder</h2>
                    <p style={{ margin: 0, color: '#666' }}>
                      Explore relationships across R&D, Clinical, Supply Chain, and Regulatory domains
                    </p>
                  </div>
                </Space>
                <Space>
                  <Button
                    icon={<HistoryOutlined />}
                    onClick={() => setHistoryModalVisible(true)}
                  >
                    History
                  </Button>
                  <Button
                    icon={<ShareAltOutlined />}
                    onClick={shareQuery}
                  >
                    Share
                  </Button>
                </Space>
              </div>

              <Tabs activeKey={activeTab} onChange={setActiveTab}>
                <TabPane tab="Query Builder" key="builder">
                  {/* Query Templates */}
                  <Divider orientation="left">Quick Start Templates</Divider>
                  <Row gutter={[16, 16]}>
                    {QUERY_TEMPLATES.map(template => (
                      <Col xs={24} sm={12} md={8} lg={6} key={template.id}>
                        <Card
                          hoverable
                          size="small"
                          onClick={() => applyTemplate(template)}
                          style={{
                            border: selectedTemplate === template.id ? '2px solid #1890ff' : undefined,
                            height: '100%'
                          }}
                        >
                          <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Space>
                              {template.icon}
                              <span style={{ fontWeight: 'bold' }}>{template.name}</span>
                            </Space>
                            <p style={{ margin: 0, fontSize: 12, color: '#666' }}>
                              {template.description}
                            </p>
                            <div>
                              {template.domains.map(domain => (
                                <Tag key={domain} color={DOMAINS[domain as keyof typeof DOMAINS]?.color}>
                                  {DOMAINS[domain as keyof typeof DOMAINS]?.name}
                                </Tag>
                              ))}
                            </div>
                            <div style={{ fontSize: 11, color: '#999' }}>
                              {template.path}
                            </div>
                          </Space>
                        </Card>
                      </Col>
                    ))}
                  </Row>

                  {/* Query Builder Form */}
                  <Divider orientation="left">Custom Query</Divider>
                  <Form
                    form={form}
                    layout="vertical"
                    initialValues={queryConfig}
                  >
                    <Row gutter={24}>
                      <Col xs={24} md={12}>
                        <Form.Item
                          label="Start Entity Type"
                          name="startEntityType"
                          rules={[{ required: true, message: 'Please select start entity type' }]}
                        >
                          <Select
                            placeholder="Select start entity type"
                            showSearch
                            optionFilterProp="children"
                          >
                            {Object.entries(DOMAINS).map(([domainKey, domain]) => (
                              <Select.OptGroup key={domainKey} label={domain.name}>
                                {domain.entities.map(entity => (
                                  <Option key={entity} value={entity}>
                                    <NodeIndexOutlined /> {entity}
                                  </Option>
                                ))}
                              </Select.OptGroup>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>

                      <Col xs={24} md={12}>
                        <Form.Item
                          label="End Entity Type"
                          name="endEntityType"
                          rules={[{ required: true, message: 'Please select end entity type' }]}
                        >
                          <Select
                            placeholder="Select end entity type"
                            showSearch
                            optionFilterProp="children"
                          >
                            {Object.entries(DOMAINS).map(([domainKey, domain]) => (
                              <Select.OptGroup key={domainKey} label={domain.name}>
                                {domain.entities.map(entity => (
                                  <Option key={entity} value={entity}>
                                    <NodeIndexOutlined /> {entity}
                                  </Option>
                                ))}
                              </Select.OptGroup>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>

                      <Col xs={24} md={12}>
                        <Form.Item
                          label="Start Entity ID (Optional)"
                          name="startEntityId"
                          tooltip="Leave empty to find paths from all entities of this type"
                        >
                          <Input placeholder="e.g., CHEMBL123" />
                        </Form.Item>
                      </Col>

                      <Col xs={24} md={12}>
                        <Form.Item
                          label="End Entity ID (Optional)"
                          name="endEntityId"
                          tooltip="Leave empty to find paths to all entities of this type"
                        >
                          <Input placeholder="e.g., NCT00012345" />
                        </Form.Item>
                      </Col>

                      <Col xs={24} md={12}>
                        <Form.Item
                          label="Maximum Path Length (Hops)"
                          name="maxHops"
                          rules={[{ required: true, message: 'Please specify max hops' }]}
                        >
                          <InputNumber min={1} max={5} style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>

                      <Col xs={24} md={12}>
                        <Form.Item
                          label="Relationship Types"
                          name="relationshipTypes"
                          tooltip="Leave empty to include all relationship types"
                        >
                          <Select
                            mode="multiple"
                            placeholder="Select relationship types"
                            allowClear
                            maxTagCount={3}
                          >
                            {RELATIONSHIP_TYPES.map(rel => (
                              <Option key={rel} value={rel}>
                                {rel}
                              </Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>

                      <Col xs={24}>
                        <Form.Item
                          label="Filter by Domains"
                          name="selectedDomains"
                        >
                          <Checkbox.Group>
                            <Space>
                              {Object.entries(DOMAINS).map(([key, domain]) => (
                                <Checkbox key={key} value={key}>
                                  <Tag color={domain.color}>{domain.name}</Tag>
                                </Checkbox>
                              ))}
                            </Space>
                          </Checkbox.Group>
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item>
                      <Space>
                        <Button
                          type="primary"
                          icon={<SearchOutlined />}
                          onClick={handleSubmit}
                          loading={loading}
                          size="large"
                        >
                          Execute Query
                        </Button>
                        <Button
                          icon={<ClearOutlined />}
                          onClick={() => {
                            form.resetFields();
                            setPaths([]);
                            setGraphData({ nodes: [], edges: [] });
                            setSelectedTemplate(null);
                          }}
                        >
                          Clear
                        </Button>
                      </Space>
                    </Form.Item>
                  </Form>
                </TabPane>

                <TabPane tab="Results" key="results" disabled={paths.length === 0}>
                  {loading ? (
                    <div style={{ textAlign: 'center', padding: '50px' }}>
                      <Spin size="large" />
                      <p style={{ marginTop: 16 }}>Executing cross-domain query...</p>
                    </div>
                  ) : paths.length > 0 ? (
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                      <Alert
                        message={`Found ${paths.length} path(s)`}
                        description="Click 'View Path' to visualize individual paths or use the graph viewer below to see all results."
                        type="success"
                        showIcon
                      />

                      <Card title="Graph Visualization" extra={
                        <Space>
                          <Button size="small" onClick={() => graphViewerRef.current?.fit()}>
                            Fit View
                          </Button>
                          <Button size="small" onClick={() => exportResults('png')}>
                            <DownloadOutlined /> PNG
                          </Button>
                        </Space>
                      }>
                        <GraphViewer
                          ref={graphViewerRef}
                          data={graphData}
                          height="600px"
                        />
                      </Card>

                      <Card title="Path Details" extra={
                        <Space>
                          <Button size="small" onClick={() => exportResults('csv')}>
                            <DownloadOutlined /> CSV
                          </Button>
                          <Button size="small" onClick={() => exportResults('json')}>
                            <DownloadOutlined /> JSON
                          </Button>
                        </Space>
                      }>
                        <Table
                          columns={pathColumns}
                          dataSource={paths}
                          rowKey={(record, idx) => idx?.toString() || '0'}
                          pagination={{ pageSize: 10 }}
                          size="small"
                        />
                      </Card>
                    </Space>
                  ) : (
                    <Empty description="No results yet. Execute a query to see results." />
                  )}
                </TabPane>
              </Tabs>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Query History Modal */}
      <Modal
        title="Query History"
        visible={historyModalVisible}
        onCancel={() => setHistoryModalVisible(false)}
        footer={null}
        width={800}
      >
        {queryHistory.length > 0 ? (
          <Table
            columns={[
              {
                title: 'Query',
                dataIndex: 'name',
                key: 'name'
              },
              {
                title: 'Results',
                dataIndex: 'resultCount',
                key: 'resultCount',
                render: (count: number) => `${count} path(s)`
              },
              {
                title: 'Date',
                dataIndex: 'timestamp',
                key: 'timestamp',
                render: (ts: number) => new Date(ts).toLocaleString()
              },
              {
                title: 'Actions',
                key: 'actions',
                render: (_, record: QueryHistory) => (
                  <Space>
                    <Button type="link" size="small" onClick={() => loadQueryFromHistory(record)}>
                      Load
                    </Button>
                    <Button
                      type="link"
                      size="small"
                      danger
                      onClick={() => {
                        const updated = queryHistory.filter(h => h.id !== record.id);
                        setQueryHistory(updated);
                        localStorage.setItem('crossDomainQueryHistory', JSON.stringify(updated));
                      }}
                    >
                      Delete
                    </Button>
                  </Space>
                )
              }
            ]}
            dataSource={queryHistory}
            rowKey="id"
            pagination={{ pageSize: 5 }}
            size="small"
          />
        ) : (
          <Empty description="No query history yet." />
        )}
      </Modal>

      {/* Share Query Modal */}
      <Modal
        title="Share Query"
        visible={shareModalVisible}
        onCancel={() => setShareModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setShareModalVisible(false)}>
            Close
          </Button>,
          <Button
            key="copy"
            type="primary"
            onClick={() => {
              navigator.clipboard.writeText(shareUrl);
              message.success('URL copied to clipboard');
            }}
          >
            Copy URL
          </Button>
        ]}
      >
        <Input.TextArea
          value={shareUrl}
          readOnly
          autoSize={{ minRows: 3, maxRows: 6 }}
          style={{ marginBottom: 16 }}
        />
        <Alert
          message="Share this URL to let others view and execute the same query"
          type="info"
          showIcon
        />
      </Modal>
    </div>
  );
};

export default CrossDomainPage;
