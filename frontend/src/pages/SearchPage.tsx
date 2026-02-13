import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UnifiedSearch, AdvancedSearch, SearchResults, SearchFilters } from '../shared/search';
import { FullTextSearchResult } from '../shared/search/types';
import { EntityType } from '../shared/types';
import { useFullTextSearch } from '../shared/search/api';
import { Layout, Space, Button, Typography } from 'antd';
import { SearchOutlined, FilterOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { Sider, Content } = Layout;

// Helper function to map entity types to their detail page routes
const getEntityDetailPath = (entityType: EntityType, id: string): string => {
  const routeMap: Record<string, string> = {
    'Compound': `/rd/compounds/${id}`,
    'Target': `/rd/targets/${id}`,
    'Assay': `/rd/assays/${id}`,
    'Pathway': `/rd/pathways/${id}`,
    'ClinicalTrial': `/clinical/trials/${id}`,
    'Trial': `/clinical/trials/${id}`,
    'Subject': `/clinical/subjects/${id}`,
    'Intervention': `/clinical/interventions/${id}`,
    'Outcome': `/clinical/outcomes/${id}`,
    'Manufacturer': `/supply/manufacturers/${id}`,
    'DrugProduct': `/supply/drugs/${id}`,
    'Facility': `/supply/facilities/${id}`,
    'Submission': `/regulatory/submissions/${id}`,
    'Approval': `/regulatory/approvals/${id}`,
    'Agency': `/regulatory/agencies/${id}`,
    'Document': `/regulatory/documents/${id}`,
  };
  return routeMap[entityType] || `/`;
};

const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchMode, setSearchMode] = useState<'unified' | 'advanced'>('unified');
  const [currentFilters, setCurrentFilters] = useState<SearchFilters | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);

  // Execute search based on filters
  const { data: searchResults, isLoading, error, refetch } = useFullTextSearch(
    currentFilters
      ? {
          query: currentFilters.query,
          entity_types: currentFilters.entityTypes?.map(String),
          limit: pageSize,
          skip: (currentPage - 1) * pageSize
        }
      : ({} as any),
    {
      enabled: !!currentFilters?.query && currentFilters.query.length > 0,
    }
  );

  // Handle search from UnifiedSearch
  const handleUnifiedSearch = (filters: SearchFilters) => {
    setCurrentFilters(filters);
    setCurrentPage(1);
  };

  // Handle search from AdvancedSearch
  const handleAdvancedSearch = (filters: SearchFilters) => {
    setCurrentFilters(filters);
    setCurrentPage(1);
  };

  // Auto-trigger search when filters change
  useEffect(() => {
    if (currentFilters?.query && currentFilters.query.length > 0) {
      refetch();
    }
  }, [currentFilters, refetch]);

  // Handle result click
  const handleResultClick = (result: FullTextSearchResult) => {
    console.log(`Clicked on ${result.entity_type}: ${result.name}`);

    // Backend API expects primary_id (like "CHEMBL123"), NOT element_id (Neo4j format)
    // element_id is in format "4:xxx:xxx" which is not URL-friendly
    // For entities where primary_id is null, use name as fallback (e.g., ChEMBL compounds)
    const id = result.primary_id || result.name || result.entity_id || result.element_id;

    if (id) {
      const detailPath = getEntityDetailPath(result.entity_type, id);
      navigate(detailPath);
    } else {
      console.error('No valid ID found for navigation:', result);
    }
  };

  // Handle page change
  const handlePageChange = (page: number, size: number) => {
    setCurrentPage(page);
    refetch();
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
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

              {searchMode === 'unified' ? (
                <div>
                  <Title level={4}>Quick Tips</Title>
                  <ul style={{ fontSize: '14px', color: '#666', paddingLeft: '16px' }}>
                    <li>Use quotes for exact phrases: "drug discovery"</li>
                    <li>Use AND/OR to combine terms</li>
                    <li>Filter by entity type</li>
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
            </div>
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
