/**
 * SubgraphExplorer.tsx - Explore neighborhoods around selected nodes
 * Supports depth control and relationship type filtering
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Slider, Select, Button, Space, Card, Badge, Spin, message } from 'antd';
import {
  ExpandOutlined,
  CompressOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FilterOutlined
} from '@ant-design/icons';
import GraphViewer, { GraphViewerRef } from './GraphViewer';
import {
  GraphData,
  GraphNode,
  SubgraphQuery,
  RelationType,
  EntityType
} from './types';
import axios from 'axios';

const { Option } = Select;

interface SubgraphExplorerProps {
  initialCenterNode?: string;
  apiBaseUrl?: string;
  height?: string | number;
  onNodeClick?: (node: GraphNode) => void;
  onExport?: (data: GraphData) => void;
}

const RELATION_TYPE_OPTIONS: { value: RelationType; label: string }[] = [
  { value: 'TARGETS', label: 'Targets' },
  { value: 'BINDS_TO', label: 'Binds To' },
  { value: 'INHIBITS', label: 'Inhibits' },
  { value: 'ACTIVATES', label: 'Activates' },
  { value: 'PARTICIPATES_IN', label: 'Participates In' },
  { value: 'ASSOCIATED_WITH', label: 'Associated With' },
  { value: 'MANUFACTURES', label: 'Manufactures' },
  { value: 'SUPPLIES', label: 'Supplies' },
  { value: 'SUBMITTED_TO', label: 'Submitted To' },
  { value: 'APPROVED_BY', label: 'Approved By' },
  { value: 'CONDUCTS_AT', label: 'Conducts At' },
  { value: 'REFERENCES', label: 'References' }
];

const ENTITY_TYPE_OPTIONS: { value: EntityType; label: string }[] = [
  { value: 'Compound', label: 'Compounds' },
  { value: 'Target', label: 'Targets' },
  { value: 'Drug', label: 'Drugs' },
  { value: 'ClinicalTrial', label: 'Clinical Trials' },
  { value: 'Manufacturer', label: 'Manufacturers' },
  { value: 'Pathway', label: 'Pathways' },
  { value: 'Disease', label: 'Diseases' },
  { value: 'Submission', label: 'Submissions' },
  { value: 'Approval', label: 'Approvals' }
];

export const SubgraphExplorer: React.FC<SubgraphExplorerProps> = ({
  initialCenterNode,
  apiBaseUrl = '/api/v1',
  height = 700,
  onNodeClick,
  onExport
}) => {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [centerNodeId, setCenterNodeId] = useState<string | undefined>(initialCenterNode);
  const [depth, setDepth] = useState<number>(2);
  const [selectedRelationTypes, setSelectedRelationTypes] = useState<RelationType[]>([]);
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<EntityType[]>([]);
  const [nodeLimit, setNodeLimit] = useState<number>(500);
  const [loading, setLoading] = useState<boolean>(false);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [graphViewerRef, setGraphViewerRef] = useState<GraphViewerRef | null>(null);

  // Fetch subgraph from API
  const fetchSubgraph = useCallback(async (centerId: string, queryDepth: number) => {
    setLoading(true);
    const startTime = performance.now();

    try {
      const params: any = {
        depth: queryDepth,
        limit: nodeLimit
      };

      if (selectedRelationTypes.length > 0) {
        params.relation_types = selectedRelationTypes.join(',');
      }

      if (selectedEntityTypes.length > 0) {
        params.entity_types = selectedEntityTypes.join(',');
      }

      const response = await axios.get(
        `${apiBaseUrl}/advanced/subgraph/${centerId}`,
        { params }
      );

      const endTime = performance.now();
      console.log(`Subgraph fetch time: ${(endTime - startTime).toFixed(2)}ms`);

      if (response.data && response.data.nodes) {
        const data: GraphData = {
          nodes: response.data.nodes || [],
          edges: response.data.edges || []
        };

        setGraphData(data);
        message.success(`Loaded ${data.nodes.length} nodes and ${data.edges.length} edges`);
      } else {
        message.warning('No data returned for this query');
      }
    } catch (error: any) {
      console.error('Error fetching subgraph:', error);
      message.error(`Failed to fetch subgraph: ${error.response?.data?.message || error.message}`);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, depth, selectedRelationTypes, selectedEntityTypes, nodeLimit]);

  // Expand neighbors of selected node
  const expandNeighbors = useCallback(async (nodeId: string) => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${apiBaseUrl}/advanced/neighbors/${nodeId}`,
        {
          params: {
            depth: 1,
            limit: 50
          }
        }
      );

      if (response.data && response.data.nodes) {
        const newNodes = response.data.nodes.filter(
          (n: GraphNode) => !graphData.nodes.find(existing => existing.id === n.id)
        );
        const newEdges = response.data.edges.filter(
          (e: any) => !graphData.edges.find(existing => existing.id === e.id)
        );

        setGraphData(prev => ({
          nodes: [...prev.nodes, ...newNodes],
          edges: [...prev.edges, ...newEdges]
        }));

        setExpandedNodes(prev => new Set([...prev, nodeId]));

        message.success(`Expanded ${newNodes.length} nodes`);
      }
    } catch (error: any) {
      console.error('Error expanding neighbors:', error);
      message.error('Failed to expand neighbors');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, graphData]);

  // Collapse neighbors (remove nodes added by expansion)
  const collapseNeighbors = useCallback((nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      newSet.delete(nodeId);
      return newSet;
    });

    // Re-fetch original subgraph without expanded nodes
    if (centerNodeId) {
      fetchSubgraph(centerNodeId, depth);
    }
  }, [centerNodeId, depth, fetchSubgraph]);

  // Handle node click
  const handleNodeClick = useCallback((node: GraphNode) => {
    if (onNodeClick) {
      onNodeClick(node);
    }

    // Auto-expand on click if not already expanded
    if (!expandedNodes.has(node.id) && depth < 5) {
      expandNeighbors(node.id);
    }
  }, [onNodeClick, expandedNodes, depth, expandNeighbors]);

  // Handle initial load
  useEffect(() => {
    if (initialCenterNode) {
      fetchSubgraph(initialCenterNode, depth);
    }
  }, [initialCenterNode]);

  // Export subgraph data
  const handleExport = useCallback(() => {
    if (onExport) {
      onExport(graphData);
    } else {
      // Default export as JSON
      const dataStr = JSON.stringify(graphData, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `subgraph_${centerNodeId || 'export'}_${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
      message.success('Subgraph exported successfully');
    }
  }, [graphData, centerNodeId, onExport]);

  // Reset view
  const handleReset = useCallback(() => {
    if (centerNodeId) {
      fetchSubgraph(centerNodeId, depth);
    } else {
      setGraphData({ nodes: [], edges: [] });
    }
    setExpandedNodes(new Set());
  }, [centerNodeId, depth, fetchSubgraph]);

  const stats = {
    nodes: graphData.nodes.length,
    edges: graphData.edges.length,
    expanded: expandedNodes.size
  };

  return (
    <Card
      title="Subgraph Explorer"
      extra={
        <Space>
          <Badge count={stats.nodes} showZero title="Total Nodes">
            <span style={{ marginRight: 8 }}>Nodes</span>
          </Badge>
          <Badge count={stats.edges} showZero title="Total Edges">
            <span style={{ marginRight: 8 }}>Edges</span>
          </Badge>
          <Badge count={stats.expanded} showZero title="Expanded Nodes">
            <span>Expanded</span>
          </Badge>
        </Space>
      }
      style={{ height: 'auto' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* Controls */}
        <Card size="small" title={<><FilterOutlined /> Exploration Controls</>}>
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            {/* Depth Control */}
            <div>
              <div style={{ marginBottom: 8 }}>
                <strong>Depth: {depth} hops</strong>
              </div>
              <Slider
                min={1}
                max={5}
                value={depth}
                onChange={setDepth}
                marks={{ 1: '1', 2: '2', 3: '3', 4: '4', 5: '5' }}
              />
            </div>

            {/* Node Limit */}
            <div>
              <div style={{ marginBottom: 8 }}>
                <strong>Max Nodes: {nodeLimit}</strong>
              </div>
              <Slider
                min={100}
                max={2000}
                step={100}
                value={nodeLimit}
                onChange={setNodeLimit}
                marks={{
                  100: '100',
                  500: '500',
                  1000: '1K',
                  1500: '1.5K',
                  2000: '2K'
                }}
              />
            </div>

            {/* Relationship Type Filter */}
            <div>
              <div style={{ marginBottom: 8 }}>
                <strong>Relationship Types:</strong>
              </div>
              <Select
                mode="multiple"
                style={{ width: '100%' }}
                placeholder="Filter by relationship type (optional)"
                value={selectedRelationTypes}
                onChange={setSelectedRelationTypes}
                options={RELATION_TYPE_OPTIONS}
                maxTagCount={3}
                allowClear
              />
            </div>

            {/* Entity Type Filter */}
            <div>
              <div style={{ marginBottom: 8 }}>
                <strong>Entity Types:</strong>
              </div>
              <Select
                mode="multiple"
                style={{ width: '100%' }}
                placeholder="Filter by entity type (optional)"
                value={selectedEntityTypes}
                onChange={setSelectedEntityTypes}
                options={ENTITY_TYPE_OPTIONS}
                maxTagCount={3}
                allowClear
              />
            </div>

            {/* Action Buttons */}
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Space>
                <Button
                  type="primary"
                  icon={<ExpandOutlined />}
                  onClick={() => centerNodeId && fetchSubgraph(centerNodeId, depth)}
                  disabled={!centerNodeId}
                >
                  Fetch
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleReset}
                >
                  Reset
                </Button>
              </Space>
              <Button
                icon={<DownloadOutlined />}
                onClick={handleExport}
                disabled={graphData.nodes.length === 0}
              >
                Export
              </Button>
            </Space>
          </Space>
        </Card>

        {/* Graph Visualization */}
        <Spin spinning={loading} tip="Loading subgraph...">
          <div style={{ position: 'relative' }}>
            {graphData.nodes.length === 0 && !loading && (
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center',
                  color: '#999'
                }}
              >
                <p>Enter a node ID or click on a node to explore its neighborhood</p>
                <p style={{ fontSize: 12, color: '#bbb' }}>
                  Adjust depth and filters, then click "Fetch" to load data
                </p>
              </div>
            )}
            <GraphViewer
              ref={setGraphViewerRef}
              data={graphData}
              onNodeClick={handleNodeClick}
              height={height}
            />
          </div>
        </Spin>
      </Space>
    </Card>
  );
};

export default SubgraphExplorer;
