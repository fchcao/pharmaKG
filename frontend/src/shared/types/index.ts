// Domain types
export type Domain = 'rd' | 'clinical' | 'supply' | 'regulatory';

// Entity types
export type EntityType =
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
export type RelationshipType =
  | 'TARGETS'
  | 'ASSAYS'
  | 'IN_PATHWAY'
  | 'REGULATED_BY'
  | 'MANUFACTURES'
  | 'SUPPLIES'
  | 'TESTED_IN'
  | 'RELATED_TO';

// Base entity interface
export interface Entity {
  id: string;
  type: EntityType;
  domain: Domain;
  name: string;
  properties?: Record<string, unknown>;
}

// Relationship interface
export interface Relationship {
  id: string;
  source: string;
  target: string;
  type: RelationshipType;
  properties?: Record<string, unknown>;
}

// Search interfaces
export interface SearchResult {
  entity: Entity;
  relevance?: number;
  snippet?: string;
}

export interface SearchFilters {
  query: string;
  domains?: Domain[];
  entityTypes?: EntityType[];
  limit?: number;
  offset?: number;
}

export interface SearchSuggestion {
  id: string;
  text: string;
  type: EntityType;
  count?: number;
}

// Recent search interface
export interface RecentSearch {
  query: string;
  timestamp: number;
  domain?: Domain;
  resultsCount?: number;
}

// Graph visualization interfaces
export interface GraphNode {
  id: string;
  label: string;
  type: EntityType;
  domain: Domain;
  data?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type: RelationshipType;
  data?: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// API response interfaces
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Error interface
export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// Table column interface
export interface TableColumn<T = unknown> {
  key: string;
  title: string;
  dataIndex?: keyof T | string;
  sorter?: boolean;
  filterable?: boolean;
  render?: (value: unknown, record: T) => React.ReactNode;
  width?: number;
  align?: 'left' | 'center' | 'right';
}

// Entity card props
export interface EntityCardProps {
  entityType: EntityType;
  entityId: string;
  data: Partial<Entity>;
  onExpand?: () => void;
  onAction?: (action: string) => void;
}

// Relationship viewer props
export interface RelationshipViewerProps {
  entityId: string;
  entityType: EntityType;
  viewMode?: 'list' | 'graph';
  relationshipTypes?: RelationshipType[];
}

// Data table props
export interface DataTableProps<T = unknown> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number, pageSize: number) => void;
  };
  onRowClick?: (record: T) => void;
  rowSelection?: {
    selectedRowKeys: string[];
    onChange: (selectedRowKeys: string[]) => void;
  };
}

// Export format
export type ExportFormat = 'csv' | 'json' | 'excel';

// Loading state
export interface LoadingState {
  isLoading: boolean;
  error?: string | null;
}

// Theme colors by domain
export const DOMAIN_COLORS: Record<Domain, { primary: string; secondary: string; text: string }> = {
  rd: {
    primary: '#4CAF50',
    secondary: '#E8F5E9',
    text: '#2E7D32'
  },
  clinical: {
    primary: '#2196F3',
    secondary: '#E3F2FD',
    text: '#1565C0'
  },
  supply: {
    primary: '#FF9800',
    secondary: '#FFF3E0',
    text: '#E65100'
  },
  regulatory: {
    primary: '#9C27B0',
    secondary: '#F3E5F5',
    text: '#6A1B9A'
  }
};

// Entity type to domain mapping
export const ENTITY_DOMAIN_MAP: Record<EntityType, Domain> = {
  Compound: 'rd',
  Target: 'rd',
  Assay: 'rd',
  Pathway: 'rd',
  Trial: 'clinical',
  Subject: 'clinical',
  Intervention: 'clinical',
  Outcome: 'clinical',
  Manufacturer: 'supply',
  Facility: 'supply',
  Document: 'regulatory',
  Agency: 'regulatory',
  Submission: 'regulatory'
};

// Export dashboard types
export * from './dashboard';
