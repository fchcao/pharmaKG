# Shared UI Components Implementation Guide

This document provides comprehensive documentation for all shared UI components implemented in the PharmaKG frontend.

## Table of Contents

1. [Component Overview](#component-overview)
2. [Component API Reference](#component-api-reference)
3. [Props Interfaces](#props-interfaces)
4. [Usage Examples](#usage-examples)
5. [Integration Guide](#integration-guide)
6. [Styling and Theming](#styling-and-theming)

---

## Component Overview

The following shared UI components have been implemented:

| Component | File | Description |
|-----------|------|-------------|
| SearchBar | `SearchBar.tsx` | Unified search with autocomplete and domain filtering |
| EntityCard | `EntityCard.tsx` | Display entity information with expandable details |
| RelationshipViewer | `RelationshipViewer.tsx` | Show entity relationships in list or graph view |
| DataTable | `DataTable.tsx` | Paginated data tables with sorting and filtering |
| LoadingSpinner | `LoadingSpinner.tsx` | Loading indicator with optional message |
| ErrorBoundary | `ErrorBoundary.tsx` | Error handling wrapper for React components |
| EmptyState | `EmptyState.tsx` | Empty results display with customizable actions |

---

## Component API Reference

### SearchBar

A unified search component with autocomplete dropdown, domain selector, and recent searches.

**Props:**

```typescript
interface SearchBarProps {
  onSearch: (filters: SearchFilters) => void;  // Required: Callback when search is executed
  placeholder?: string;                         // Optional: Input placeholder text
  defaultDomain?: Domain;                       // Optional: Default selected domain
  showDomainSelector?: boolean;                 // Optional: Show/hide domain dropdown
  showRecentSearches?: boolean;                 // Optional: Show/hide recent searches
  className?: string;                           // Optional: Additional CSS classes
}
```

**Features:**
- Autocomplete with debounced suggestions
- Domain selector (R&D, Clinical, Supply, Regulatory)
- Recent searches stored in localStorage
- Keyboard support (Enter to search)
- Clear recent searches button

**Example:**

```tsx
import { SearchBar } from '@/shared/components';

function MyPage() {
  const handleSearch = (filters) => {
    console.log('Search query:', filters.query);
    console.log('Selected domains:', filters.domains);
  };

  return (
    <SearchBar
      onSearch={handleSearch}
      placeholder="Search compounds, targets, trials..."
      defaultDomain="rd"
      showDomainSelector={true}
    />
  );
}
```

---

### EntityCard

Display entity information with type-specific styling and expandable details.

**Props:**

```typescript
interface EntityCardProps {
  entityType: EntityType;    // Required: Type of entity (Compound, Target, etc.)
  entityId: string;          // Required: Unique entity identifier
  data: Partial<Entity>;      // Required: Entity data
  onExpand?: () => void;     // Optional: Callback when expanded/collapsed
  onAction?: (action: string) => void;  // Optional: Callback for actions
}
```

**Features:**
- Domain-specific coloring (green for R&D, blue for Clinical, etc.)
- Entity type icon and label
- Expandable property details
- Quick actions (view in graph, relationships, add to workspace)
- Copy ID and share functionality

**Example:**

```tsx
import { EntityCard } from '@/shared/components';

function EntityDetail({ entity }) {
  const handleAction = (action) => {
    switch (action) {
      case 'view-graph':
        // Navigate to graph view
        break;
      case 'download':
        // Download entity data
        break;
    }
  };

  return (
    <EntityCard
      entityType="Compound"
      entityId={entity.id}
      data={entity}
      onAction={handleAction}
    />
  );
}
```

---

### RelationshipViewer

Show entity relationships with list and compact graph view modes.

**Props:**

```typescript
interface RelationshipViewerProps {
  entityId: string;                           // Required: Entity ID to load relationships for
  entityType: EntityType;                     // Required: Type of the entity
  viewMode?: 'list' | 'graph';               // Optional: Default view mode
  relationshipTypes?: RelationshipType[];     // Optional: Filter by relationship types
}
```

**Features:**
- Toggle between list and graph view
- Filter by relationship type
- Sortable table columns
- Export to CSV
- Click to navigate to related entities

**Example:**

```tsx
import { RelationshipViewer } from '@/shared/components';

function EntityRelationships({ entity }) {
  return (
    <RelationshipViewer
      entityId={entity.id}
      entityType="Compound"
      viewMode="list"
      relationshipTypes={['TARGETS', 'ASSAYS']}
    />
  );
}
```

---

### DataTable

Paginated data tables with sorting, filtering, and export capabilities.

**Props:**

```typescript
interface DataTableProps<T = unknown> {
  columns: TableColumn<T>[];                  // Required: Table column definitions
  data: T[];                                  // Required: Table data
  loading?: boolean;                          // Optional: Show loading state
  pagination?: {                              // Optional: Pagination configuration
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number, pageSize: number) => void;
  };
  onRowClick?: (record: T) => void;          // Optional: Row click handler
  rowSelection?: {                            // Optional: Row selection configuration
    selectedRowKeys: string[];
    onChange: (selectedRowKeys: string[]) => void;
  };
}
```

**Features:**
- Sortable columns
- Per-column search filters
- Pagination controls
- Export to CSV/JSON
- Row selection
- Double-click to view details

**Example:**

```tsx
import { DataTable } from '@/shared/components';

function CompoundsList() {
  const columns = [
    {
      key: 'name',
      title: 'Name',
      dataIndex: 'name',
      sorter: true,
      filterable: true,
    },
    {
      key: 'type',
      title: 'Type',
      dataIndex: 'type',
      render: (type) => <Tag>{type}</Tag>,
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={compounds}
      loading={isLoading}
      pagination={{
        page: 1,
        pageSize: 20,
        total: 1000,
        onPageChange: (page, pageSize) => console.log(page, pageSize),
      }}
    />
  );
}
```

---

### LoadingSpinner

Loading indicator with optional message and fullscreen mode.

**Props:**

```typescript
interface LoadingSpinnerProps extends SpinProps {
  message?: string;          // Optional: Loading message
  fullscreen?: boolean;      // Optional: Show as fullscreen overlay
  size?: 'small' | 'default' | 'large';  // Optional: Spinner size
}
```

**Features:**
- Configurable size
- Customizable message
- Fullscreen overlay mode
- Inherits all Ant Design Spin props

**Example:**

```tsx
import { LoadingSpinner } from '@/shared/components';

function MyComponent() {
  if (isLoading) {
    return <LoadingSpinner message="Loading compounds..." fullscreen />;
  }
  return <div>{/* Content */}</div>;
}
```

---

### ErrorBoundary

Error handling wrapper that catches and displays errors gracefully.

**Props:**

```typescript
interface Props {
  children: ReactNode;              // Required: Child components to wrap
  fallback?: ReactNode;             // Optional: Custom error fallback UI
  onError?: (error: Error, errorInfo: ErrorInfo) => void;  // Optional: Error callback
}
```

**Features:**
- Catches JavaScript errors anywhere in child component tree
- Displays error message and stack trace
- Provides reset and reload actions
- Custom fallback UI support
- Error callback for logging

**Example:**

```tsx
import { ErrorBoundary } from '@/shared/components';

function App() {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('Error caught:', error, errorInfo);
        // Send to error tracking service
      }}
    >
      <MyComponent />
    </ErrorBoundary>
  );
}
```

---

### EmptyState

Empty results display with customizable illustrations and actions.

**Props:**

```typescript
interface EmptyStateProps {
  type?: 'no-results' | 'no-data' | 'error' | 'info' | 'custom';
  title?: string;              // Optional: Custom title
  description?: string;        // Optional: Custom description
  image?: React.ReactNode;     // Optional: Custom image/illustration
  actionLabel?: string;        // Optional: Action button label
  onAction?: () => void;       // Optional: Action button callback
  illustration?: React.ReactNode;  // Optional: Custom illustration
}
```

**Features:**
- Predefined types with icons (no-results, no-data, error, info)
- Custom title and description
- Optional action button
- Custom illustration support

**Example:**

```tsx
import { EmptyState } from '@/shared/components';

function NoResults() {
  return (
    <EmptyState
      type="no-results"
      title="No compounds found"
      description="Try adjusting your search filters"
      actionLabel="Clear filters"
      onAction={() => clearFilters()}
    />
  );
}
```

---

## Props Interfaces

Complete TypeScript interfaces for all props:

```typescript
// Domain types
type Domain = 'rd' | 'clinical' | 'supply' | 'regulatory';

// Entity types
type EntityType =
  | 'Compound'
  | 'Target'
  | 'Assay'
  | 'Pathway'
  | 'Document'
  | 'Agency'
  | 'Submission'
  | 'Manufacturer'
  | 'Facility'
  | 'Trial'
  | 'Subject'
  | 'Intervention'
  | 'Outcome';

// Relationship types
type RelationshipType =
  | 'TARGETS'
  | 'ASSAYS'
  | 'IN_PATHWAY'
  | 'REGULATED_BY'
  | 'MANUFACTURES'
  | 'SUPPLIES'
  | 'TESTED_IN'
  | 'RELATED_TO';

// Search filters
interface SearchFilters {
  query: string;
  domains?: Domain[];
  entityTypes?: EntityType[];
  limit?: number;
  offset?: number;
}

// Table column
interface TableColumn<T = unknown> {
  key: string;
  title: string;
  dataIndex?: keyof T | string;
  sorter?: boolean;
  filterable?: boolean;
  render?: (value: unknown, record: T) => React.ReactNode;
  width?: number;
  align?: 'left' | 'center' | 'right';
}
```

---

## Usage Examples

### Complete Page Example

```tsx
import React, { useState } from 'react';
import { Layout, Typography } from 'antd';
import {
  SearchBar,
  DataTable,
  EntityCard,
  LoadingSpinner,
  ErrorBoundary,
  EmptyState
} from '@/shared/components';
import { useSearch, useEntity } from '@/shared/api/hooks';

const { Header, Content } = Layout;
const { Title } = Typography;

function SearchPage() {
  const [searchFilters, setSearchFilters] = useState(null);
  const [selectedEntityId, setSelectedEntityId] = useState(null);

  const { data: searchResults, isLoading } = useSearch(searchFilters || {});
  const { data: entity } = useEntity(selectedEntityId, 'Compound', {
    enabled: !!selectedEntityId,
  });

  const handleSearch = (filters) => {
    setSearchFilters(filters);
  };

  const columns = [
    { key: 'name', title: 'Name', dataIndex: 'name', sorter: true },
    { key: 'type', title: 'Type', dataIndex: 'type' },
  ];

  return (
    <ErrorBoundary>
      <Layout>
        <Header>
          <Title level={3}>PharmaKG Search</Title>
          <SearchBar onSearch={handleSearch} />
        </Header>
        <Content style={{ padding: '24px' }}>
          {isLoading ? (
            <LoadingSpinner message="Searching..." />
          ) : searchResults?.length === 0 ? (
            <EmptyState type="no-results" />
          ) : (
            <>
              <DataTable
                columns={columns}
                data={searchResults || []}
                onRowClick={(record) => setSelectedEntityId(record.id)}
              />
              {entity && (
                <EntityCard
                  entityType="Compound"
                  entityId={entity.id}
                  data={entity}
                />
              )}
            </>
          )}
        </Content>
      </Layout>
    </ErrorBoundary>
  );
}
```

---

## Integration Guide

### Installation

1. Ensure all dependencies are installed:

```bash
cd frontend
npm install
```

### Import Components

Import from the shared components module:

```tsx
// Individual imports
import { SearchBar } from '@/shared/components';
import { EntityCard } from '@/shared/components';
import { DataTable } from '@/shared/components';

// Or import all
import {
  SearchBar,
  EntityCard,
  DataTable,
  RelationshipViewer,
  LoadingSpinner,
  ErrorBoundary,
  EmptyState
} from '@/shared/components';
```

### API Integration

Components are designed to work with the React Query hooks:

```tsx
import { useSearch, useEntity, useRelationships } from '@/shared/api/hooks';

function MyComponent() {
  const { data, isLoading, error } = useSearch({
    query: 'aspirin',
    domains: ['rd'],
  });

  // Use data in components
}
```

---

## Styling and Theming

### Domain Color Scheme

Each domain has a specific color palette:

- **R&D**: Green (#4CAF50)
- **Clinical**: Blue (#2196F3)
- **Supply Chain**: Orange (#FF9800)
- **Regulatory**: Purple (#9C27B0)

### Tailwind CSS

Components use Tailwind CSS for utility classes. Custom theme colors are defined in `tailwind.config.js`.

### Ant Design

Components use Ant Design components. Customize theme in your app configuration:

```tsx
import { ConfigProvider } from 'antd';
import theme from './theme';

function App() {
  return (
    <ConfigProvider theme={theme}>
      {/* Your app */}
    </ConfigProvider>
  );
}
```

---

## File Structure

```
frontend/src/shared/
├── components/
│   ├── SearchBar.tsx
│   ├── EntityCard.tsx
│   ├── RelationshipViewer.tsx
│   ├── DataTable.tsx
│   ├── LoadingSpinner.tsx
│   ├── ErrorBoundary.tsx
│   ├── EmptyState.tsx
│   └── index.ts
├── types/
│   └── index.ts
├── api/
│   ├── client.ts
│   └── hooks.ts
├── utils/
│   └── helpers.ts
└── index.ts
```

---

## Best Practices

1. **Error Handling**: Always wrap pages in ErrorBoundary
2. **Loading States**: Use LoadingSpinner for async operations
3. **Empty States**: Display EmptyState when no data is available
4. **TypeScript**: Use provided interfaces for type safety
5. **Accessibility**: Components include ARIA labels and keyboard support
6. **Responsive**: All components are mobile-friendly

---

## Troubleshooting

### Common Issues

1. **Components not rendering**: Ensure Ant Design styles are imported
2. **Type errors**: Check that you're using correct TypeScript interfaces
3. **API errors**: Verify API base URL in `.env` file
4. **Styling issues**: Check Tailwind CSS is properly configured

---

## Next Steps

After implementing shared components:

1. Implement domain-specific pages (R&D, Clinical, Supply, Regulatory)
2. Create graph visualization components
3. Build advanced search interface
4. Add authentication and user preferences

---

## Support

For issues or questions, please refer to:
- Project documentation: `/docs`
- Component examples: `/src/shared/components/`
- API reference: `/src/shared/api/`
