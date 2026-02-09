import React from 'react';
import { Card, Statistic, Row, Col, Progress, Typography, Space } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import { DOMAIN_COLORS } from '../types';

const { Text } = Typography;

// Domain Statistics Card
export interface DomainStatsCardProps {
  title: string;
  value: number;
  suffix?: string;
  icon: React.ReactNode;
  color: string;
  onClick?: () => void;
  breakdown?: { label: string; value: number }[];
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export const DomainStatsCard: React.FC<DomainStatsCardProps> = ({
  title,
  value,
  suffix = 'entities',
  icon,
  color,
  onClick,
  breakdown,
  trend,
}) => {
  return (
    <Card
      hoverable={!!onClick}
      onClick={onClick}
      style={{ borderTop: `4px solid ${color}` }}
    >
      <Statistic
        title={
          <Space>
            {icon}
            <span>{title}</span>
          </Space>
        }
        value={value}
        suffix={suffix}
        valueStyle={{ color }}
        prefix={trend && (
          trend.isPositive ? (
            <ArrowUpOutlined style={{ fontSize: 14 }} />
          ) : (
            <ArrowDownOutlined style={{ fontSize: 14 }} />
          )
        )}
      />
      {breakdown && (
        <div style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }} size={4}>
            {breakdown.map((item) => (
              <div
                key={item.label}
                style={{ display: 'flex', justifyContent: 'space-between' }}
              >
                <Text type="secondary">{item.label}</Text>
                <Text strong>{item.value.toLocaleString()}</Text>
              </div>
            ))}
          </Space>
        </div>
      )}
      {trend && (
        <div style={{ marginTop: 8 }}>
          <Text
            type={trend.isPositive ? 'success' : 'danger'}
            style={{ fontSize: '12px' }}
          >
            {trend.isPositive ? '+' : ''}
            {trend.value}% from last period
          </Text>
        </div>
      )}
    </Card>
  );
};

// Data Quality Progress Card
export interface DataQualityCardProps {
  title: string;
  score: number;
  color?: string;
  size?: number;
  showPercentage?: boolean;
}

export const DataQualityCard: React.FC<DataQualityCardProps> = ({
  title,
  score,
  color,
  size = 120,
  showPercentage = true,
}) => {
  return (
    <div style={{ textAlign: 'center' }}>
      <Progress
        type="circle"
        percent={score}
        strokeColor={color || {
          '0%': '#108ee9',
          '100%': '#87d068',
        }}
        size={size}
        format={(percent) => (showPercentage ? `${percent}%` : '')}
      />
      <div style={{ marginTop: 8 }}>
        <Text strong>{title}</Text>
      </div>
    </div>
  );
};

// Quick Action Card
export interface QuickActionCardProps {
  title: string;
  icon: React.ReactNode;
  backgroundColor?: string;
  onClick: () => void;
}

export const QuickActionCard: React.FC<QuickActionCardProps> = ({
  title,
  icon,
  backgroundColor = '#f0f0f0',
  onClick,
}) => {
  return (
    <Card
      hoverable
      style={{ textAlign: 'center', background: backgroundColor }}
      onClick={onClick}
    >
      <div style={{ fontSize: 32, marginBottom: 8 }}>{icon}</div>
      <Text strong>{title}</Text>
    </Card>
  );
};

// Metric Row Component
export interface MetricRowProps {
  metrics: {
    title: string;
    value: number | string;
    prefix?: React.ReactNode;
    suffix?: string;
    color?: string;
  }[];
}

export const MetricRow: React.FC<MetricRowProps> = ({ metrics }) => {
  return (
    <Row gutter={[16, 16]}>
      {metrics.map((metric, index) => (
        <Col xs={12} sm={6} key={index}>
          <Statistic
            title={metric.title}
            value={metric.value}
            prefix={metric.prefix}
            suffix={metric.suffix}
            valueStyle={{ color: metric.color }}
          />
        </Col>
      ))}
    </Row>
  );
};

// Timeline Card
export interface TimelineCardProps {
  title: string;
  icon: React.ReactNode;
  items: {
    time: string;
    title: string;
    description?: string;
    status?: 'success' | 'warning' | 'error' | 'info';
  }[];
}

export const TimelineCard: React.FC<TimelineCardProps> = ({ title, icon, items }) => {
  return (
    <Card
      title={
        <Space>
          {icon}
          <span>{title}</span>
        </Space>
      }
    >
      {/* Timeline items would be rendered here */}
      <div>
        {items.map((item, index) => (
          <div
            key={index}
            style={{
              padding: '12px 0',
              borderBottom: index < items.length - 1 ? '1px solid #f0f0f0' : 'none',
            }}
          >
            <Text strong>{item.title}</Text>
            {item.description && (
              <>
                <br />
                <Text type="secondary">{item.description}</Text>
              </>
            )}
            <br />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {item.time}
            </Text>
          </div>
        ))}
      </div>
    </Card>
  );
};

// Activity Feed Card
export interface ActivityFeedProps {
  activities: {
    id: string;
    type: string;
    title: string;
    timestamp: string;
    status?: string;
  }[];
  onActivityClick?: (activity: any) => void;
  maxItems?: number;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities,
  onActivityClick,
  maxItems = 5,
}) => {
  const displayedActivities = activities.slice(0, maxItems);

  return (
    <Card title="Recent Activity">
      <div>
        {displayedActivities.map((activity) => (
          <div
            key={activity.id}
            onClick={() => onActivityClick?.(activity)}
            style={{
              padding: '12px 0',
              borderBottom: '1px solid #f0f0f0',
              cursor: onActivityClick ? 'pointer' : 'default',
            }}
          >
            <Text strong>{activity.title}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {new Date(activity.timestamp).toLocaleString()}
            </Text>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default {
  DomainStatsCard,
  DataQualityCard,
  QuickActionCard,
  MetricRow,
  TimelineCard,
  ActivityFeed,
};
