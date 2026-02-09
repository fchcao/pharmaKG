/**
 * PathVisualizer.tsx - Visualize paths between entities
 * Supports animated path traversal and alternative path highlighting
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { Card, Space, Button, Select, Steps, Tag, Statistic, Row, Col, message, Spin } from 'antd';
import {
  PlayCircleOutlined,
  StepForwardOutlined,
  StepBackwardOutlined,
  ReloadOutlined,
  RightOutlined,
  SwapRightOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import GraphViewer, { GraphViewerRef } from './GraphViewer';
import {
  GraphData,
  GraphNode,
  GraphEdge,
  PathResult
} from './types';
import axios from 'axios';

const { Option } = Select;
const { Step } = Steps;

interface PathVisualizerProps {
  apiBaseUrl?: string;
  height?: string | number;
  onNodeClick?: (node: GraphNode) => void;
  onExport?: (path: PathResult) => void;
}

interface PathStep {
  node: GraphNode;
  edge?: GraphEdge;
  index: number;
}

export const PathVisualizer: React.FC<PathVisualizerProps> = ({
  apiBaseUrl = '/api/v1',
  height = 600,
  onNodeClick,
  onExport
}) => {
  const [sourceId, setSourceId] = useState<string>('');
  const [targetId, setTargetId] = useState<string>('');
  const [pathResults, setPathResults] = useState<PathResult[]>([]);
  const [selectedPathIndex, setSelectedPathIndex] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [graphViewerRef, setGraphViewerRef] = useState<GraphViewerRef | null>(null);
  const [animationSpeed, setAnimationSpeed] = useState<number>(1000);
  const [maxPaths, setMaxPaths] = useState<number>(5);

  // Convert path to graph data for visualization
  const pathToGraphData = useCallback((path: PathResult, highlightStep?: number): GraphData => {
    const allNodes = path.nodes;
    const allEdges = path.edges;

    // If we have a current step, highlight path up to that point
    if (highlightStep !== undefined && highlightStep < path.path.length) {
      const nodesUpToStep = path.nodes.slice(0, highlightStep + 1);
      const edgesUpToStep = path.edges.slice(0, highlightStep);

      return {
        nodes: allNodes.map(node => ({
          ...node,
          properties: {
            ...node.properties,
            active: nodesUpToStep.some(n => n.id === node.id)
          }
        })),
        edges: allEdges.map(edge => ({
          ...edge,
          properties: {
            ...edge.properties,
            active: edgesUpToStep.some(e => e.id === edge.id)
          }
        }))
      };
    }

    return {
      nodes: allNodes,
      edges: allEdges
    };
  }, []);

  // Get current path steps
  const currentPathSteps = useMemo((): PathStep[] => {
    if (pathResults.length === 0) return [];

    const path = pathResults[selectedPathIndex];
    const steps: PathStep[] = [];

    path.path.forEach((nodeId, index) => {
      const node = path.nodes.find(n => n.id === nodeId);
      if (node) {
        const edge = index > 0 ? path.edges[index - 1] : undefined;
        steps.push({ node, edge, index });
      }
    });

    return steps;
  }, [pathResults, selectedPathIndex]);

  // Find paths between nodes
  const findPaths = useCallback(async () => {
    if (!sourceId || !targetId) {
      message.warning('Please enter both source and target node IDs');
      return;
    }

    setLoading(true);
    const startTime = performance.now();

    try {
      const response = await axios.get(
        `${apiBaseUrl}/advanced/paths`,
        {
          params: {
            source: sourceId,
            target: targetId,
            max_paths: maxPaths,
            max_length: 6
          }
        }
      );

      const endTime = performance.now();
      console.log(`Path finding time: ${(endTime - startTime).toFixed(2)}ms`);

      if (response.data && response.data.paths && response.data.paths.length > 0) {
        setPathResults(response.data.paths);
        setSelectedPathIndex(0);
        setCurrentStep(0);
        message.success(`Found ${response.data.paths.length} path(s)`);
      } else {
        message.warning('No paths found between these nodes');
        setPathResults([]);
      }
    } catch (error: any) {
      console.error('Error finding paths:', error);
      message.error(`Failed to find paths: ${error.response?.data?.message || error.message}`);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, sourceId, targetId, maxPaths]);

  // Animation control
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (isPlaying && currentStep < currentPathSteps.length - 1) {
      intervalId = setInterval(() => {
        setCurrentStep(prev => {
          const next = prev + 1;
          if (next >= currentPathSteps.length - 1) {
            setIsPlaying(false);
          }
          return next;
        });
      }, animationSpeed);
    } else if (isPlaying) {
      setIsPlaying(false);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isPlaying, currentStep, currentPathSteps.length, animationSpeed]);

  // Handle step navigation
  const goToStep = useCallback((step: number) => {
    setCurrentStep(Math.max(0, Math.min(step, currentPathSteps.length - 1)));
  }, [currentPathSteps.length]);

  const nextStep = useCallback(() => {
    goToStep(currentStep + 1);
  }, [currentStep, goToStep]);

  const prevStep = useCallback(() => {
    goToStep(currentStep - 1);
  }, [currentStep, goToStep]);

  // Export current path
  const handleExport = useCallback(() => {
    if (pathResults.length === 0) return;

    const currentPath = pathResults[selectedPathIndex];
    if (onExport) {
      onExport(currentPath);
    } else {
      const dataStr = JSON.stringify(currentPath, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `path_${sourceId}_to_${targetId}.json`;
      link.click();
      URL.revokeObjectURL(url);
      message.success('Path exported successfully');
    }
  }, [pathResults, selectedPathIndex, sourceId, targetId, onExport]);

  // Handle node click from graph
  const handleNodeClick = useCallback((node: GraphNode) => {
    if (onNodeClick) {
      onNodeClick(node);
    }

    // If clicking a node in current path, jump to that step
    const stepIndex = currentPathSteps.findIndex(s => s.node.id === node.id);
    if (stepIndex >= 0) {
      setCurrentStep(stepIndex);
    }
  }, [onNodeClick, currentPathSteps]);

  // Current graph data based on animation step
  const currentGraphData = useMemo(() => {
    if (pathResults.length === 0) return { nodes: [], edges: [] };
    return pathToGraphData(pathResults[selectedPathIndex], currentStep);
  }, [pathResults, selectedPathIndex, currentStep, pathToGraphData]);

  const currentPath = pathResults[selectedPathIndex];
  const currentStepData = currentPathSteps[currentStep];

  return (
    <Card
      title="Path Visualizer"
      extra={
        <Space>
          <Tag color="blue">{pathResults.length} Paths Found</Tag>
          {currentPath && (
            <Tag color="green">Length: {currentPath.length}</Tag>
          )}
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* Search Controls */}
        <Card size="small" title="Find Paths">
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            <Row gutter={16}>
              <Col span={10}>
                <div style={{ marginBottom: 8 }}>
                  <strong>Source Node ID:</strong>
                </div>
                <Select
                  showSearch
                  style={{ width: '100%' }}
                  placeholder="Enter or search source ID"
                  value={sourceId || undefined}
                  onChange={setSourceId}
                  notFoundContent={null}
                  filterOption={false}
                  allowClear
                >
                  {/* Options would be populated by API search */}
                </Select>
              </Col>
              <Col span={4}>
                <div style={{ textAlign: 'center', marginTop: 30 }}>
                  <SwapRightOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                </div>
              </Col>
              <Col span={10}>
                <div style={{ marginBottom: 8 }}>
                  <strong>Target Node ID:</strong>
                </div>
                <Select
                  showSearch
                  style={{ width: '100%' }}
                  placeholder="Enter or search target ID"
                  value={targetId || undefined}
                  onChange={setTargetId}
                  notFoundContent={null}
                  filterOption={false}
                  allowClear
                >
                  {/* Options would be populated by API search */}
                </Select>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <div style={{ marginBottom: 8 }}>
                  <strong>Max Paths:</strong>
                </div>
                <Select
                  style={{ width: '100%' }}
                  value={maxPaths}
                  onChange={setMaxPaths}
                >
                  <Option value={1}>1</Option>
                  <Option value={3}>3</Option>
                  <Option value={5}>5</Option>
                  <Option value={10}>10</Option>
                </Select>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: 8 }}>
                  <strong>Animation Speed:</strong>
                </div>
                <Select
                  style={{ width: '100%' }}
                  value={animationSpeed}
                  onChange={setAnimationSpeed}
                >
                  <Option value={2000}>Slow (2s)</Option>
                  <Option value={1000}>Normal (1s)</Option>
                  <Option value={500}>Fast (0.5s)</Option>
                </Select>
              </Col>
            </Row>

            <Button
              type="primary"
              block
              icon={<RightOutlined />}
              onClick={findPaths}
              loading={loading}
              disabled={!sourceId || !targetId}
            >
              Find Paths
            </Button>
          </Space>
        </Card>

        {/* Path Selection & Navigation */}
        {pathResults.length > 0 && (
          <>
            {/* Path Selector */}
            <Card size="small">
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                <div style={{ marginBottom: 8 }}>
                  <strong>Select Path:</strong>
                </div>
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Select
                    style={{ width: 'calc(100% - 140px)' }}
                    value={selectedPathIndex}
                    onChange={setSelectedPathIndex}
                  >
                    {pathResults.map((path, index) => (
                      <Option key={index} value={index}>
                        Path {index + 1}: {path.length} steps - {path.path.join(' → ')}
                      </Option>
                    ))}
                  </Select>
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={handleExport}
                  >
                    Export
                  </Button>
                </Space>
              </Space>
            </Card>

            {/* Step Navigation */}
            <Card size="small">
              <Row gutter={16} align="middle">
                <Col span={18}>
                  <Steps
                    current={currentStep}
                    size="small"
                    onChange={goToStep}
                  >
                    {currentPathSteps.map((step, index) => (
                      <Step
                        key={index}
                        title={step.node.type}
                        description={step.node.label.slice(0, 15)}
                        icon={<RightOutlined />}
                      />
                    ))}
                  </Steps>
                </Col>
                <Col span={6}>
                  <Space>
                    <Button
                      icon={<StepBackwardOutlined />}
                      onClick={prevStep}
                      disabled={currentStep === 0 || isPlaying}
                    />
                    <Button
                      type={isPlaying ? 'default' : 'primary'}
                      icon={<PlayCircleOutlined />}
                      onClick={() => setIsPlaying(!isPlaying)}
                      disabled={currentStep >= currentPathSteps.length - 1}
                    >
                      {isPlaying ? 'Pause' : 'Play'}
                    </Button>
                    <Button
                      icon={<StepForwardOutlined />}
                      onClick={nextStep}
                      disabled={currentStep >= currentPathSteps.length - 1 || isPlaying}
                    />
                  </Space>
                </Col>
              </Row>
            </Card>

            {/* Current Step Details */}
            {currentStepData && (
              <Card size="small" title={`Step ${currentStep + 1} of ${currentPathSteps.length}`}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="Current Node"
                      value={currentStepData.node.label}
                      prefix={<Tag color="blue">{currentStepData.node.type}</Tag>}
                    />
                    {currentStepData.node.properties && Object.keys(currentStepData.node.properties).length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        {Object.entries(currentStepData.node.properties).slice(0, 3).map(([key, value]) => (
                          <Tag key={key} color="default">
                            {key}: {String(value).slice(0, 20)}
                          </Tag>
                        ))}
                      </div>
                    )}
                  </Col>
                  <Col span={12}>
                    {currentStepData.edge && (
                      <>
                        <Statistic
                          title="Relationship"
                          value={currentStepData.edge.type}
                          prefix={<Tag color="orange">{currentStepData.edge.label || 'Edge'}</Tag>}
                        />
                        {currentStepData.edge.properties && Object.keys(currentStepData.edge.properties).length > 0 && (
                          <div style={{ marginTop: 8 }}>
                            {Object.entries(currentStepData.edge.properties).slice(0, 2).map(([key, value]) => (
                              <Tag key={key} color="default">
                                {key}: {String(value).slice(0, 20)}
                              </Tag>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </Col>
                </Row>
              </Card>
            )}

            {/* Graph Visualization */}
            <Spin spinning={loading}>
              <GraphViewer
                ref={setGraphViewerRef}
                data={currentGraphData}
                onNodeClick={handleNodeClick}
                height={height}
              />
            </Spin>
          </>
        )}
      </Space>
    </Card>
  );
};

export default PathVisualizer;
