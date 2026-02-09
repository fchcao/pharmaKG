import React, { useState, useEffect, useCallback } from 'react';
import {
  Input,
  Select,
  Button,
  Tabs,
  Tag,
  Space,
  Typography,
  Card,
  Row,
  Col,
  Divider,
  Empty,
  Spin,
  Alert,
  Dropdown,
  MenuProps,
  Tooltip,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  HistoryOutlined,
  StarOutlined,
  StarFilled,
  DownloadOutlined,
  ClearOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { debounce } from '../utils/helpers';
import { Domain, EntityType, DOMAIN_COLORS } from '../types';
import {
  FullTextSearchRequest,
  FullTextSearchResult,
  SearchFilters,
  SavedQuery,
  EntityTab,
} from './types';
import { useFullTextSearch, useSearchSuggestions, useSaveQuery, useSavedQueries } from './api';
import { SearchBar } from '../components/SearchBar';
import { exportAsCSV } from '../utils/helpers';

const { Search } = Input;
const { Title, Text } = Typography;
const { Option } = Select;

const ENTITY_TYPE_OPTIONS: { value: EntityType; label: string; icon: string }[] = [
  { value: 'Compound', label: 'Compounds', icon: '🧪' },
  { value: 'Target', label: 'Targets', icon: '🎯' },
  { value: 'Assay', label: 'Assays', icon: '🔬' },
  { value: 'Pathway', label: 'Pathways', icon: '🔀' },
  { value: 'Trial', label: 'Clinical Trials', icon: '📋' },
  { value: 'Subject', label: 'Subjects', icon: '👤' },
  { value: 'Intervention', label: 'Interventions', icon: '💊' },
  { value: 'Outcome', label: 'Outcomes', icon: '📊' },
  { value: 'Manufacturer', label: 'Manufacturers', icon: '🏭' },
  { value: 'Facility', label: 'Facilities', icon: '🏢' },
  { value: 'Document', label: 'Documents', icon: '📄' },
  { value: 'Agency', label: 'Agencies', icon: '🏛️' },
  { value: 'Submission', label: 'Submissions', icon: '📝' },
];

const DOMAIN_OPTIONS: { value: Domain; label: string; color: string }[] = [
  { value: 'rd', label: 'R&D', color: DOMAIN_COLORS.rd.primary },
  { value: 'clinical', label: 'Clinical', color: DOMAIN_COLORS.clinical.primary },
  { value: 'supply', label: 'Supply Chain', color: DOMAIN_COLORS.supply.primary },
  { value: 'regulatory', label: 'Regulatory', color: DOMAIN_COLORS.regulatory.primary },
];

const RECENT_SEARCHES_KEY = 'pharmakg_recent_searches';

interface UnifiedSearchProps {
  className?: string;
  onResultClick?: (result: FullTextSearchResult) => void;
  defaultQuery?: string;
}

export const UnifiedSearch: React.FC<UnifiedSearchProps> = ({
  className = '',
  onResultClick,
  defaultQuery = '',
}) => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [query, setQuery] = useState(defaultQuery || searchParams.get('q') || '');
  const [selectedDomains, setSelectedDomains] = useState<Domain[]>(
    searchParams.get('domains')?.split(',') as Domain[] || []
  );
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<EntityType[]>(
    searchParams.get('entityTypes')?.split(',') as EntityType[] || []
  );
  const [activeTab, setActiveTab] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [recentSearches, setRecentSearches] = useState<Array<{ query: string; timestamp: number }>>([]);
  const [showFilters, setShowFilters] = useState(false);

  // API hooks
  const { data: searchResults, isLoading, error, refetch } = useFullTextSearch(
    {
      query,
      entity_types: selectedEntityTypes.length > 0 ? selectedEntityTypes : undefined,
      domains: selectedDomains.length > 0 ? selectedDomains : undefined,
      limit: pageSize,
      offset: (currentPage - 1) * pageSize,
      fuzzy: false,
    },
    {
      enabled: false,
    }
  );

  const { data: suggestions } = useSearchSuggestions(query);
  const saveQueryMutation = useSaveQuery();
  const { data: savedQueries } = useSavedQueries();

  // Load recent searches
  useEffect(() => {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    if (stored) {
      try {
        setRecentSearches(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse recent searches', e);
      }
    }
  }, []);

  // Update URL params when search changes
  useEffect(() => {
    const params: Record<string, string> = {};
    if (query) params.q = query;
    if (selectedDomains.length > 0) params.domains = selectedDomains.join(',');
    if (selectedEntityTypes.length > 0) params.entityTypes = selectedEntityTypes.join(',');
    setSearchParams(params);
  }, [query, selectedDomains, selectedEntityTypes, setSearchParams]);

  // Handle search
  const handleSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim()) return;

    setQuery(searchQuery);
    setCurrentPage(1);

    // Save to recent searches
    const newRecent = [
      { query: searchQuery, timestamp: Date.now() },
      ...recentSearches.filter((s) => s.query !== searchQuery),
    ].slice(0, 10);
    setRecentSearches(newRecent);
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(newRecent));
  }, [recentSearches]);

  // Debounced search
  const debouncedSearch = useCallback(
    debounce((q: string) => {
      if (q.trim()) {
        refetch();
      }
    }, 500),
    [refetch]
  );

  useEffect(() => {
    if (query) {
      debouncedSearch(query);
    }
  }, [query, selectedDomains, selectedEntityTypes, debouncedSearch]);

  // Group results by entity type
  const entityTabs: EntityTab[] = React.useMemo(() => {
    if (!searchResults) return [];

    const counts: Record<EntityType, number> = {} as Record<EntityType, number>;
    searchResults.forEach((result) => {
      counts[result.entity_type] = (counts[result.entity_type] || 0) + 1;
    });

    const tabs: EntityTab[] = [
      {
        entityType: 'all' as EntityType,
        label: 'All Results',
        icon: '🔍',
        count: searchResults.length,
        color: '#1890ff',
      },
    ];

    Object.entries(counts).forEach(([entityType, count]) => {
      const option = ENTITY_TYPE_OPTIONS.find((opt) => opt.value === entityType);
      if (option) {
        tabs.push({
          entityType: entityType as EntityType,
          label: option.label,
          icon: option.icon,
          count,
          color: DOMAIN_COLORS[ENTITY_TYPE_OPTIONS.find((o) => o.value === entityType)!.value as Domain]?.primary || '#999',
        });
      }
    });

    return tabs.sort((a, b) => b.count - a.count);
  }, [searchResults]);

  // Filter results by active tab
  const filteredResults = React.useMemo(() => {
    if (!searchResults) return [];
    if (activeTab === 'all') return searchResults;
    return searchResults.filter((r) => r.entity_type === activeTab);
  }, [searchResults, activeTab]);

  // Save query
  const handleSaveQuery = () => {
    const name = prompt('Enter a name for this saved query:');
    if (name) {
      saveQueryMutation.mutate({
        name,
        query,
        filters: {
          query,
          domains: selectedDomains,
          entityTypes: selectedEntityTypes,
        },
      });
    }
  };

  // Export results
  const handleExport = (format: 'csv' | 'json') => {
    if (!filteredResults.length) return;

    const data = filteredResults.map((r) => ({
      entity_id: r.entity_id,
      entity_type: r.entity_type,
      domain: r.domain,
      name: r.name,
      relevance_score: r.relevance_score,
      snippet: r.snippet,
    }));

    if (format === 'csv') {
      exportAsCSV(data, `search-results-${query}-${Date.now()}`);
    } else {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `search-results-${query}-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  const exportMenu: MenuProps['items'] = [
    {
      key: 'csv',
      label: 'Export as CSV',
      icon: <DownloadOutlined />,
      onClick: () => handleExport('csv'),
    },
    {
      key: 'json',
      label: 'Export as JSON',
      icon: <DownloadOutlined />,
      onClick: () => handleExport('json'),
    },
  ];

  // Clear all filters
  const handleClearFilters = () => {
    setSelectedDomains([]);
    setSelectedEntityTypes([]);
  };

  return (
    <div className={`unified-search ${className}`}>
      <Card>
        {/* Search Header */}
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={3}>Knowledge Graph Search</Title>
            <Text type="secondary">
              Search across compounds, targets, clinical trials, and regulatory data
            </Text>
          </div>

          {/* Search Bar */}
          <div>
            <SearchBar
              onSearch={(filters) => handleSearch(filters.query)}
              placeholder="Search for compounds, targets, trials, documents..."
              showDomainSelector={false}
            />
          </div>

          {/* Filters */}
          <div>
            <Space>
              <Button
                icon={<FilterOutlined />}
                onClick={() => setShowFilters(!showFilters)}
              >
                Filters
                {(selectedDomains.length > 0 || selectedEntityTypes.length > 0) && (
                  <Tag color="blue" style={{ marginLeft: 4 }}>
                    {selectedDomains.length + selectedEntityTypes.length}
                  </Tag>
                )}
              </Button>

              {(selectedDomains.length > 0 || selectedEntityTypes.length > 0) && (
                <Button
                  icon={<ClearOutlined />}
                  onClick={handleClearFilters}
                  size="small"
                >
                  Clear Filters
                </Button>
              )}

              {query && (
                <>
                  <Button
                    icon={<StarOutlined />}
                    onClick={handleSaveQuery}
                    disabled={saveQueryMutation.isPending}
                  >
                    Save Query
                  </Button>

                  <Dropdown menu={{ items: exportMenu }} trigger={['click']}>
                    <Button icon={<DownloadOutlined />}>
                      Export
                    </Button>
                  </Dropdown>
                </>
              )}
            </Space>

            {showFilters && (
              <Card size="small" style={{ marginTop: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Domains:</Text>
                    <div style={{ marginTop: 8 }}>
                      <Select
                        mode="multiple"
                        placeholder="Select domains"
                        value={selectedDomains}
                        onChange={setSelectedDomains}
                        style={{ width: '100%' }}
                        options={DOMAIN_OPTIONS.map((d) => ({
                          label: (
                            <Space>
                              <Tag color={d.color}>{d.label}</Tag>
                            </Space>
                          ),
                          value: d.value,
                        }))}
                      />
                    </div>
                  </div>

                  <Divider style={{ margin: '12px 0' }} />

                  <div>
                    <Text strong>Entity Types:</Text>
                    <div style={{ marginTop: 8 }}>
                      <Select
                        mode="multiple"
                        placeholder="Select entity types"
                        value={selectedEntityTypes}
                        onChange={setSelectedEntityTypes}
                        style={{ width: '100%' }}
                        options={ENTITY_TYPE_OPTIONS.map((e) => ({
                          label: (
                            <Space>
                              <span>{e.icon}</span>
                              <span>{e.label}</span>
                            </Space>
                          ),
                          value: e.value,
                        }))}
                      />
                    </div>
                  </div>
                </Space>
              </Card>
            )}
          </div>

          {/* Search Status */}
          {query && (
            <Space>
              <Text>
                Searching for <Text strong>"{query}"</Text>
              </Text>
              {selectedDomains.length > 0 && (
                <Text>
                  in <Text strong>{selectedDomains.join(', ')}</Text>
                </Text>
              )}
              {searchResults && (
                <Text type="secondary">
                  ({searchResults.length} results)
                </Text>
              )}
            </Space>
          )}

          {/* Results */}
          {query && (
            <>
              {isLoading && (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <Spin size="large" />
                  <div style={{ marginTop: 16 }}>
                    <Text type="secondary">Searching knowledge graph...</Text>
                  </div>
                </div>
              )}

              {error && (
                <Alert
                  message="Search Error"
                  description={error.message}
                  type="error"
                  showIcon
                  closable
                />
              )}

              {!isLoading && !error && searchResults && searchResults.length > 0 && (
                <Tabs
                  activeKey={activeTab}
                  onChange={setActiveTab}
                  type="card"
                  items={entityTabs.map((tab) => ({
                    key: tab.entityType,
                    label: (
                      <Space>
                        <span>{tab.icon}</span>
                        <span>{tab.label}</span>
                        <Tag color={tab.color}>{tab.count}</Tag>
                      </Space>
                    ),
                    children: (
                      <div>
                        <Row gutter={[16, 16]}>
                          {filteredResults.map((result) => (
                            <Col key={result.entity_id} xs={24} sm={12} lg={8}>
                              <Card
                                hoverable
                                size="small"
                                onClick={() => {
                                  if (onResultClick) {
                                    onResultClick(result);
                                  } else {
                                    navigate(`/entity/${result.entity_type}/${result.entity_id}`);
                                  }
                                }}
                                style={{
                                  borderColor: DOMAIN_COLORS[result.domain]?.primary,
                                }}
                              >
                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                  <div>
                                    <Tag color={DOMAIN_COLORS[result.domain]?.primary}>
                                      {result.entity_type}
                                    </Tag>
                                    <Tooltip title={`Relevance: ${result.relevance_score.toFixed(2)}`}>
                                      <Tag color="blue">
                                        {Math.round(result.relevance_score * 100)}% match
                                      </Tag>
                                    </Tooltip>
                                  </div>

                                  <Title level={5} style={{ margin: 0 }}>
                                    {result.name}
                                  </Title>

                                  {result.snippet && (
                                    <Text
                                      type="secondary"
                                      ellipsis={{ rows: 2 }}
                                      style={{ fontSize: '12px' }}
                                    >
                                      {result.snippet}
                                    </Text>
                                  )}

                                  {result.matched_fields && result.matched_fields.length > 0 && (
                                    <div>
                                      {result.matched_fields.slice(0, 3).map((field) => (
                                        <Tag key={field} style={{ fontSize: '11px' }}>
                                          {field}
                                        </Tag>
                                      ))}
                                    </div>
                                  )}
                                </Space>
                              </Card>
                            </Col>
                          ))}
                        </Row>

                        {/* Pagination */}
                        <div style={{ marginTop: 24, textAlign: 'center' }}>
                          <Button
                            disabled={currentPage === 1}
                            onClick={() => setCurrentPage((p) => p - 1)}
                          >
                            Previous
                          </Button>
                          <span style={{ margin: '0 16px' }}>
                            Page {currentPage}
                          </span>
                          <Button
                            disabled={filteredResults.length < pageSize}
                            onClick={() => setCurrentPage((p) => p + 1)}
                          >
                            Next
                          </Button>
                        </div>
                      </div>
                    ),
                  }))}
                />
              )}

              {!isLoading && !error && searchResults && searchResults.length === 0 && (
                <Empty
                  description={
                    <Space direction="vertical">
                      <Text>No results found for "{query}"</Text>
                      <Text type="secondary">
                        Try adjusting your search terms or filters
                      </Text>
                    </Space>
                  }
                />
              )}
            </>
          )}

          {/* Recent Searches */}
          {!query && recentSearches.length > 0 && (
            <div>
              <Divider>Recent Searches</Divider>
              <Space wrap>
                {recentSearches.slice(0, 5).map((search, index) => (
                  <Tag
                    key={index}
                    icon={<HistoryOutlined />}
                    closable
                    onClose={() => {
                      const newRecent = recentSearches.filter((_, i) => i !== index);
                      setRecentSearches(newRecent);
                      localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(newRecent));
                    }}
                    style={{ cursor: 'pointer', padding: '4px 8px' }}
                    onClick={() => handleSearch(search.query)}
                  >
                    {search.query}
                  </Tag>
                ))}
              </Space>
            </div>
          )}

          {/* Saved Queries */}
          {!query && savedQueries && savedQueries.length > 0 && (
            <div>
              <Divider>Saved Queries</Divider>
              <Space direction="vertical" style={{ width: '100%' }}>
                {savedQueries.slice(0, 5).map((savedQuery) => (
                  <Card key={savedQuery.id} size="small">
                    <Space>
                      <StarFilled style={{ color: '#faad14' }} />
                      <Text strong>{savedQuery.name}</Text>
                      <Text type="secondary">{savedQuery.query}</Text>
                      <Button
                        size="small"
                        type="link"
                        onClick={() => {
                          handleSearch(savedQuery.query);
                          if (savedQuery.filters.domains) {
                            setSelectedDomains(savedQuery.filters.domains);
                          }
                          if (savedQuery.filters.entityTypes) {
                            setSelectedEntityTypes(savedQuery.filters.entityTypes);
                          }
                        }}
                      >
                        Run Search
                      </Button>
                    </Space>
                  </Card>
                ))}
              </Space>
            </div>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default UnifiedSearch;
