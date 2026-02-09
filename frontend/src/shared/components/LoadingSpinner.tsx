import React from 'react';
import { Spin, Typography, Space } from 'antd';
import type { SpinProps } from 'antd';

const { Text } = Typography;

interface LoadingSpinnerProps extends SpinProps {
  message?: string;
  fullscreen?: boolean;
  size?: 'small' | 'default' | 'large';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  fullscreen = false,
  size = 'default',
  ...spinProps
}) => {
  const content = (
    <Space direction="vertical" size="middle">
      <Spin size={size} {...spinProps} />
      {message && (
        <Text type="secondary" style={{ fontSize: 14 }}>
          {message}
        </Text>
      )}
    </Space>
  );

  if (fullscreen) {
    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          zIndex: 9999,
        }}
      >
        {content}
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
      }}
    >
      {content}
    </div>
  );
};

export default LoadingSpinner;
