/**
 * CrossDomainResultsPage.tsx - Cross-domain query results page
 * Standalone page for displaying cross-domain query results with visualization and export
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Alert,
  Table,
  Tag,
  Badge,
  Spin,
  Empty,
  Descriptions,
  Statistic,
  Progress,
  Tabs,
  Divider,
  Tooltip,
  message,
  Select
} from 'antd';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  ReloadOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  FileTextOutlined,
  FileImageOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { GraphViewer, GraphData, GraphNode, GraphEdge } from '@/shared/graphs/GraphViewer';
import api from '@/services/api';

const { Option } = Select;

// Domain entity types with colors
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

interface PathResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  length: number;
  path: string[];
  weight?: number;
  confidence?: number;
}

interface QueryConfig {
  startEntityType: string;
  startEntityId?: string;
  endEntityType: string;
  endEntityId?: string;
  maxHops: number;
  relationshipTypes: string[];
  selectedDomains: string[];
}

interface QueryResult {
  paths: PathResult[];
  graphData: GraphData;
  queryConfig: QueryConfig;
  timestamp: number;
  totalPaths: number;
}

const CrossDomainResultsPage: React.FC = () => {
  const { queryId } = useParams<{ queryId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const graphViewerRef = useRef<any>(null);

  // State
  const [loading, setLoading] = useState(true);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [filteredPaths, setFilteredPaths] = useState<PathResult[]>([]);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedPathLength, setSelectedPathLength] = useState<number[]>([]);
  const [selectedDomains, setSelectedDomains] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [pathPagination, setPathPagination] = useState({ current: 1, pageSize: 10 });

  // Load query results
  useEffect(() => {
    loadQueryResults();
  }, [queryId, location.state]);

  // Apply filters
  useEffect(() => {
    if (queryResult) {
      let filtered = [...queryResult.paths];

      // Filter by path length
      if (selectedPathLength.length > 0) {
        filtered = filtered.filter(path => selectedPathLength.includes(path.length));
      }

      // Filter by domains in path
      if (selectedDomains.length > 0) {
        filtered = filtered.filter(path => {
          const pathDomains = new Set(
            path.nodes.map(node => {
              const entry = Object.entries(DOMAINS).find(([_, d]) => d.entities.includes(node.type));
              return entry?.[0] || '';
            }).filter(d => d)
          );
          return selectedDomains.some(domain => pathDomains.has(domain));
        });
      }

      setFilteredPaths(filtered);
    }
  }, [queryResult, selectedPathLength, selectedDomains]);

  const loadQueryResults = async () => {
    setLoading(true);

    try {
      // Try to get results from location state first
      if (location.state?.results) {
        const results = location.state.results as QueryResult;
        setQueryResult(results);
        setFilteredPaths(results.paths);
        setGraphData(results.graphData);
        setLoading(false);
        return;
      }

      // Try to load from localStorage using queryId
      if (queryId) {
        const savedResults = localStorage.getItem(`queryResult_${queryId}`);
        if (savedResults) {
          const results = JSON.parse(savedResults) as QueryResult;
          setQueryResult(results);
          setFilteredPaths(results.paths);
          setGraphData(results.graphData);
          setLoading(false);
          return;
        }
      }

      // Try to load from recent query
      const recentResults = localStorage.getItem('recentCrossDomainQuery');
      if (recentResults) {
        const results = JSON.parse(recentResults) as QueryResult;
        setQueryResult(results);
        setFilteredPaths(results.paths);
        setGraphData(results.graphData);
        setLoading(false);
        return;
      }

      // No results found
      message.warning('No query results found. Please execute a query first.');
      navigate('/cross-domain');
    } catch (error) {
      console.error('Failed to load query results:', error);
      message.error('Failed to load query results');
      navigate('/cross-domain');
    } finally {
      setLoading(false);
    }
  };

  // Get domain for entity type
  const getDomainForEntityType = (entityType: string) => {
    return Object.entries(DOMAINS).find(([_, domain]) =>
      domain.entities.includes(entityType)
    )?.[0] || 'research';
  };

  // Export results
  const exportResults = (format: 'csv' | 'json' | 'png' | 'svg') => {
    if (!queryResult) return;

    if (format === 'png' && graphViewerRef.current) {
      const pngData = graphViewerRef.current.exportAs('png');
      const link = document.createElement('a');
      link.download = `cross-domain-results-${Date.now()}.png`;
      link.href = pngData as string;
      link.click();
      message.success('Exported as PNG');
    } else if (format === 'json') {
      const dataStr = JSON.stringify(queryResult, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `cross-domain-results-${Date.now()}.json`;
      link.href = url;
      link.click();
      message.success('Exported as JSON');
    } else if (format === 'csv') {
      const headers = ['Path ID', 'Length', 'Nodes', 'Edges', 'Weight', 'Confidence'];
      const rows = filteredPaths.map((path, idx) => [
        idx + 1,
        path.length,
        path.nodes.map(n => n.label).join(' → '),
        path.edges.map(e => e.type).join(' → '),
        path.weight || 'N/A',
        path.confidence || 'N/A'
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `cross-domain-results-${Date.now()}.csv`;
      link.href = url;
      link.click();
      message.success('Exported as CSV');
    }
  };

  // Share results
  const shareResults = () => {
    if (!queryResult) return;

    const shareId = `query_${Date.now()}`;
    localStorage.setItem(`queryResult_${shareId}`, JSON.stringify(queryResult));
    const shareUrl = `${window.location.origin}/cross-domain/results/${shareId}`;

    navigator.clipboard.writeText(shareUrl).then(() => {
      message.success('Share link copied to clipboard');
    });
  };

  // View specific path in graph
  const viewPath = (path: PathResult) => {
    setGraphData({
      nodes: path.nodes,
      edges: path.edges
    });
    setTimeout(() => {
      graphViewerRef.current?.fit();
    }, 100);
  };

  // View all paths in graph
  const viewAllPaths = () => {
    if (!queryResult) return;

    const allNodes = new Map<string, GraphNode>();
    const allEdges = new Map<string, GraphEdge>();

    queryResult.paths.forEach(path => {
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
    setTimeout(() => {
      graphViewerRef.current?.fit();
    }, 100);
  };

  // Table columns for path results
  const pathColumns: ColumnsType<PathResult> = [
    {
      title: 'Path',
      dataIndex: 'path',
      key: 'path',
      render: (_: any, record: PathResult, index: number) => (
        <Space size="small" wrap>
          {record.nodes.map((node, idx) => (
            <React.Fragment key={node.id}>
              <Tag
                color={DOMAINS[getDomainForEntityType(node.type) as keyof typeof DOMAINS]?.color}
                style={{ margin: '2px' }}
              >
                {node.label}
              </Tag>
              {idx < record.edges.length && (
                <span style={{ color: '#999', fontSize: '12px' }}>
                  {record.edges[idx].type}
                </span>
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
      sorter: (a, b) => a.length - b.length,
      render: (length: number) => (
        <Badge count={length} style={{ backgroundColor: '#52c41a' }} />
      )
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 120,
      sorter: (a, b) => (a.confidence || 0) - (b.confidence || 0),
      render: (confidence?: number) => (
        confidence !== undefined ? (
          <Progress
            percent={Math.round(confidence * 100)}
            size="small"
            status={confidence >= 0.7 ? 'success' : confidence >= 0.4 ? 'normal' : 'exception'}
          />
        ) : (
          <span style={{ color: '#999' }}>-</span>
        )
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: PathResult) => (
        <Button
          type="link"
          size="small"
          onClick={() => viewPath(record)}
        >
          View
        </Button>
      )
    }
  ];

  // Calculate statistics
  const getStatistics = () => {
    if (!queryResult) return null;

    const pathLengths = queryResult.paths.map(p => p.length);
    const avgLength = pathLengths.reduce((a, b) => a + b, 0) / pathLengths.length;
    const uniqueNodes = new Set(queryResult.paths.flatMap(p => p.nodes.map(n => n.id))).size;
    const uniqueEdges = new Set(queryResult.paths.flatMap(p => p.edges.map(e => e.id))).size;

    const domainCounts = queryResult.paths.flatMap(path =>
      path.nodes.map(node => getDomainForEntityType(node.type))
    ).reduce((acc, domain) => {
      acc[domain] = (acc[domain] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      totalPaths: queryResult.paths.length,
      filteredPaths: filteredPaths.length,
      avgLength: avgLength.toFixed(2),
      uniqueNodes,
      uniqueEdges,
      domainCounts
    };
  };

  const stats = getStatistics();

  // Get available path lengths for filtering
  const availablePathLengths = queryResult
    ? [...new Set(queryResult.paths.map(p => p.length))].sort((a, b) => a - b)
    : [];

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading query results...</p>
      </div>
    );
  }

  if (!queryResult) {
    return (
      <div style={{ padding: '24px' }}>
        <Empty
          description="No query results found"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" onClick={() => navigate('/cross-domain')}>
            Go to Query Builder
          </Button>
        </Empty>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card>
            <Row justify="space-between" align="middle">
              <Col>
                <Space>
                  <Button
                    icon={<ArrowLeftOutlined />}
                    onClick={() => navigate('/cross-domain')}
                  >
                    Back to Query Builder
                  </Button>
                  <Divider type="vertical" />
                  <div>
                    <h2 style={{ margin: 0 }}>Cross-Domain Query Results</h2>
                    <p style={{ margin: 0, color: '#666' }}>
                      {queryResult.queryConfig.startEntityType}
                      {queryResult.queryConfig.startEntityId && ` (${queryResult.queryConfig.startEntityId})`}
                      {' → '}
                      {queryResult.queryConfig.endEntityType}
                      {queryResult.queryConfig.endEntityId && ` (${queryResult.queryConfig.endEntityId})`}
                    </p>
                  </div>
                </Space>
              </Col>
              <Col>
                <Space>
                  <Button icon={<ReloadOutlined />} onClick={viewAllPaths}>
                    View All
                  </Button>
                  <Button icon={<ShareAltOutlined />} onClick={shareResults}>
                    Share
                  </Button>
                  <Button.Group>
                    <Button
                      icon={<FileTextOutlined />}
                      onClick={() => exportResults('csv')}
                    >
                      CSV
                    </Button>
                    <Button
                      icon={<DownloadOutlined />}
                      onClick={() => exportResults('json')}
                    >
                      JSON
                    </Button>
                    <Button
                      icon={<FileImageOutlined />}
                      onClick={() => exportResults('png')}
                    >
                      PNG
                    </Button>
                  </Button.Group>
                </Space>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Statistics */}
      {stats && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={12} sm={8} md={6}>
            <Card>
              <Statistic
                title="Total Paths"
                value={stats.totalPaths}
                suffix="paths"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card>
              <Statistic
                title="Filtered Results"
                value={stats.filteredPaths}
                suffix="paths"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card>
              <Statistic
                title="Unique Entities"
                value={stats.uniqueNodes}
                suffix="nodes"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card>
              <Statistic
                title="Avg Path Length"
                value={stats.avgLength}
                suffix="hops"
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Query Configuration */}
      <Card title="Query Configuration" style={{ marginTop: 16 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 4 }}>
          <Descriptions.Item label="Start Entity Type">
            <Tag color="blue">{queryResult.queryConfig.startEntityType}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="End Entity Type">
            <Tag color="blue">{queryResult.queryConfig.endEntityType}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Max Hops">
            <Tag>{queryResult.queryConfig.maxHops}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Relationship Types">
            {queryResult.queryConfig.relationshipTypes.length > 0 ? (
              queryResult.queryConfig.relationshipTypes.map(rt => (
                <Tag key={rt} style={{ margin: '2px' }}>{rt}</Tag>
              ))
            ) : (
              <Tag>All Types</Tag>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="Start Entity ID">
            {queryResult.queryConfig.startEntityId || (
              <span style={{ color: '#999' }}>All entities</span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="End Entity ID">
            {queryResult.queryConfig.endEntityId || (
              <span style={{ color: '#999' }}>All entities</span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="Executed At">
            {new Date(queryResult.timestamp).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Filters */}
      <Card title="Filters" style={{ marginTop: 16 }} size="small">
        <Space wrap>
          <span>Path Length:</span>
          <Select
            mode="multiple"
            placeholder="Select path lengths"
            style={{ width: 200 }}
            value={selectedPathLength}
            onChange={setSelectedPathLength}
            allowClear
          >
            {availablePathLengths.map(length => (
              <Option key={length} value={length}>
                {length} hop{length > 1 ? 's' : ''}
              </Option>
            ))}
          </Select>

          <Divider type="vertical" />

          <span>Domains:</span>
          <Select
            mode="multiple"
            placeholder="Select domains"
            style={{ width: 250 }}
            value={selectedDomains}
            onChange={setSelectedDomains}
            allowClear
          >
            {Object.entries(DOMAINS).map(([key, domain]) => (
              <Option key={key} value={key}>
                <Tag color={domain.color}>{domain.name}</Tag>
              </Option>
            ))}
          </Select>

          {filteredPaths.length !== queryResult.paths.length && (
            <Button
              size="small"
              onClick={() => {
                setSelectedPathLength([]);
                setSelectedDomains([]);
              }}
            >
              Clear Filters
            </Button>
          )}
        </Space>
      </Card>

      {/* Main Content */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* Graph Visualization */}
        <Col span={24}>
          <Card
            title="Graph Visualization"
            extra={
              <Space>
                <Button size="small" onClick={() => graphViewerRef.current?.fit()}>
                  Fit View
                </Button>
                <Button
                  size="small"
                  icon={<ZoomInOutlined />}
                  onClick={() => graphViewerRef.current?.zoom(1.2)}
                />
                <Button
                  size="small"
                  icon={<ZoomOutOutlined />}
                  onClick={() => graphViewerRef.current?.zoom(0.8)}
                />
              </Space>
            }
          >
            {graphData.nodes.length > 0 ? (
              <GraphViewer
                ref={graphViewerRef}
                data={graphData}
                height="500px"
              />
            ) : (
              <Empty description="No graph data to display" />
            )}
          </Card>
        </Col>

        {/* Path Details Table */}
        <Col span={24}>
          <Card title={`Path Details (${filteredPaths.length} paths)`}>
            <Table
              columns={pathColumns}
              dataSource={filteredPaths}
              rowKey={(record, idx) => idx?.toString() || '0'}
              pagination={{
                current: pathPagination.current,
                pageSize: pathPagination.pageSize,
                total: filteredPaths.length,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) =>
                  `${range[0]}-${range[1]} of ${total} paths`,
                onChange: (page, pageSize) => {
                  setPathPagination({ current: page, pageSize: pageSize || 10 });
                }
              }}
              scroll={{ x: 800 }}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default CrossDomainResultsPage;
