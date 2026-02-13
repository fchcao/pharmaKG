import { Domain, EntityType } from '../types';

// Extended search interfaces for the search module

export interface FullTextSearchRequest {
  query: string;
  entity_types?: string[];  // Backend expects string[], not EntityType[]
  limit?: number;
  skip?: number;  // Backend uses 'skip' not 'offset'
}

export interface FullTextSearchResult {
  entity_id?: string;  // Optional for backward compatibility
  element_id?: string;  // Backend returns element_id from elementId(node)
  primary_id?: string;  // Backend returns primary_id from node.primary_id
  entity_type: EntityType;
  domain?: Domain;  // Optional - backend may not always return domain
  name: string;
  relevance_score?: number;  // Optional for backward compatibility
  score?: number;  // Backend returns score from fulltext search
  snippet?: string;
  matched_fields?: string[];
  highlights?: Record<string, string>;
}

export interface FuzzySearchRequest {
  query: string;
  entity_type: string;  // Backend expects single entity_type as string
  search_field?: string;
  max_distance?: number;  // Backend uses 'max_distance' not 'max_edits'
  limit?: number;
  skip?: number;
}

export interface FuzzySearchResult {
  entity_id: string;
  entity_type: EntityType;
  domain: Domain;
  name: string;
  edit_distance: number;
  similarity_score: number;
}

export interface SearchSuggestion {
  text: string;
  frequency: number;  // Backend uses 'frequency' not 'count'
}

export interface AggregateSearchRequest {
  query: string;
  entity_types?: EntityType[];
  domains?: Domain[];
  aggregate_by?: 'entity_type' | 'domain' | 'property';
  property_name?: string;
}

export interface AggregateSearchResult {
  group_by_value: string;
  count: number;
  results: FullTextSearchResult[];
}

export interface MultiEntitySearchRequest {
  queries: Array<{
    query: string;
    entity_types: EntityType[];
  }>;
  limit?: number;
}

export interface MultiEntitySearchResult {
  query_index: number;
  results: FullTextSearchResult[];
}

export interface SavedQuery {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  created_at: number;
  last_used?: number;
}

export interface SearchFilters {
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

export interface SearchState {
  filters: SearchFilters;
  results: FullTextSearchResult[];
  isLoading: boolean;
  error?: string;
  totalCount: number;
  currentPage: number;
  pageSize: number;
}

export interface FilterOption {
  label: string;
  value: string;
  count?: number;
  icon?: string;
}

export interface EntityTab {
  entityType: EntityType;
  label: string;
  icon: string;
  count: number;
  color: string;
}
