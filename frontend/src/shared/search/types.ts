import { Domain, EntityType } from '../types';

// Extended search interfaces for the search module

export interface FullTextSearchRequest {
  query: string;
  entity_types?: EntityType[];
  domains?: Domain[];
  limit?: number;
  offset?: number;
  fuzzy?: boolean;
}

export interface FullTextSearchResult {
  entity_id: string;
  entity_type: EntityType;
  domain: Domain;
  name: string;
  relevance_score: number;
  snippet?: string;
  matched_fields?: string[];
  highlights?: Record<string, string>;
}

export interface FuzzySearchRequest {
  query: string;
  entity_types?: EntityType[];
  domains?: Domain[];
  max_edits?: number;
  limit?: number;
  offset?: number;
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
  entity_type: EntityType;
  count?: number;
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
