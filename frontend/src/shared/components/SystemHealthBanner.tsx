import React from 'react';
import { Alert, Space, Badge, Typography, Statistic, Row, Col } from 'antd';
import {
  ThunderboltOutlined,
  DatabaseOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { useSystemHealth } from '@/pages/dashboardHooks';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/en';

dayjs.extend(relativeTime);

const { Text } = Typography;

export interface SystemHealthBannerProps {
  style?: React.CSSProperties;
  className?: string;
  showDetails?: boolean;
}

const SystemHealthBanner: React.FC<SystemHealthBannerProps> = ({
  style,
  className,
  showDetails = false,
}) => {
  const { data: systemHealth, isLoading } = useSystemHealth({
    refetchInterval: 30000, // 30 second polling
  });

  if (isLoading || !systemHealth) {
    return null;
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined />;
      case 'degraded':
        return <WarningOutlined />;
      case 'down':
        return <CloseCircleOutlined />;
      default:
        return <CheckCircleOutlined />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'success';
    }
  };

  const isSystemHealthy = systemHealth.api_status === 'healthy' && systemHealth.neo4j_status === 'healthy';

  return (
    <Alert
      message={
        <Space size="large" wrap>
          <Badge
            status={getStatusBadge(systemHealth.api_status)}
            text={`API: ${systemHealth.api_status.toUpperCase()}`}
          />
          <Badge
            status={getStatusBadge(systemHealth.neo4j_status)}
            text={`Neo4j: ${systemHealth.neo4j_status.toUpperCase()}`}
          />
          <Text>
            <ThunderboltOutlined /> Avg Response: {systemHealth.avg_response_time_ms}ms
          </Text>
          <Text>
            Uptime: {systemHealth.uptime_percentage.toFixed(2)}%
          </Text>
          {showDetails && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Last updated: {dayjs(systemHealth.last_updated).fromNow()}
            </Text>
          )}
        </Space>
      }
      type={isSystemHealthy ? 'success' : systemHealth.api_status === 'degraded' ? 'warning' : 'error'}
      showIcon
      style={style}
      className={className}
    />
  );
};

export default SystemHealthBanner;
