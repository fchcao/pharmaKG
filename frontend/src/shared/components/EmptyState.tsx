import React from 'react';
import { Empty, Button, Space, Typography } from 'antd';
import {
  FileSearchOutlined,
  DatabaseOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

type EmptyStateType = 'no-results' | 'no-data' | 'error' | 'info' | 'custom';

interface EmptyStateProps {
  type?: EmptyStateType;
  title?: string;
  description?: string;
  image?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  illustration?: React.ReactNode;
}

const EMPTY_STATE_CONFIG: Record<EmptyStateType, { icon: React.ReactNode; defaultTitle: string; defaultDescription: string }> = {
  'no-results': {
    icon: <FileSearchOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />,
    defaultTitle: 'No Results Found',
    defaultDescription: 'Try adjusting your search or filters to find what you are looking for.',
  },
  'no-data': {
    icon: <DatabaseOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />,
    defaultTitle: 'No Data Available',
    defaultDescription: 'There is no data to display at the moment.',
  },
  'error': {
    icon: <WarningOutlined style={{ fontSize: 64, color: '#ff4d4f' }} />,
    defaultTitle: 'Something Went Wrong',
    defaultDescription: 'An error occurred while loading the data. Please try again.',
  },
  'info': {
    icon: <InfoCircleOutlined style={{ fontSize: 64, color: '#1890ff' }} />,
    defaultTitle: 'Information',
    defaultDescription: 'Additional information about this section.',
  },
  'custom': {
    icon: null,
    defaultTitle: '',
    defaultDescription: '',
  },
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  type = 'no-data',
  title,
  description,
  image,
  actionLabel,
  onAction,
  illustration,
}) => {
  const config = EMPTY_STATE_CONFIG[type];

  const renderContent = () => {
    if (illustration) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          {illustration}
          <Space direction="vertical" size="middle" style={{ marginTop: 24 }}>
            {title && <Text strong style={{ fontSize: 16 }}>{title}</Text>}
            {description && <Text type="secondary">{description}</Text>}
            {actionLabel && onAction && (
              <Button type="primary" onClick={onAction}>
                {actionLabel}
              </Button>
            )}
          </Space>
        </div>
      );
    }

    return (
      <Empty
        image={image || (config.icon && undefined)}
        imageStyle={config.icon ? { height: 60 } : undefined}
        description={
          <Space direction="vertical" size="small">
            <Text strong>{title || config.defaultTitle}</Text>
            <Text type="secondary">{description || config.defaultDescription}</Text>
          </Space>
        }
      >
        {actionLabel && onAction && (
          <Button type="primary" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </Empty>
    );
  };

  return <div className="empty-state">{renderContent()}</div>;
};

export default EmptyState;
