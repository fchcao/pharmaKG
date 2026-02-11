import { useEffect, useState } from 'react';
import { Card, Button, Spin, Alert, Typography } from 'antd';
import apiClient from '@/shared/api/client';

const { Title, Paragraph, Text } = Typography;

interface ApiData {
  items: any[];
  total: number;
  page: number;
  pageSize: number;
}

const TestApi: React.FC = () => {
  const [data, setData] = useState<ApiData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testApi = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Fetching /rd/compounds...');
      const result = await apiClient.get<ApiData>('/rd/compounds', {
        params: { page: 1, page_size: 5 }
      });
      console.log('API Result:', result);
      setData(result);
    } catch (err: any) {
      console.error('API Error:', err);
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="API Test">
        <Title level={4}>Frontend-Backend Connection Test</Title>

        <Paragraph>
          <Text>Click the button below to test the API connection:</Text>
        </Paragraph>

        <Button type="primary" onClick={testApi} loading={loading}>
          Test API (/rd/compounds)
        </Button>

        {error && (
          <Alert
            message="API Error"
            description={error}
            type="error"
            style={{ marginTop: '16px' }}
            showIcon
          />
        )}

        {data && (
          <Alert
            message="API Success!"
            description={`Received ${data.items.length} items. Total: ${data.total}`}
            type="success"
            style={{ marginTop: '16px' }}
            showIcon
          />
        )}

        {data && (
          <div style={{ marginTop: '16px' }}>
            <Title level={5}>Data Preview:</Title>
            <pre style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </Card>
    </div>
  );
};

export default TestApi;
