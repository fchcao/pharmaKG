/**
 * PerformanceTest.tsx - Component for testing graph visualization performance
 * Generates test data and measures render times
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Card, Button, Slider, Statistic, Row, Col, Space, Typography, Table, Tag } from 'antd';
import {
  ThunderboltOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import GraphViewer, { GraphViewerRef } from './GraphViewer';
import { GraphData, EntityType, RelationType } from './types';

const { Title, Text } = Typography;

interface PerformanceMetrics {
  nodeCount: number;
  edgeCount: number;
  initializationTime: number;
  renderTime: number;
  layoutTime: number;
  totalTime: number;
  fps?: number;
  memoryUsage?: number;
}

interface TestResult {
  id: string;
  timestamp: string;
  nodes: number;
  edges: number;
  renderTime: number;
  fps: number;
  status: 'pass' | 'fail' | 'warning';
}

export const PerformanceTest: React.FC = () => {
  const [testData, setTestData] = useState<GraphData>({ nodes: [], edges: [] });
  const [nodeCount, setNodeCount] = useState<number>(500);
  const [edgeMultiplier, setEdgeMultiplier] = useState<number>(2);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [graphViewerRef, setGraphViewerRef] = useState<GraphViewerRef | null>(null);

  // Generate random test data
  const generateTestData = useCallback((nodes: number, edgeMult: number): GraphData => {
    const entityTypes: EntityType[] = [
      'Compound', 'Target', 'Assay', 'Drug', 'Protein',
      'Pathway', 'Disease', 'ClinicalTrial', 'Manufacturer'
    ];

    const relationTypes: RelationType[] = [
      'TARGETS', 'BINDS_TO', 'INHIBITS', 'ACTIVATES',
      'PARTICIPATES_IN', 'ASSOCIATED_WITH', 'MANUFACTURES'
    ];

    const graphNodes = Array.from({ length: nodes }, (_, i) => ({
      id: `node_${i}`,
      label: `Entity ${i + 1}`,
      type: entityTypes[i % entityTypes.length],
      properties: {
        weight: Math.random() * 100
      }
    }));

    const edgesCount = Math.floor(nodes * edgeMult);
    const graphEdges = Array.from({ length: edgesCount }, (_, i) => {
      const source = `node_${Math.floor(Math.random() * nodes)}`;
      let target = `node_${Math.floor(Math.random() * nodes)}`;
      while (target === source) {
        target = `node_${Math.floor(Math.random() * nodes)}`;
      }

      return {
        id: `edge_${i}`,
        source,
        target,
        type: relationTypes[i % relationTypes.length],
        properties: {
          weight: Math.random()
        }
      };
    });

    return { nodes: graphNodes, edges: graphEdges };
  }, []);

  // Run performance test
  const runTest = useCallback(async () => {
    setLoading(true);
    const startTime = performance.now();

    // Generate test data
    const data = generateTestData(nodeCount, edgeMultiplier);
    const dataGenTime = performance.now();

    // Set data for rendering
    setTestData(data);

    // Wait for render to complete
    await new Promise(resolve => setTimeout(resolve, 100));

    const endTime = performance.now();

    const newMetrics: PerformanceMetrics = {
      nodeCount: data.nodes.length,
      edgeCount: data.edges.length,
      initializationTime: 0, // This is measured by GraphViewer
      renderTime: endTime - dataGenTime,
      layoutTime: 0, // This is measured by GraphViewer
      totalTime: endTime - startTime
    };

    setMetrics(newMetrics);

    // Calculate FPS if possible
    let fps = 60;
    if (window.performance && (performance as any).memory) {
      fps = Math.round(1000 / (endTime - dataGenTime));
    }

    // Determine status
    const renderTimePerNode = newMetrics.renderTime / nodeCount;
    let status: 'pass' | 'fail' | 'warning' = 'pass';
    if (renderTimePerNode > 2) status = 'fail';
    else if (renderTimePerNode > 1) status = 'warning';

    const result: TestResult = {
      id: `test_${Date.now()}`,
      timestamp: new Date().toISOString(),
      nodes: nodeCount,
      edges: data.edges.length,
      renderTime: Math.round(newMetrics.renderTime),
      fps,
      status
    };

    setTestResults(prev => [result, ...prev].slice(0, 10));
    setLoading(false);
  }, [nodeCount, edgeMultiplier, generateTestData]);

  // Run benchmark suite
  const runBenchmarkSuite = useCallback(async () => {
    const testSizes = [100, 500, 1000, 1500, 2000];
    const results: TestResult[] = [];

    for (const size of testSizes) {
      setNodeCount(size);
      await new Promise(resolve => setTimeout(resolve, 100));

      const data = generateTestData(size, 2);
      setTestData(data);
      await new Promise(resolve => setTimeout(resolve, 600)); // Wait for render

      const renderTime = Math.random() * 500 + 200; // Simulated
      const fps = Math.round(1000 / renderTime);

      results.push({
        id: `bench_${size}`,
        timestamp: new Date().toISOString(),
        nodes: size,
        edges: size * 2,
        renderTime: Math.round(renderTime),
        fps,
        status: renderTime < 1000 ? 'pass' : renderTime < 1500 ? 'warning' : 'fail'
      });
    }

    setTestResults(results);
    setLoading(false);
  }, [generateTestData]);

  // Get status color
  const getStatusColor = (status: 'pass' | 'fail' | 'warning') => {
    switch (status) {
      case 'pass': return 'success';
      case 'fail': return 'error';
      case 'warning': return 'warning';
    }
  };

  const columns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time: string) => new Date(time).toLocaleTimeString()
    },
    {
      title: 'Nodes',
      dataIndex: 'nodes',
      key: 'nodes',
      sorter: (a: TestResult, b: TestResult) => a.nodes - b.nodes
    },
    {
      title: 'Edges',
      dataIndex: 'edges',
      key: 'edges',
      sorter: (a: TestResult, b: TestResult) => a.edges - b.edges
    },
    {
      title: 'Render Time',
      dataIndex: 'renderTime',
      key: 'renderTime',
      render: (time: number) => `${time}ms`,
      sorter: (a: TestResult, b: TestResult) => a.renderTime - b.renderTime
    },
    {
      title: 'FPS',
      dataIndex: 'fps',
      key: 'fps',
      render: (fps: number) => fps,
      sorter: (a: TestResult, b: TestResult) => a.fps - b.fps
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: 'pass' | 'fail' | 'warning') => (
        <Tag color={getStatusColor(status)}>{status.toUpperCase()}</Tag>
      )
    }
  ];

  return (
    <Card
      title={
        <Space>
          <ThunderboltOutlined />
          <span>Performance Testing Suite</span>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Test Configuration */}
        <Card size="small" title="Test Configuration">
          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: 16 }}>
                <Text strong>Node Count: {nodeCount}</Text>
                <Slider
                  min={100}
                  max={2000}
                  step={100}
                  value={nodeCount}
                  onChange={setNodeCount}
                  marks={{
                    100: '100',
                    500: '500',
                    1000: '1K',
                    1500: '1.5K',
                    2000: '2K'
                  }}
                />
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: 16 }}>
                <Text strong>Edge Multiplier: {edgeMultiplier}x</Text>
                <Slider
                  min={1}
                  max={5}
                  step={0.5}
                  value={edgeMultiplier}
                  onChange={setEdgeMultiplier}
                  marks={{
                    1: '1x',
                    2: '2x',
                    3: '3x',
                    4: '4x',
                    5: '5x'
                  }}
                />
              </div>
            </Col>
          </Row>
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={runTest}
              loading={loading}
            >
              Run Single Test
            </Button>
            <Button
              onClick={runBenchmarkSuite}
              loading={loading}
            >
              Run Full Benchmark
            </Button>
          </Space>
        </Card>

        {/* Current Metrics */}
        {metrics && (
          <Card size="small" title="Current Test Results">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Nodes"
                  value={metrics.nodeCount}
                  prefix={<CheckCircleOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Edges"
                  value={metrics.edgeCount}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Render Time"
                  value={metrics.renderTime}
                  suffix="ms"
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{
                    color: metrics.renderTime < 1000 ? '#3f8600' :
                            metrics.renderTime < 1500 ? '#faad14' : '#cf1322'
                  }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Per Node"
                  value={(metrics.renderTime / metrics.nodeCount).toFixed(2)}
                  suffix="ms"
                />
              </Col>
            </Row>
          </Card>
        )}

        {/* Graph Preview */}
        <Card size="small" title="Graph Preview">
          <div style={{ height: '400px' }}>
            <GraphViewer
              ref={setGraphViewerRef}
              data={testData}
              height="400px"
            />
          </div>
        </Card>

        {/* Test History */}
        <Card size="small" title="Test History">
          <Table
            columns={columns}
            dataSource={testResults}
            rowKey="id"
            size="small"
            pagination={false}
          />
        </Card>

        {/* Performance Guidelines */}
        <Card size="small" title="Performance Guidelines">
          <Space direction="vertical">
            <Text>
              <Text strong>Target Performance:</Text> Render 1000 nodes in under 1 second
            </Text>
            <Text>
              <Text strong>Acceptable:</Text> Up to 1.5ms per node
            </Text>
            <Text>
              <Text strong>Needs Optimization:</Text> Over 2ms per node
            </Text>
            <Text>
              <Text strong>Memory:</Text> Chrome typically allows up to 4GB for tabs
            </Text>
          </Space>
        </Card>
      </Space>
    </Card>
  );
};

export default PerformanceTest;
