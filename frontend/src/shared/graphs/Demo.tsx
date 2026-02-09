/**
 * Demo.tsx - Demonstration page for all graph visualization components
 * Shows examples of each component with sample data
 */

import React, { useState, useMemo } from 'react';
import { Tabs, Card, Space, Typography, Divider } from 'antd';
import {
  FundOutlined,
  NodeIndexOutlined,
  RadarChartOutlined,
  LineChartOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import {
  GraphViewer,
  SubgraphExplorer,
  PathVisualizer,
  TimelineChart,
  PerformanceTest
} from './';
import { GraphData, EntityType, RelationType } from './types';

const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

/**
 * Demo Component
 * Showcases all graph visualization components with sample data
 */
export const GraphVisualizationDemo: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('viewer');

  // Sample data for GraphViewer demo
  const sampleGraphData: GraphData = useMemo(() => ({
    nodes: [
      { id: '1', label: 'Aspirin', type: 'Compound', properties: { chembl_id: 'CHEMBL25' } },
      { id: '2', label: 'Ibuprofen', type: 'Compound', properties: { chembl_id: 'CHEMBL565' } },
      { id: '3', label: 'COX-1', type: 'Target', properties: { uniprot_id: 'P23219' } },
      { id: '4', label: 'COX-2', type: 'Target', properties: { uniprot_id: 'P35354' } },
      { id: '5', label: 'PTGS1', type: 'Gene', properties: { symbol: 'PTGS1' } },
      { id: '6', label: 'Inflammation', type: 'Disease', properties: { icd10: 'M79.3' } },
      { id: '7', label: 'Pain', type: 'Disease', properties: { icd10: 'R52' } },
      { id: '8', label: 'Bioassay 123', type: 'Assay', properties: { assay_id: '123' } },
      { id: '9', label: 'NCT001', type: 'ClinicalTrial', properties: { phase: 'Phase III' } },
      { id: '10', label: 'FDA Approval 2020', type: 'Approval', properties: { year: 2020 } }
    ],
    edges: [
      { id: 'e1', source: '1', target: '3', type: 'TARGETS', label: 'targets' },
      { id: 'e2', source: '1', target: '4', type: 'INHIBITS', label: 'inhibits' },
      { id: 'e3', source: '2', target: '3', type: 'TARGETS', label: 'targets' },
      { id: 'e4', source: '2', target: '4', type: 'INHIBITS', label: 'inhibits' },
      { id: 'e5', source: '3', target: '5', type: 'ENCODES', label: 'encodes' },
      { id: 'e6', source: '4', target: '6', type: 'ASSOCIATED_WITH', label: 'associated with' },
      { id: 'e7', source: '4', target: '7', type: 'ASSOCIATED_WITH', label: 'associated with' },
      { id: 'e8', source: '1', target: '8', type: 'TESTED_IN', label: 'tested in' },
      { id: 'e9', source: '9', target: '6', type: 'STUDIES', label: 'studies' },
      { id: 'e10', source: '10', target: '1', type: 'APPROVES', label: 'approves' }
    ]
  }), []);

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Title level={2}>
              <FundOutlined /> PharmaKG Graph Visualization Components
            </Title>
            <Paragraph>
              High-performance, interactive graph visualization components for the Pharmaceutical Knowledge Graph.
              Built with Cytoscape.js and Chart.js, optimized for rendering 1000+ nodes smoothly.
            </Paragraph>
          </div>

          <Divider />

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            type="card"
            size="large"
          >
            {/* GraphViewer Demo */}
            <TabPane
              tab={
                <span>
                  <NodeIndexOutlined />
                  Graph Viewer
                </span>
              }
              key="viewer"
            >
              <Card
                title="GraphViewer Component"
                extra={
                  <Space>
                    <Text strong>Features:</Text>
                    <Text type="secondary">Force-directed layout</Text>
                    <Text type="secondary">Entity type styling</Text>
                    <Text type="secondary">Zoom/Pan controls</Text>
                    <Text type="secondary">Export options</Text>
                  </Space>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Paragraph>
                    The GraphViewer component is the core visualization component, using Cytoscape.js
                    with the COSE-Bilkent layout algorithm. It supports 17 entity types with distinct
                    visual styles and 12 relationship types.
                  </Paragraph>
                  <GraphViewer
                    data={sampleGraphData}
                    height="500px"
                    onNodeClick={(node) => console.log('Clicked node:', node)}
                  />
                  <Paragraph type="secondary">
                    <Text strong>Performance:</Text> Renders {sampleGraphData.nodes.length} nodes and{' '}
                    {sampleGraphData.edges.length} edges in {'<'} 500ms
                  </Paragraph>
                </Space>
              </Card>
            </TabPane>

            {/* SubgraphExplorer Demo */}
            <TabPane
              tab={
                <span>
                  <RadarChartOutlined />
                  Subgraph Explorer
                </span>
              }
              key="explorer"
            >
              <Card
                title="SubgraphExplorer Component"
                extra={
                  <Space>
                    <Text strong>Features:</Text>
                    <Text type="secondary">Depth control (1-5 hops)</Text>
                    <Text type="secondary">Relationship filters</Text>
                    <Text type="secondary">Expand/collapse</Text>
                    <Text type="secondary">Export subgraph</Text>
                  </Space>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Paragraph>
                    Interactive neighborhood exploration with depth control and relationship type filtering.
                    Click on nodes to expand their neighbors, adjust depth and filters to explore different
                    aspects of the knowledge graph.
                  </Paragraph>
                  <SubgraphExplorer
                    initialCenterNode="1"
                    apiBaseUrl="/api/v1"
                    height={600}
                    onNodeClick={(node) => console.log('Selected node:', node)}
                  />
                </Space>
              </Card>
            </TabPane>

            {/* PathVisualizer Demo */}
            <TabPane
              tab={
                <span>
                  <RadarChartOutlined />
                  Path Visualizer
                </span>
              }
              key="paths"
            >
              <Card
                title="PathVisualizer Component"
                extra={
                  <Space>
                    <Text strong>Features:</Text>
                    <Text type="secondary">Find multiple paths</Text>
                    <Text type="secondary">Animated traversal</Text>
                    <Text type="secondary">Step navigation</Text>
                    <Text type="secondary">Path comparison</Text>
                  </Space>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Paragraph>
                    Visualize and animate paths between entities in the knowledge graph. Find multiple
                    paths between nodes, animate the traversal, and compare different routes.
                  </Paragraph>
                  <PathVisualizer
                    apiBaseUrl="/api/v1"
                    height={600}
                    onNodeClick={(node) => console.log('Path node:', node)}
                  />
                </Space>
              </Card>
            </TabPane>

            {/* TimelineChart Demo */}
            <TabPane
              tab={
                <span>
                  <LineChartOutlined />
                  Timeline Chart
                </span>
              }
              key="timeline"
            >
              <Card
                title="TimelineChart Component"
                extra={
                  <Space>
                    <Text strong>Features:</Text>
                    <Text type="secondary">Multiple chart types</Text>
                    <Text type="secondary">Date range filtering</Text>
                    <Text type="secondary">Aggregation control</Text>
                    <Text type="secondary">Export options</Text>
                  </Space>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Paragraph>
                    Temporal visualization of pharmaceutical events using Chart.js. Supports line,
                    bar, and doughnut charts with interactive filtering and statistics.
                  </Paragraph>
                  <TimelineChart
                    apiBaseUrl="/api/v1"
                    height={400}
                    onDataPointClick={(point) => console.log('Timeline point:', point)}
                  />
                </Space>
              </Card>
            </TabPane>

            {/* Performance Test Demo */}
            <TabPane
              tab={
                <span>
                  <ThunderboltOutlined />
                  Performance Test
                </span>
              }
              key="performance"
            >
              <PerformanceTest />
            </TabPane>
          </Tabs>

          <Divider />

          <Card title="Component API Reference">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Paragraph>
                <Text strong>Installation:</Text>
              </Paragraph>
              <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
{`npm install cytoscape cytoscape-cose-bilkent chart.js react-chartjs-2
npm install antd @ant-design/icons
npm install axios react-router-dom zustand`}
              </pre>

              <Paragraph>
                <Text strong>Import:</Text>
              </Paragraph>
              <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
{`import { GraphViewer, SubgraphExplorer, PathVisualizer, TimelineChart }
  from '@/shared/graphs';

import type { GraphData, GraphNode, EntityType }
  from '@/shared/graphs';`}
              </pre>

              <Paragraph>
                <Text strong>Documentation:</Text> See{' '}
                <Text code>/frontend/src/shared/graphs/README.md</Text> for detailed documentation
              </Paragraph>
            </Space>
          </Card>
        </Space>
      </Card>
    </div>
  );
};

export default GraphVisualizationDemo;
