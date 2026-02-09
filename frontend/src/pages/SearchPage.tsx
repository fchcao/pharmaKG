import React, { useState } from 'react';
import { Layout, Tabs, Button, Space, Typography, message } from 'antd';
import { SearchOutlined, FilterOutlined } from '@ant-design/icons';
import { UnifiedSearch, AdvancedSearch, SearchResults, SearchFilters } from '../shared/search';
import { FullTextSearchResult } from '../shared/search/types';
import { useFullTextSearch } from '../shared/search/api';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;

const SearchPage: React.FC = () => {
  const [searchMode, setSearchMode] = useState<'unified' | 'advanced'>('unified');
  const [currentFilters, setCurrentFilters] = useState<SearchFilters | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);

  // Execute search based on filters
  const { data: searchResults, isLoading, error, refetch } = useFullTextSearch(
    currentFilters
      ? {
          query: currentFilters.query,
          entity_types: currentFilters.entityTypes,
          domains: currentFilters.domains,
          limit: pageSize,
          offset: (currentPage - 1) * pageSize,
          fuzzy: false,
        }
      : ({} as any),
    {
      enabled: false,
    }
  );

  // Handle search from UnifiedSearch
  const handleUnifiedSearch = (filters: SearchFilters) => {
    setCurrentFilters(filters);
    setCurrentPage(1);
    refetch();
  };

  // Handle search from AdvancedSearch
  const handleAdvancedSearch = (filters: SearchFilters) => {
    setCurrentFilters(filters);
    setCurrentPage(1);
    refetch();
  };

  // Handle result click
  const handleResultClick = (result: FullTextSearchResult) => {
    message.info(`Clicked on ${result.entity_type}: ${result.name}`);
    // Navigate to entity detail page
    // navigate(`/entity/${result.entity_type}/${result.entity_id}`);
  };

  // Handle page change
  const handlePageChange = (page: number, size: number) => {
    setCurrentPage(page);
    refetch();
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0' }}>
        <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          <Title level={3} style={{ margin: 0 }}>
            PharmaKG Search
          </Title>
        </div>
      </Header>

      <Layout>
        <Sider width={300} style={{ background: '#fff', padding: '24px' }}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Title level={4}>Search Mode</Title>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  type={searchMode === 'unified' ? 'primary' : 'default'}
                  icon={<SearchOutlined />}
                  onClick={() => setSearchMode('unified')}
                  block
                >
                  Unified Search
                </Button>
                <Button
                  type={searchMode === 'advanced' ? 'primary' : 'default'}
                  icon={<FilterOutlined />}
                  onClick={() => setSearchMode('advanced')}
                  block
                >
                  Advanced Search
                </Button>
              </Space>
            </div>

            {searchMode === 'unified' ? (
              <div>
                <Title level={4}>Quick Tips</Title>
                <ul style={{ fontSize: '14px', color: '#666', paddingLeft: '16px' }}>
                  <li>Use quotes for exact phrases: "drug discovery"</li>
                  <li>Use AND/OR to combine terms</li>
                  <li>Filter by domain or entity type</li>
                  <li>Save frequent searches for quick access</li>
                </ul>
              </div>
            ) : (
              <div>
                <Title level={4}>Advanced Tips</Title>
                <ul style={{ fontSize: '14px', color: '#666', paddingLeft: '16px' }}>
                  <li>Build complex queries with multiple conditions</li>
                  <li>Use range filters for numerical values</li>
                  <li>Combine with boolean operators (AND/OR/NOT)</li>
                  <li>Save queries for future use</li>
                </ul>
              </div>
            )}

            {currentFilters && (
              <div>
                <Title level={4}>Current Search</Title>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Query: "{currentFilters.query}"
                </Text>
                {currentFilters.domains && currentFilters.domains.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      Domains: {currentFilters.domains.join(', ')}
                    </Text>
                  </div>
                )}
                {currentFilters.entityTypes && currentFilters.entityTypes.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      Types: {currentFilters.entityTypes.join(', ')}
                    </Text>
                  </div>
                )}
              </div>
            )}
          </Space>
        </Sider>

        <Content style={{ padding: '24px' }}>
          <div style={{ maxWidth: 1400, margin: '0 auto' }}>
            {searchMode === 'unified' ? (
              <>
                <UnifiedSearch
                  onSearch={handleUnifiedSearch}
                  className="mb-4"
                />

                {searchResults && searchResults.length > 0 && (
                  <div style={{ marginTop: 24 }}>
                    <SearchResults
                      results={searchResults}
                      isLoading={isLoading}
                      error={error?.message}
                      currentPage={currentPage}
                      pageSize={pageSize}
                      onPageChange={handlePageChange}
                      onResultClick={handleResultClick}
                    />
                  </div>
                )}
              </>
            ) : (
              <>
                <AdvancedSearch
                  onSearch={handleAdvancedSearch}
                  className="mb-4"
                />

                {searchResults && searchResults.length > 0 && (
                  <div style={{ marginTop: 24 }}>
                    <SearchResults
                      results={searchResults}
                      isLoading={isLoading}
                      error={error?.message}
                      currentPage={currentPage}
                      pageSize={pageSize}
                      onPageChange={handlePageChange}
                      onResultClick={handleResultClick}
                    />
                  </div>
                )}
              </>
            )}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default SearchPage;
