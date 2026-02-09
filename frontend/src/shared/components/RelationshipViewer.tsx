import React, { useState } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Tooltip,
  Select,
  Empty,
  Spin,
} from 'antd';
import {
  UnorderedListOutlined,
  NodeIndexOutlined,
  FilterOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { RelationshipViewerProps, Relationship, RelationshipType } from '../types';
import { useRelationships } from '../api/hooks';
import { formatDate, exportAsCSV, formatNumber } from '../utils/helpers';

const { Text } = Typography;
const { TabPane } = Tabs;

const RELATIONSHIP_LABELS: Record<RelationshipType, string> = {
  TARGETS: 'Targets',
  ASSAYS: 'Assays',
  IN_PATHWAY: 'In Pathway',
  REGULATED_BY: 'Regulated By',
  MANUFACTURES: 'Manufactures',
  SUPPLIES: 'Supplies',
  TESTED_IN: 'Tested In',
  RELATED_TO: 'Related To',
};

const RELATIONSHIP_COLORS: Record<RelationshipType, string> = {
  TARGETS: 'green',
  ASSAYS: 'blue',
  IN_PATHWAY: 'purple',
  REGULATED_BY: 'orange',
  MANUFACTURES: 'cyan',
  SUPPLIES: 'lime',
  TESTED_IN: 'magenta',
  RELATED_TO: 'default',
};

export const RelationshipViewer: React.FC<RelationshipViewerProps> = ({
  entityId,
  entityType,
  viewMode = 'list',
  relationshipTypes,
}) => {
  const [activeView, setActiveView] = useState<'list' | 'graph'>(viewMode);
  const [selectedTypes, setSelectedTypes] = useState<RelationshipType[]>(relationshipTypes || []);
  const [pageSize, setPageSize] = useState(10);

  const { data: relationships, isLoading, error } = useRelationships(entityId, selectedTypes);

  // Filter relationships by type if selected
  const filteredRelationships =
    selectedTypes.length > 0
      ? relationships?.filter((r) => selectedTypes.includes(r.type)) || []
      : relationships || [];

  // Get all unique relationship types
  const availableTypes = Array.from(
    new Set(relationships?.map((r) => r.type) || [])
  ) as RelationshipType[];

  // Build table columns
  const columns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 150,
      render: (type: RelationshipType) => (
        <Tag color={RELATIONSHIP_COLORS[type]}>{RELATIONSHIP_LABELS[type] || type}</Tag>
      ),
      sorter: (a: Relationship, b: Relationship) => a.type.localeCompare(b.type),
    },
    {
      title: 'Target',
      dataIndex: 'target',
      key: 'target',
      render: (target: string) => (
        <Tooltip title={target}>
          <Text ellipsis style={{ maxWidth: 200 }}>
            {target}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: 'Properties',
      dataIndex: 'properties',
      key: 'properties',
      render: (props: Record<string, unknown> | undefined) => {
        if (!props) return '-';
        const entries = Object.entries(props).slice(0, 2);
        return (
          <Space direction="vertical" size="small">
            {entries.map(([key, value]) => (
              <Text key={key} type="secondary" style={{ fontSize: 12 }}>
                {key}: {typeof value === 'number' ? formatNumber(Number(value)) : String(value).slice(0, 30)}
              </Text>
            ))}
          </Space>
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: unknown, record: Relationship) => (
        <Button type="link" size="small" onClick={() => handleNavigateToEntity(record.target)}>
          View
        </Button>
      ),
    },
  ];

  const handleNavigateToEntity = (targetId: string) => {
    // Navigate to entity detail page
    window.location.href = `/entity/${targetId}`;
  };

  const handleExport = () => {
    const exportData = filteredRelationships.map((r) => ({
      type: r.type,
      source: r.source,
      target: r.target,
      ...r.properties,
    }));
    exportAsCSV(exportData, `relationships-${entityId}`);
  };

  const handleTypeFilterChange = (types: RelationshipType[]) => {
    setSelectedTypes(types);
  };

  if (isLoading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>
            Loading relationships...
          </Text>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Empty
          description={`Failed to load relationships: ${error.message || 'Unknown error'}`}
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  if (!filteredRelationships || filteredRelationships.length === 0) {
    return (
      <Card>
        <Empty description="No relationships found" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    );
  }

  return (
    <Card
      className="relationship-viewer"
      title={
        <Space>
          <Text strong>Relationships</Text>
          <Tag color="blue">{filteredRelationships.length}</Tag>
        </Space>
      }
      extra={
        <Space>
          <Select
            mode="multiple"
            placeholder="Filter by type"
            style={{ width: 200 }}
            value={selectedTypes}
            onChange={handleTypeFilterChange}
            allowClear
          >
            {availableTypes.map((type) => (
              <Select.Option key={type} value={type}>
                {RELATIONSHIP_LABELS[type] || type}
              </Select.Option>
            ))}
          </Select>
          <Button
            type="primary"
            icon={<ExportOutlined />}
            onClick={handleExport}
            disabled={filteredRelationships.length === 0}
          >
            Export
          </Button>
        </Space>
      }
    >
      <Tabs
        activeKey={activeView}
        onChange={(key) => setActiveView(key as 'list' | 'graph')}
        tabBarExtraContent={
          <Text type="secondary" style={{ fontSize: 12 }}>
            Showing {filteredRelationships.length} relationships
          </Text>
        }
      >
        <TabPane
          tab={
            <span>
              <UnorderedListOutlined />
              List View
            </span>
          }
          key="list"
        >
          <Table
            columns={columns}
            dataSource={filteredRelationships}
            rowKey="id"
            pagination={{
              pageSize,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} relationships`,
              onShowSizeChange: (_, size) => setPageSize(size),
            }}
            size="small"
          />
        </TabPane>

        <TabPane
          tab={
            <span>
              <NodeIndexOutlined />
              Compact Graph
            </span>
          }
          key="graph"
        >
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Text type="secondary">
              Compact graph visualization will be implemented in the graph visualization component.
            </Text>
            <br />
            <Button type="link" onClick={() => handleNavigateToEntity(entityId)}>
              Open in Graph Viewer
            </Button>
          </div>
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default RelationshipViewer;
