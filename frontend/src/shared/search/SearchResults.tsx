import React, { useState, useMemo } from 'react';
import {
  Card,
  Tabs,
  Tag,
  Space,
  Typography,
  Row,
  Col,
  Pagination,
  Button,
  Dropdown,
  MenuProps,
  Tooltip,
  Badge,
  Empty,
  Spin,
  Alert,
  Collapse,
  Checkbox,
  InputNumber,
  Slider,
  Progress,
} from 'antd';
import {
  DownloadOutlined,
  SortAscendingOutlined,
  FilterOutlined,
  FullscreenOutlined,
  ShareAltOutlined,
} from '@ant-design/icons';
import { EntityType, Domain, DOMAIN_COLORS } from '../types';
import { FullTextSearchResult, EntityTab } from './types';
import { exportAsCSV } from '../utils/helpers';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface SearchResultsProps {
  results: FullTextSearchResult[];
  isLoading?: boolean;
  error?: string;
  totalCount?: number;
  currentPage?: number;
  pageSize?: number;
  onPageChange?: (page: number, pageSize: number) => void;
  onResultClick?: (result: FullTextSearchResult) => void;
  className?: string;
}

const ENTITY_TYPE_ICONS: Record<EntityType, string> = {
  Compound: '🧪',
  Target: '🎯',
  Assay: '🔬',
  Pathway: '🔀',
  Document: '📄',
  Agency: '🏛️',
  Submission: '📝',
  Manufacturer: '🏭',
  Facility: '🏢',
  Trial: '📋',
  Subject: '👤',
  Intervention: '💊',
  Outcome: '📊',
};

const ENTITY_TYPE_LABELS: Record<EntityType, string> = {
  Compound: 'Compound',
  Target: 'Target',
  Assay: 'Assay',
  Pathway: 'Pathway',
  Document: 'Document',
  Agency: 'Agency',
  Submission: 'Submission',
  Manufacturer: 'Manufacturer',
  Facility: 'Facility',
  Trial: 'Clinical Trial',
  Subject: 'Subject',
  Intervention: 'Intervention',
  Outcome: 'Outcome',
};

export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  isLoading = false,
  error,
  totalCount,
  currentPage = 1,
  pageSize = 20,
  onPageChange,
  onResultClick,
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'relevance' | 'name' | 'type'>('relevance');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedDomains, setSelectedDomains] = useState<Domain[]>([]);
  const [relevanceFilter, setRelevanceFilter] = useState<[number, number]>([0, 100]);

  // Group results by entity type
  const entityTabs = useMemo(() => {
    const counts: Record<string, number> = { all: results.length };
    const domainCounts: Record<Domain, number> = {} as Record<Domain, number>;

    results.forEach((result) => {
      counts[result.entity_type] = (counts[result.entity_type] || 0) + 1;
      domainCounts[result.domain] = (domainCounts[result.domain] || 0) + 1;
    });

    const tabs: EntityTab[] = [
      {
        entityType: 'all' as EntityType,
        label: 'All Results',
        icon: '🔍',
        count: counts.all || 0,
        color: '#1890ff',
      },
    ];

    Object.entries(counts).forEach(([entityType, count]) => {
      if (entityType !== 'all') {
        const domain = ENTITY_TYPE_LABELS[entityType as EntityType] as Domain;
        tabs.push({
          entityType: entityType as EntityType,
          label: ENTITY_TYPE_LABELS[entityType as EntityType],
          icon: ENTITY_TYPE_ICONS[entityType as EntityType],
          count,
          color: DOMAIN_COLORS[domain]?.primary || '#999',
        });
      }
    });

    return tabs.sort((a, b) => b.count - a.count);
  }, [results]);

  // Filter and sort results
  const filteredAndSortedResults = useMemo(() => {
    let filtered = [...results];

    // Apply domain filter
    if (selectedDomains.length > 0) {
      filtered = filtered.filter((r) => selectedDomains.includes(r.domain));
    }

    // Apply relevance filter
    filtered = filtered.filter(
      (r) => r.relevance_score * 100 >= relevanceFilter[0] && r.relevance_score * 100 <= relevanceFilter[1]
    );

    // Apply entity type filter
    if (activeTab !== 'all') {
      filtered = filtered.filter((r) => r.entity_type === activeTab);
    }

    // Sort results
    filtered.sort((a, b) => {
      let compareValue = 0;

      if (sortBy === 'relevance') {
        compareValue = a.relevance_score - b.relevance_score;
      } else if (sortBy === 'name') {
        compareValue = a.name.localeCompare(b.name);
      } else if (sortBy === 'type') {
        compareValue = a.entity_type.localeCompare(b.entity_type);
      }

      return sortOrder === 'asc' ? compareValue : -compareValue;
    });

    return filtered;
  }, [results, activeTab, sortBy, sortOrder, selectedDomains, relevanceFilter]);

  // Get domains for filter
  const availableDomains = useMemo(() => {
    const domains = new Set(results.map((r) => r.domain));
    return Array.from(domains);
  }, [results]);

  // Handle export
  const handleExport = (format: 'csv' | 'json') => {
    if (filteredAndSortedResults.length === 0) return;

    const data = filteredAndSortedResults.map((r) => ({
      entity_id: r.entity_id,
      entity_type: r.entity_type,
      domain: r.domain,
      name: r.name,
      relevance_score: r.relevance_score,
      snippet: r.snippet,
    }));

    if (format === 'csv') {
      exportAsCSV(data, `search-results-${Date.now()}`);
    } else {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `search-results-${Date.now()}.json`;
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

  const sortMenu: MenuProps['items'] = [
    {
      key: 'relevance',
      label: 'Sort by Relevance',
      onClick: () => setSortBy('relevance'),
    },
    {
      key: 'name',
      label: 'Sort by Name',
      onClick: () => setSortBy('name'),
    },
    {
      key: 'type',
      label: 'Sort by Type',
      onClick: () => setSortBy('type'),
    },
    {
      type: 'divider',
    },
    {
      key: 'toggle-order',
      label: sortOrder === 'asc' ? 'Descending' : 'Ascending',
      onClick: () => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc'),
    },
  ];

  // Render a single result card
  const renderResultCard = (result: FullTextSearchResult) => (
    <Col key={result.entity_id} xs={24} sm={12} lg={8} xl={6}>
      <Card
        hoverable
        size="small"
        onClick={() => onResultClick?.(result)}
        style={{
          height: '100%',
          borderColor: DOMAIN_COLORS[result.domain]?.primary,
          borderWidth: '2px',
        }}
        bodyStyle={{ padding: '12px' }}
      >
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Space size="small">
              <span style={{ fontSize: '16px' }}>
                {ENTITY_TYPE_ICONS[result.entity_type]}
              </span>
              <Tag color={DOMAIN_COLORS[result.domain]?.primary} style={{ margin: 0 }}>
                {result.entity_type}
              </Tag>
            </Space>
            <Tooltip title={`Relevance Score: ${(result.relevance_score * 100).toFixed(1)}%`}>
              <Progress
                type="circle"
                percent={Math.round(result.relevance_score * 100)}
                width={40}
                strokeColor={result.relevance_score > 0.8 ? '#52c41a' : result.relevance_score > 0.5 ? '#faad14' : '#ff4d4f'}
                format={(percent) => (
                  <span style={{ fontSize: '10px', fontWeight: 'bold' }}>
                    {percent}
                  </span>
                )}
              />
            </Tooltip>
          </div>

          {/* Name */}
          <Title
            level={5}
            style={{
              margin: 0,
              fontSize: '14px',
              fontWeight: 600,
            }}
            ellipsis={{ rows: 2, tooltip: result.name }}
          >
            {result.name}
          </Title>

          {/* Snippet */}
          {result.snippet && (
            <Paragraph
              ellipsis={{ rows: 3 }}
              style={{
                margin: 0,
                fontSize: '12px',
                color: '#666',
              }}
            >
              {result.snippet}
            </Paragraph>
          )}

          {/* Matched Fields */}
          {result.matched_fields && result.matched_fields.length > 0 && (
            <div style={{ marginTop: 4 }}>
              <Space size={[4, 4]} wrap>
                {result.matched_fields.slice(0, 4).map((field) => (
                  <Tag key={field} style={{ fontSize: '10px', margin: 0 }}>
                    {field}
                  </Tag>
                ))}
                {result.matched_fields.length > 4 && (
                  <Tag style={{ fontSize: '10px', margin: 0 }}>
                    +{result.matched_fields.length - 4} more
                  </Tag>
                )}
              </Space>
            </div>
          )}

          {/* Highlights */}
          {result.highlights && Object.keys(result.highlights).length > 0 && (
            <Collapse
              ghost
              size="small"
              style={{ marginTop: 8 }}
              items={[
                {
                  key: 'highlights',
                  label: (
                    <Text style={{ fontSize: '12px', color: '#999' }}>
                      Highlighted Matches
                    </Text>
                  ),
                  children: (
                    <Space direction="vertical" size="small" style={{ fontSize: '12px' }}>
                      {Object.entries(result.highlights).slice(0, 3).map(([field, highlight]) => (
                        <div key={field}>
                          <Text strong style={{ fontSize: '11px', color: '#666' }}>
                            {field}:
                          </Text>
                          <div
                            dangerouslySetInnerHTML={{ __html: highlight }}
                            style={{ color: '#999' }}
                          />
                        </div>
                      ))}
                    </Space>
                  ),
                },
              ]}
            />
          )}
        </Space>
      </Card>
    </Col>
  );

  if (isLoading) {
    return (
      <div className={`search-results ${className}`}>
        <Card>
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 24 }}>
              <Text type="secondary">Searching knowledge graph...</Text>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`search-results ${className}`}>
        <Alert
          message="Search Error"
          description={error}
          type="error"
          showIcon
          closable
        />
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className={`search-results ${className}`}>
        <Card>
          <Empty
            description={
              <Space direction="vertical">
                <Text>No results found</Text>
                <Text type="secondary">
                  Try adjusting your search terms or filters
                </Text>
              </Space>
            }
          />
        </Card>
      </div>
    );
  }

  const paginatedResults = filteredAndSortedResults.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className={`search-results ${className}`}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Title level={4} style={{ margin: 0 }}>
                Search Results
              </Title>
              <Badge count={filteredAndSortedResults.length} showZero />
              {totalCount && totalCount > filteredAndSortedResults.length && (
                <Text type="secondary">
                  (showing {filteredAndSortedResults.length} of {totalCount})
                </Text>
              )}
            </Space>

            <Space>
              <Dropdown menu={{ items: sortMenu }} trigger={['click']}>
                <Button icon={<SortAscendingOutlined />}>
                  Sort
                </Button>
              </Dropdown>

              <Dropdown menu={{ items: exportMenu }} trigger={['click']}>
                <Button icon={<DownloadOutlined />}>
                  Export
                </Button>
              </Dropdown>

              <Button
                icon={<ShareAltOutlined />}
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href);
                }}
              >
                Share
              </Button>
            </Space>
          </div>

          {/* Filters Sidebar */}
          <Collapse
            defaultActiveKey={['filters']}
            style={{ background: '#fafafa' }}
            items={[
              {
                key: 'filters',
                label: (
                  <Space>
                    <FilterOutlined />
                    <span>Filters</span>
                    {(selectedDomains.length > 0 || relevanceFilter[0] > 0 || relevanceFilter[1] < 100) && (
                      <Badge dot />
                    )}
                  </Space>
                ),
                children: (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {/* Domain Filter */}
                    <div>
                      <Text strong style={{ fontSize: '12px' }}>
                        Domains
                      </Text>
                      <div style={{ marginTop: 8 }}>
                        <Space wrap>
                          {availableDomains.map((domain) => (
                            <Checkbox
                              key={domain}
                              checked={selectedDomains.includes(domain)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedDomains([...selectedDomains, domain]);
                                } else {
                                  setSelectedDomains(selectedDomains.filter((d) => d !== domain));
                                }
                              }}
                            >
                              <Tag color={DOMAIN_COLORS[domain]?.primary} style={{ margin: 0 }}>
                                {domain.toUpperCase()}
                              </Tag>
                            </Checkbox>
                          ))}
                        </Space>
                      </div>
                    </div>

                    {/* Relevance Filter */}
                    <div>
                      <Text strong style={{ fontSize: '12px' }}>
                        Relevance Score
                      </Text>
                      <div style={{ marginTop: 8 }}>
                        <Slider
                          range
                          min={0}
                          max={100}
                          value={relevanceFilter}
                          onChange={setRelevanceFilter}
                          marks={{
                            0: '0%',
                            50: '50%',
                            100: '100%',
                          }}
                        />
                      </div>
                      <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                        <InputNumber
                          size="small"
                          min={0}
                          max={100}
                          value={relevanceFilter[0]}
                          onChange={(val) => setRelevanceFilter([val || 0, relevanceFilter[1]])}
                          formatter={(value) => `${value}%`}
                          parser={(value) => Number(value?.replace('%', ''))}
                        />
                        <span>-</span>
                        <InputNumber
                          size="small"
                          min={0}
                          max={100}
                          value={relevanceFilter[1]}
                          onChange={(val) => setRelevanceFilter([relevanceFilter[0], val || 100])}
                          formatter={(value) => `${value}%`}
                          parser={(value) => Number(value?.replace('%', ''))}
                        />
                      </div>
                    </div>
                  </Space>
                ),
              },
            ]}
          />

          {/* Entity Type Tabs */}
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
                  <Badge
                    count={tab.count}
                    showZero
                    style={{
                      backgroundColor: tab.color,
                      fontSize: '11px',
                      padding: '0 4px',
                    }}
                  />
                </Space>
              ),
            }))}
          />

          {/* Results Grid */}
          <Row gutter={[16, 16]}>
            {paginatedResults.map((result) => renderResultCard(result))}
          </Row>

          {/* Pagination */}
          {filteredAndSortedResults.length > pageSize && onPageChange && (
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: 24 }}>
              <Pagination
                current={currentPage}
                pageSize={pageSize}
                total={filteredAndSortedResults.length}
                onChange={onPageChange}
                showSizeChanger
                showTotal={(total, range) =>
                  `${range[0]}-${range[1]} of ${total} results`
                }
                pageSizeOptions={['10', '20', '50', '100']}
              />
            </div>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default SearchResults;
