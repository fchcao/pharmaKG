import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button, Result, Typography, Card, Space } from 'antd';

const { Paragraph, Text } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div style={{ padding: '50px 20px', textAlign: 'center' }}>
          <Result
            status="error"
            title="Something went wrong"
            subTitle="An unexpected error occurred. Please try refreshing the page."
            extra={[
              <Button type="primary" key="reset" onClick={this.handleReset}>
                Try Again
              </Button>,
              <Button key="reload" onClick={this.handleReload}>
                Reload Page
              </Button>,
            ]}
          >
            <Space direction="vertical" style={{ width: '100%', textAlign: 'left' }} size="middle">
              <Card title="Error Details" size="small">
                {this.state.error && (
                  <div>
                    <Text strong>Error Message:</Text>
                    <Paragraph code copyable>
                      {this.state.error.toString()}
                    </Paragraph>
                  </div>
                )}
                {this.state.errorInfo && (
                  <div>
                    <Text strong>Component Stack:</Text>
                    <Paragraph code copyable style={{ fontSize: 12 }}>
                      {this.state.errorInfo.componentStack}
                    </Paragraph>
                  </div>
                )}
              </Card>

              <Paragraph type="secondary">
                If this problem persists, please contact support with the error details above.
              </Paragraph>
            </Space>
          </Result>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
