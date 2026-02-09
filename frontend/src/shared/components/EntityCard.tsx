import React, { useState } from 'react';
import { Card, Tag, Button, Space, Descriptions, Collapse, Tooltip, Typography } from 'antd';
import {
  ExpandOutlined,
  ShrinkOutlined,
  LinkOutlined,
  DownloadOutlined,
  ShareAltOutlined,
} from '@ant-design/icons';
import { EntityCardProps, EntityType } from '../types';
import {
  getDomainColor,
  getEntityDisplayName,
  getEntityIcon,
  formatNumber,
  formatDate,
  copyToClipboard,
} from '../utils/helpers';

const { Text } = Typography;
const { Panel } = Collapse;

const ENTITY_TYPE_LABELS: Record<EntityType, string> = {
  Compound: 'Compound',
  Target: 'Target',
  Assay: 'Assay',
  Pathway: 'Pathway',
  Trial: 'Clinical Trial',
  Subject: 'Subject',
  Intervention: 'Intervention',
  Outcome: 'Outcome',
  Manufacturer: 'Manufacturer',
  Facility: 'Facility',
  Document: 'Document',
  Agency: 'Agency',
  Submission: 'Submission',
};

const ENTITY_TYPE_COLORS: Record<EntityType, string> = {
  Compound: 'green',
  Target: 'blue',
  Assay: 'cyan',
  Pathway: 'purple',
  Trial: 'orange',
  Subject: 'geekblue',
  Intervention: 'magenta',
  Outcome: 'red',
  Manufacturer: 'gold',
  Facility: 'lime',
  Document: 'default',
  Agency: 'processing',
  Submission: 'volcano',
};

export const EntityCard: React.FC<EntityCardProps> = ({
  entityType,
  entityId,
  data,
  onExpand,
  onAction,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const domain = data.domain || 'rd';
  const domainColor = getDomainColor(domain);
  const displayName = getEntityDisplayName(data);
  const entityIcon = getEntityIcon(entityType);
  const typeLabel = ENTITY_TYPE_LABELS[entityType];
  const typeColor = ENTITY_TYPE_COLORS[entityType];

  const handleExpand = () => {
    setExpanded(!expanded);
    onExpand?.();
  };

  const handleAction = (action: string) => {
    onAction?.(action);
  };

  const handleCopyId = async () => {
    const success = await copyToClipboard(entityId);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleShare = () => {
    const url = `${window.location.origin}/entity/${entityType.toLowerCase()}/${entityId}`;
    copyToClipboard(url);
  };

  // Build property items for descriptions
  const propertyItems = Object.entries(data.properties || {}).reduce<
    { key: string; label: string; value: React.ReactNode }[]
  >((acc, [key, value]) => {
    if (value == null) return acc;

    let displayValue: React.ReactNode = value;

    // Format certain types
    if (typeof value === 'number') {
      displayValue = formatNumber(value);
    } else if (typeof value === 'string' && key.match(/date|time|updated/i)) {
      displayValue = formatDate(value);
    } else if (typeof value === 'boolean') {
      displayValue = value ? 'Yes' : 'No';
    } else if (Array.isArray(value)) {
      displayValue = value.slice(0, 3).join(', ') + (value.length > 3 ? ` (+${value.length - 3})` : '');
    } else if (typeof value === 'string' && value.length > 100) {
      displayValue = `${value.slice(0, 100)}...`;
    }

    acc.push({
      key,
      label: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      value: displayValue,
    });

    return acc;
  }, []);

  return (
    <Card
      className="entity-card"
      style={{
        borderColor: domainColor,
        borderRadius: 8,
        marginBottom: 16,
      }}
      headStyle={{
        backgroundColor: getDomainColor(domain, 'secondary'),
        borderBottomColor: domainColor,
      }}
      title={
        <Space>
          <span style={{ fontSize: 24 }}>{entityIcon}</span>
          <div>
            <Text strong style={{ fontSize: 16 }}>
              {displayName}
            </Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {typeLabel}
            </Text>
          </div>
        </Space>
      }
      extra={
        <Space>
          <Tooltip title={copied ? 'Copied!' : 'Copy ID'}>
            <Button
              type="text"
              icon={<LinkOutlined />}
              onClick={handleCopyId}
              style={{ color: copied ? '#52c41a' : undefined }}
            />
          </Tooltip>
          <Tooltip title="Share">
            <Button type="text" icon={<ShareAltOutlined />} onClick={handleShare} />
          </Tooltip>
          <Tooltip title="Download">
            <Button type="text" icon={<DownloadOutlined />} onClick={() => handleAction('download')} />
          </Tooltip>
          <Tooltip title={expanded ? 'Collapse' : 'Expand'}>
            <Button
              type="text"
              icon={expanded ? <ShrinkOutlined /> : <ExpandOutlined />}
              onClick={handleExpand}
            />
          </Tooltip>
        </Space>
      }
      bordered
    >
      {/* Quick Info */}
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <Space wrap>
          <Tag color={typeColor}>{typeLabel}</Tag>
          <Tag color={domainColor === '#4CAF50' ? 'green' : domainColor === '#2196F3' ? 'blue' : 'purple'}>
            {domain.toUpperCase()}
          </Tag>
          {data.properties?.status && <Tag color="processing">{String(data.properties.status)}</Tag>}
        </Space>

        {/* Expandable Details */}
        {expanded && propertyItems.length > 0 && (
          <Collapse ghost defaultActiveKey={['properties']}>
            <Panel header="Properties" key="properties">
              <Descriptions
                items={propertyItems.slice(0, 10)}
                column={1}
                size="small"
                bordered
                style={{ marginTop: 8 }}
              />
              {propertyItems.length > 10 && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  + {propertyItems.length - 10} more properties
                </Text>
              )}
            </Panel>
          </Collapse>
        )}

        {/* Quick Actions */}
        <Space style={{ marginTop: 12 }}>
          <Button size="small" onClick={() => handleAction('view-graph')}>
            View in Graph
          </Button>
          <Button size="small" onClick={() => handleAction('view-relationships')}>
            Relationships
          </Button>
          <Button size="small" onClick={() => handleAction('add-to-workspace')}>
            Add to Workspace
          </Button>
        </Space>
      </Space>
    </Card>
  );
};

export default EntityCard;
