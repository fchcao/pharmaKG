import React, { useState, useEffect, useRef, KeyboardEvent, useMemo, useCallback } from 'react';
import { AutoComplete, Input, Select, Button, Space, Tag, Dropdown } from 'antd';
import { SearchOutlined, HistoryOutlined, ClearOutlined } from '@ant-design/icons';
import { useSearchSuggestions, useSaveSearch } from '../api/hooks';
import { Domain, SearchFilters, RecentSearch } from '../types';
import { storage } from '../utils/helpers';

const { Option } = Select;

interface SearchBarProps {
  onSearch: (filters: SearchFilters) => void;
  placeholder?: string;
  defaultDomain?: Domain;
  showDomainSelector?: boolean;
  showRecentSearches?: boolean;
  className?: string;
}

const DOMAIN_OPTIONS: { value: Domain; label: string }[] = [
  { value: 'rd', label: 'R&D' },
  { value: 'clinical', label: 'Clinical' },
  { value: 'supply', label: 'Supply Chain' },
  { value: 'regulatory', label: 'Regulatory' },
];

const RECENT_SEARCHES_KEY = 'pharmakg_recent_searches';

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  placeholder = 'Search compounds, targets, trials...',
  defaultDomain = 'rd',
  showDomainSelector = true,
  showRecentSearches = true,
  className = '',
}) => {
  const [query, setQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<Domain>(defaultDomain);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);

  const { data: suggestions, isLoading: suggestionsLoading } = useSearchSuggestions(query);
  const saveSearchMutation = useSaveSearch();

  const searchInputRef = useRef<any>(null);
  const optionsUpdateRef = useRef(false);

  // Load recent searches from localStorage
  useEffect(() => {
    if (showRecentSearches) {
      const stored = storage.get<RecentSearch[]>(RECENT_SEARCHES_KEY, []);
      setRecentSearches(stored);
    }
  }, [showRecentSearches]);

  // Memoized options to prevent unnecessary re-renders that cause focus loss
  const options = useMemo(() => {
    if (!query || optionsUpdateRef.current) {
      optionsUpdateRef.current = false;
      return [];
    }

    const opts: { value: string; label: string }[] = [];

    // Add recent searches
    if (showRecentSearches && recentSearches.length > 0) {
      const matchingRecent = recentSearches
        .filter((s) => s.query.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 3);
      matchingRecent.forEach((search) => {
        opts.push({
          value: search.query,
          label: (
            <div>
              <HistoryOutlined style={{ marginRight: 8 }} />
              {search.query}
            </div>
          ),
        });
      });
    }

    // Add suggestions
    if (suggestions && suggestions.length > 0) {
      suggestions.slice(0, 5).forEach((suggestion) => {
        if (!opts.find((o) => o.value === suggestion.text)) {
          opts.push({
            value: suggestion.text,
            label: (
              <div>
                {suggestion.text}
                {suggestion.frequency && <span style={{ marginLeft: 8, color: '#999' }}>({suggestion.frequency})</span>}
              </div>
            ),
          });
        }
      });
    }

    return opts;
  }, [query, suggestions, recentSearches, showRecentSearches]);

  const handleSearch = (searchQuery?: string) => {
    const finalQuery = searchQuery || query;
    if (!finalQuery.trim()) return;

    const filters: SearchFilters = {
      query: finalQuery,
      domains: showDomainSelector ? [selectedDomain] : undefined,
    };

    // Save to recent searches
    saveSearchMutation.mutate({ query: finalQuery, domain: selectedDomain });

    // Update local state
    const newRecentSearch: RecentSearch = {
      query: finalQuery,
      timestamp: Date.now(),
      domain: selectedDomain,
    };
    const updatedRecentSearches = [newRecentSearch, ...recentSearches.filter((s) => s.query !== finalQuery)].slice(
      0,
      10
    );
    setRecentSearches(updatedRecentSearches);
    storage.set(RECENT_SEARCHES_KEY, updatedRecentSearches);

    onSearch(filters);
    setQuery(''); // Clear input after search
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleSelect = (value: string) => {
    // Don't update query state here to avoid focus loss
    // Directly call handleSearch with the selected value
    handleSearch(value);
    // Clear query after a small delay to avoid focus loss during render
    setTimeout(() => {
      setQuery('');
      optionsUpdateRef.current = true; // Prevent showing options immediately after selection
    }, 0);
  };

  const handleClearRecentSearches = () => {
    setRecentSearches([]);
    storage.remove(RECENT_SEARCHES_KEY);
  };

  const recentSearchesMenu = {
    items: recentSearches.slice(0, 5).map((search) => ({
      key: search.query,
      label: (
        <div>
          <span>{search.query}</span>
          {search.domain && <Tag style={{ marginLeft: 8 }}>{search.domain}</Tag>}
        </div>
      ),
      onClick: () => handleSearch(search.query),
    })),
  };

  return (
    <div className={`search-bar ${className}`}>
      <Space.Compact style={{ width: '100%' }}>
        {showDomainSelector && (
          <Select
            value={selectedDomain}
            onChange={setSelectedDomain}
            style={{ width: 120 }}
            options={DOMAIN_OPTIONS}
          />
        )}
        <AutoComplete
          ref={searchInputRef}
          value={query}
          onChange={setQuery}
          options={options}
          onSelect={handleSelect}
          style={{ flex: 1 }}
          placeholder={placeholder}
          // Don't disable the input while loading - this causes focus loss
          // disabled={suggestionsLoading}
          notFoundContent={null}
          // Use built-in debounce for search instead of external state management
          onSearch={(text) => {
            // This triggers when user types, but we use useSearchSuggestions hook
            // which already handles debouncing via react-query
          }}
        >
          <Input
            suffix={
              <Space>
                {showRecentSearches && recentSearches.length > 0 && (
                  <Dropdown menu={recentSearchesMenu} trigger={['click']}>
                    <Button
                      type="text"
                      icon={<HistoryOutlined />}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Dropdown>
                )}
                {recentSearches.length > 0 && (
                  <Button
                    type="text"
                    icon={<ClearOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleClearRecentSearches();
                    }}
                  />
                )}
                <Button
                  type="primary"
                  icon={<SearchOutlined />}
                  onClick={() => handleSearch()}
                  disabled={!query.trim()}
                />
              </Space>
            }
            onPressEnter={handleKeyPress}
          />
        </AutoComplete>
      </Space.Compact>
    </div>
  );
};

export default SearchBar;
