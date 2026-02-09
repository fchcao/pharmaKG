# PharmaKG Search Components

This directory contains the search interface components for PharmaKG, providing powerful search capabilities across the pharmaceutical knowledge graph.

## Components

### 1. UnifiedSearch (`UnifiedSearch.tsx`)

The main search interface with real-time suggestions and intelligent filtering.

**Features:**
- Real-time search suggestions from backend API
- Domain and entity type filtering
- Recent searches (stored in localStorage)
- Saved queries with custom names
- Tabbed results by entity type
- Relevance score display
- Export to CSV/JSON
- URL parameter support for sharing searches

**Props:**
```typescript
interface UnifiedSearchProps {
  className?: string;
  onResultClick?: (result: FullTextSearchResult) => void;
  defaultQuery?: string;
}
```

**Example Usage:**
```tsx
import { UnifiedSearch } from '@/shared/search';

function MyComponent() {
  return (
    <UnifiedSearch
      defaultQuery="aspirin"
      onResultClick={(result) => {
        console.log('Clicked:', result.name);
        // Navigate to entity detail page
        navigate(`/entity/${result.entity_type}/${result.entity_id}`);
      }}
    />
  );
}
```

### 2. AdvancedSearch (`AdvancedSearch.tsx`)

Complex query builder for sophisticated searches.

**Features:**
- Multi-field filters
- Numerical range sliders
- Date range pickers
- Boolean operators (AND/OR/NOT)
- Custom condition builder
- Saved queries management
- Query export/import

**Props:**
```typescript
interface AdvancedSearchProps {
  onSearch: (filters: SearchFilters) => void;
  className?: string;
  initialFilters?: SearchFilters;
}
```

**Example Usage:**
```tsx
import { AdvancedSearch } from '@/shared/search';

function MyComponent() {
  const handleSearch = (filters) => {
    console.log('Search filters:', filters);
    // Execute search with filters
  };

  return (
    <AdvancedSearch
      onSearch={handleSearch}
      initialFilters={{
        query: 'cancer',
        domains: ['clinical'],
        entityTypes: ['Trial'],
      }}
    />
  );
}
```

### 3. SearchResults (`SearchResults.tsx`)

Display search results with advanced filtering and sorting.

**Features:**
- Tabbed by entity type
- Faceted navigation
- Relevance score filtering
- Multiple sort options
- Pagination controls
- Export functionality
- Shareable URLs

**Props:**
```typescript
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
```

**Example Usage:**
```tsx
import { SearchResults } from '@/shared/search';

function MyComponent() {
  const [results, setResults] = useState([]);

  return (
    <SearchResults
      results={results}
      isLoading={isLoading}
      currentPage={1}
      pageSize={20}
      onPageChange={(page, size) => {
        console.log('Page changed:', page, size);
      }}
      onResultClick={(result) => {
        console.log('Clicked:', result.name);
      }}
    />
  );
}
```

## API Hooks

The search module provides React Query hooks for data fetching:

### `useFullTextSearch(request, options?)`

Execute full-text search with relevance scoring.

```tsx
const { data, isLoading, error } = useFullTextSearch({
  query: 'aspirin',
  entity_types: ['Compound', 'Target'],
  domains: ['rd'],
  limit: 20,
  offset: 0,
  fuzzy: false,
});
```

### `useFuzzySearch(request, options?)`

Execute fuzzy search with edit distance.

```tsx
const { data } = useFuzzySearch({
  query: 'asprin',
  entity_types: ['Compound'],
  max_edits: 2,
  limit: 10,
});
```

### `useSearchSuggestions(query, entityType?, options?)`

Get search suggestions as user types.

```tsx
const { data: suggestions } = useSearchSuggestions('asp', 'Compound');
```

### `useAggregateSearch(request, options?)`

Get aggregated search results grouped by entity type, domain, or property.

```tsx
const { data } = useAggregateSearch({
  query: 'cancer',
  aggregate_by: 'entity_type',
  domains: ['clinical'],
});
```

### `useMultiEntitySearch(request, options?)`

Search multiple entity types simultaneously.

```tsx
const { data } = useMultiEntitySearch({
  queries: [
    { query: 'aspirin', entity_types: ['Compound'] },
    { query: 'COX-1', entity_types: ['Target'] },
  ],
  limit: 10,
});
```

### Saved Queries Hooks

```tsx
// Get saved queries
const { data: savedQueries } = useSavedQueries();

// Save a query
const saveQueryMutation = useSaveQuery();
saveQueryMutation.mutate({
  name: 'My Search',
  query: 'aspirin',
  filters: { query: 'aspirin', domains: ['rd'] },
});

// Delete a saved query
const deleteQueryMutation = useDeleteQuery();
deleteQueryMutation.mutate(queryId);

// Update last used timestamp
const updateLastUsedMutation = useUpdateQueryLastUsed();
updateLastUsedMutation.mutate({ queryId, lastUsed: Date.now() });
```

## Data Types

### SearchFilters

```typescript
interface SearchFilters {
  query: string;
  domains?: Domain[];
  entityTypes?: EntityType[];
  dateRange?: {
    start?: string;
    end?: string;
  };
  numericalRanges?: Record<string, { min?: number; max?: number }>;
  properties?: Record<string, unknown>;
  booleanOperator?: 'AND' | 'OR' | 'NOT';
}
```

### FullTextSearchResult

```typescript
interface FullTextSearchResult {
  entity_id: string;
  entity_type: EntityType;
  domain: Domain;
  name: string;
  relevance_score: number;
  snippet?: string;
  matched_fields?: string[];
  highlights?: Record<string, string>;
}
```

### SavedQuery

```typescript
interface SavedQuery {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  created_at: number;
  last_used?: number;
}
```

## Backend Integration

The search components integrate with the following backend endpoints:

- `POST /api/v1/search/fulltext` - Full-text search with relevance scores
- `POST /api/v1/search/fuzzy` - Fuzzy search with edit distance
- `GET /api/v1/search/suggestions` - Auto-complete suggestions
- `POST /api/v1/search/aggregate` - Aggregated search results
- `POST /api/v1/search/multi-entity` - Multi-entity search

## State Management

- Uses **React Query** for server state management
- **localStorage** for recent searches and saved queries
- **URL parameters** for sharing searches

## User Experience Features

### Real-time Suggestions
- Debounced input (300ms delay)
- Shows recent searches
- Displays entity type and count
- Keyboard navigation support

### Visual Feedback
- Loading states during search
- Empty state messages
- Error handling with alerts
- Relevance score indicators

### Accessibility
- Keyboard shortcuts (Ctrl+K to focus search)
- ARIA labels on interactive elements
- Semantic HTML structure
- Focus management

### Performance
- Debounced search input
- Result pagination
- Lazy loading of suggestions
- Optimized re-renders

## Best Practices

1. **Always provide an `onResultClick` handler** to navigate to entity details
2. **Use the UnifiedSearch component** for most use cases - it's more user-friendly
3. **Reserve AdvancedSearch** for power users who need complex queries
4. **Implement proper error handling** for network failures
5. **Use URL parameters** for sharing searches between users
6. **Clear filters** when starting a new search to avoid confusion

## Example Integration

See `/root/autodl-tmp/pj-pharmaKG/frontend/src/pages/SearchPage.tsx` for a complete example of integrating all search components.

## Dependencies

- `@ant-design/icons` - Icons
- `@tanstack/react-query` - Data fetching
- `react-router-dom` - Navigation (optional)
- `dayjs` - Date handling (AdvancedSearch)
- Ant Design components - UI components

## Future Enhancements

- [ ] Search analytics and tracking
- [ ] Search history visualization
- [ ] Collaborative filtering
- [ ] ML-powered relevance ranking
- [ ] Voice search support
- [ ] Search result clustering
- [ ] Advanced result visualization
