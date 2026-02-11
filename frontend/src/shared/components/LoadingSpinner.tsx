import React from 'react';
import { Spin, Typography, Space } from 'antd';
import type { SpinProps } from 'antd';

const { Text } = Typography;

interface LoadingSpinnerProps {
  message?: string;
  fullscreen?: boolean;
  size?: 'small' | 'default' | 'large';
  spinning?: boolean;
  loading?: boolean;  // Alias for spinning, used by some pages
  tip?: string;
  delay?: number;
  indicator?: React.ReactNode;
  children?: React.ReactNode;  // Content to wrap
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  fullscreen = false,
  size = 'default',
  spinning,
  loading,
  tip,
  delay,
  indicator,
  children,
}) => {
  // Support both 'spinning' and 'loading' props
  const isLoading = spinning !== undefined ? spinning : (loading !== undefined ? loading : true);

  // If there are children, use Spin as a wrapper
  if (children) {
    return (
      <Spin
        spinning={isLoading}
        tip={tip || message}
        delay={delay}
        indicator={indicator}
        size={size}
      >
        {children}
      </Spin>
    );
  }

  // Standalone spinner without children
  const content = (
    <Space direction="vertical" size="middle">
      <Spin size={size} spinning={isLoading} tip={tip} delay={delay} indicator={indicator} />
      {message && !tip && (
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
