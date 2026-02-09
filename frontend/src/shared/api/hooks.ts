import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { apiClient } from './client';
import {
  Entity,
  SearchResult,
  SearchFilters,
  SearchSuggestion,
  Relationship,
  GraphData,
  PaginatedResponse,
  ApiError,
} from '../types';

// Query key factories
export const queryKeys = {
  // Entity queries
  entity: (id: string, type: string) => ['entity', id, type] as const,
  entities: (type: string, filters?: Record<string, unknown>) =>
    ['entities', type, filters] as const,

  // Search queries
  search: (filters: SearchFilters) => ['search', filters] as const,
  suggestions: (query: string, entityType?: string) =>
    ['suggestions', query, entityType] as const,
  recentSearches: () => ['recentSearches'] as const,

  // Relationship queries
  relationships: (entityId: string, types?: string[]) =>
    ['relationships', entityId, types] as const,
  graph: (entityId: string, depth?: number) => ['graph', entityId, depth] as const,

  // Domain queries
  rd: {
    compounds: (filters?: Record<string, unknown>) => ['rd', 'compounds', filters] as const,
    targets: (filters?: Record<string, unknown>) => ['rd', 'targets', filters] as const,
    assays: (filters?: Record<string, unknown>) => ['rd', 'assays', filters] as const,
    pathways: (filters?: Record<string, unknown>) => ['rd', 'pathways', filters] as const,
  },
  clinical: {
    trials: (filters?: Record<string, unknown>) => ['clinical', 'trials', filters] as const,
  },
  supply: {
    manufacturers: (filters?: Record<string, unknown>) =>
      ['supply', 'manufacturers', filters] as const,
  },
  regulatory: {
    submissions: (filters?: Record<string, unknown>) =>
      ['regulatory', 'submissions', filters] as const,
  },
};

// Entity hooks
export function useEntity(id: string, type: string, options?: UseQueryOptions<Entity, ApiError>) {
  return useQuery<Entity, ApiError>({
    queryKey: queryKeys.entity(id, type),
    queryFn: () => apiClient.get<Entity>(`/${type.toLowerCase()}/${id}`),
    enabled: !!id && !!type,
    ...options,
  });
}

export function useEntities(
  type: string,
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Entity>, ApiError>
) {
  return useQuery<PaginatedResponse<Entity>, ApiError>({
    queryKey: queryKeys.entities(type, filters),
    queryFn: () => apiClient.get<PaginatedResponse<Entity>>(`/${type.toLowerCase()}`, { params: filters }),
    ...options,
  });
}

// Search hooks
export function useSearch(filters: SearchFilters, options?: UseQueryOptions<SearchResult[], ApiError>) {
  return useQuery<SearchResult[], ApiError>({
    queryKey: queryKeys.search(filters),
    queryFn: () => apiClient.post<SearchResult[]>('/search', filters),
    enabled: !!filters.query && filters.query.length > 0,
    ...options,
  });
}

export function useSearchSuggestions(
  query: string,
  entityType?: string,
  options?: UseQueryOptions<SearchSuggestion[], ApiError>
) {
  return useQuery<SearchSuggestion[], ApiError>({
    queryKey: queryKeys.suggestions(query, entityType),
    queryFn: () =>
      apiClient.get<SearchSuggestion[]>('/search/suggestions', {
        params: { q: query, entity_type: entityType },
      }),
    enabled: !!query && query.length > 1,
    ...options,
  });
}

// Relationship hooks
export function useRelationships(
  entityId: string,
  relationshipTypes?: string[],
  options?: UseQueryOptions<Relationship[], ApiError>
) {
  return useQuery<Relationship[], ApiError>({
    queryKey: queryKeys.relationships(entityId, relationshipTypes),
    queryFn: () =>
      apiClient.get<Relationship[]>(`/relationships/${entityId}`, {
        params: { types: relationshipTypes },
      }),
    enabled: !!entityId,
    ...options,
  });
}

export function useGraph(
  entityId: string,
  depth = 1,
  options?: UseQueryOptions<GraphData, ApiError>
) {
  return useQuery<GraphData, ApiError>({
    queryKey: queryKeys.graph(entityId, depth),
    queryFn: () => apiClient.get<GraphData>(`/graph/${entityId}`, { params: { depth } }),
    enabled: !!entityId,
    ...options,
  });
}

// R&D domain hooks
export function useCompounds(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Entity>, ApiError>
) {
  return useQuery<PaginatedResponse<Entity>, ApiError>({
    queryKey: queryKeys.rd.compounds(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Entity>>('/rd/compounds', { params: filters }),
    ...options,
  });
}

export function useTargets(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Entity>, ApiError>
) {
  return useQuery<PaginatedResponse<Entity>, ApiError>({
    queryKey: queryKeys.rd.targets(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Entity>>('/rd/targets', { params: filters }),
    ...options,
  });
}

// Clinical domain hooks
export function useTrials(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Entity>, ApiError>
) {
  return useQuery<PaginatedResponse<Entity>, ApiError>({
    queryKey: queryKeys.clinical.trials(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Entity>>('/clinical/trials', { params: filters }),
    ...options,
  });
}

// Mutation hooks
export function useSaveSearch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (search: { query: string; domain?: string }) => {
      // Save to localStorage
      const recentSearches = JSON.parse(localStorage.getItem('recentSearches') || '[]');
      const newSearch = {
        query: search.query,
        timestamp: Date.now(),
        domain: search.domain,
      };
      recentSearches.unshift(newSearch);
      // Keep only last 10 searches
      const trimmed = recentSearches.slice(0, 10);
      localStorage.setItem('recentSearches', JSON.stringify(trimmed));
      return newSearch;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.recentSearches() });
    },
  });
}

export function useClearSearches() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      localStorage.removeItem('recentSearches');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.recentSearches() });
    },
  });
}
