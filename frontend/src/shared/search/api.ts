import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import {
  FullTextSearchRequest,
  FullTextSearchResult,
  FuzzySearchRequest,
  FuzzySearchResult,
  SearchSuggestion,
  AggregateSearchRequest,
  AggregateSearchResult,
  MultiEntitySearchRequest,
  MultiEntitySearchResult,
  SavedQuery,
} from './types';

// Query key factories
export const searchQueryKeys = {
  fulltext: (request: FullTextSearchRequest) => ['search', 'fulltext', request] as const,
  fuzzy: (request: FuzzySearchRequest) => ['search', 'fuzzy', request] as const,
  suggestions: (query: string, entityType?: string) =>
    ['search', 'suggestions', query, entityType] as const,
  aggregate: (request: AggregateSearchRequest) => ['search', 'aggregate', request] as const,
  multiEntity: (request: MultiEntitySearchRequest) => ['search', 'multi', request] as const,
  savedQueries: () => ['search', 'savedQueries'] as const,
};

/**
 * Hook for full-text search with relevance scoring
 */
export function useFullTextSearch(
  request: FullTextSearchRequest,
  options?: UseQueryOptions<FullTextSearchResult[], Error>
) {
  return useQuery<FullTextSearchResult[], Error>({
    queryKey: searchQueryKeys.fulltext(request),
    queryFn: async () => {
      // Backend returns a wrapped response: { results: [], total: 0, ... }
      const response = await apiClient.post<{
        results: FullTextSearchResult[];
        total: number;
        returned: number;
        query: string;
        message?: string;
      }>('/v1/search/fulltext', {
        query: request.query,
        entity_types: request.entity_types,
        domains: request.domains,
        limit: request.limit,
        skip: request.skip || 0,  // Backend uses 'skip' not 'offset'
      });
      // Extract results array from response
      return response.results || [];
    },
    enabled: !!request.query && request.query.length > 0,
    ...options,
  });
}

/**
 * Hook for fuzzy search with edit distance
 */
export function useFuzzySearch(
  request: FuzzySearchRequest,
  options?: UseQueryOptions<FuzzySearchResult[], Error>
) {
  return useQuery<FuzzySearchResult[], Error>({
    queryKey: searchQueryKeys.fuzzy(request),
    queryFn: async () => {
      // Backend returns a wrapped response
      const response = await apiClient.post<{
        results: FuzzySearchResult[];
        total: number;
        returned: number;
        query: string;
        message?: string;
      }>('/v1/search/fuzzy', {
        query: request.query,
        entity_type: request.entity_type,
        search_field: request.search_field || 'name',
        max_distance: request.max_distance || 2,
        limit: request.limit,
        skip: request.skip || 0,
      });
      // Extract results array from response
      return response.results || [];
    },
    enabled: !!request.query && request.query.length > 0,
    ...options,
  });
}

/**
 * Hook for search suggestions
 */
export function useSearchSuggestions(
  query: string,
  entityType?: string,
  options?: UseQueryOptions<SearchSuggestion[], Error>
) {
  return useQuery<SearchSuggestion[], Error>({
    queryKey: searchQueryKeys.suggestions(query, entityType),
    queryFn: async () => {
      // Backend returns wrapped response: { suggestions: [], ... }
      const response = await apiClient.get<{
        suggestions: SearchSuggestion[];
        total: number;
        prefix: string;
        entity_type: string;
        search_field: string;
      }>('/v1/search/suggestions', {
        params: { prefix: query, entity_type: entityType || 'Compound' },
      });
      // Extract suggestions array from response
      return response.suggestions || [];
    },
    enabled: !!query && query.length > 1,
    ...options,
  });
}

/**
 * Hook for aggregated search results
 */
export function useAggregateSearch(
  request: AggregateSearchRequest,
  options?: UseQueryOptions<AggregateSearchResult[], Error>
) {
  return useQuery<AggregateSearchResult[], Error>({
    queryKey: searchQueryKeys.aggregate(request),
    queryFn: async () => {
      // Backend returns wrapped response: { groups: [], ... }
      const response = await apiClient.post<{
        groups: AggregateSearchResult[];
        total_groups: number;
        total_results: number;
        query: string;
        group_by: string;
      }>('/v1/search/aggregate', request);
      // Extract groups array from response
      return response.groups || [];
    },
    enabled: !!request.query && request.query.length > 0,
    ...options,
  });
}

/**
 * Hook for multi-entity search
 */
export function useMultiEntitySearch(
  request: MultiEntitySearchRequest,
  options?: UseQueryOptions<MultiEntitySearchResult[], Error>
) {
  return useQuery<MultiEntitySearchResult[], Error>({
    queryKey: searchQueryKeys.multiEntity(request),
    queryFn: () => apiClient.post<MultiEntitySearchResult[]>('/v1/search/multi-entity', request),
    enabled: !!request.queries && request.queries.length > 0,
    ...options,
  });
}

/**
 * Hook for saved queries
 */
export function useSavedQueries(options?: UseQueryOptions<SavedQuery[], Error>) {
  return useQuery<SavedQuery[], Error>({
    queryKey: searchQueryKeys.savedQueries(),
    queryFn: () => {
      const stored = localStorage.getItem('pharmakg_saved_queries');
      return stored ? JSON.parse(stored) : [];
    },
    ...options,
  });
}

/**
 * Hook for saving a query
 */
export function useSaveQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (query: Omit<SavedQuery, 'id' | 'created_at'>) => {
      const savedQueries = JSON.parse(
        localStorage.getItem('pharmakg_saved_queries') || '[]'
      ) as SavedQuery[];

      const newQuery: SavedQuery = {
        ...query,
        id: `query-${Date.now()}`,
        created_at: Date.now(),
      };

      savedQueries.unshift(newQuery);
      localStorage.setItem('pharmakg_saved_queries', JSON.stringify(savedQueries));

      return newQuery;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: searchQueryKeys.savedQueries() });
    },
  });
}

/**
 * Hook for deleting a saved query
 */
export function useDeleteQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (queryId: string) => {
      const savedQueries = JSON.parse(
        localStorage.getItem('pharmakg_saved_queries') || '[]'
      ) as SavedQuery[];

      const filtered = savedQueries.filter((q) => q.id !== queryId);
      localStorage.setItem('pharmakg_saved_queries', JSON.stringify(filtered));

      return queryId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: searchQueryKeys.savedQueries() });
    },
  });
}

/**
 * Hook for updating a saved query's last used timestamp
 */
export function useUpdateQueryLastUsed() {
  return useMutation({
    mutationFn: async ({ queryId, lastUsed }: { queryId: string; lastUsed: number }) => {
      const savedQueries = JSON.parse(
        localStorage.getItem('pharmakg_saved_queries') || '[]'
      ) as SavedQuery[];

      const updated = savedQueries.map((q) =>
        q.id === queryId ? { ...q, last_used: lastUsed } : q
      );

      localStorage.setItem('pharmakg_saved_queries', JSON.stringify(updated));
      return queryId;
    },
  });
}
