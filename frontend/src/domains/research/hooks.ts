import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import {
  Compound,
  Target,
  Assay,
  Pathway,
  BioactivityData,
  PaginatedResponse,
  ApiError,
} from './types';

// Query keys factory
export const rdQueryKeys = {
  compounds: (filters?: Record<string, unknown>) => ['rd', 'compounds', filters] as const,
  compound: (id: string) => ['rd', 'compound', id] as const,
  targets: (filters?: Record<string, unknown>) => ['rd', 'targets', filters] as const,
  target: (id: string) => ['rd', 'target', id] as const,
  assays: (filters?: Record<string, unknown>) => ['rd', 'assays', filters] as const,
  assay: (id: string) => ['rd', 'assay', id] as const,
  pathways: (filters?: Record<string, unknown>) => ['rd', 'pathways', filters] as const,
  pathway: (id: string) => ['rd', 'pathway', id] as const,
  bioactivities: (compoundId: string) => ['rd', 'bioactivities', compoundId] as const,
  compoundTargets: (compoundId: string) => ['rd', 'compoundTargets', compoundId] as const,
  targetCompounds: (targetId: string) => ['rd', 'targetCompounds', targetId] as const,
  targetPathways: (targetId: string) => ['rd', 'targetPathways', targetId] as const,
  statistics: () => ['rd', 'statistics'] as const,
};

// Compounds hooks
export function useCompounds(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Compound>, ApiError>
) {
  return useQuery<PaginatedResponse<Compound>, ApiError>({
    queryKey: rdQueryKeys.compounds(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Compound>>('/rd/compounds', { params: filters }),
    ...options,
  });
}

export function useCompound(
  id: string,
  options?: UseQueryOptions<Compound, ApiError>
) {
  return useQuery<Compound, ApiError>({
    queryKey: rdQueryKeys.compound(id),
    queryFn: () => apiClient.get<Compound>(`/rd/compounds/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Targets hooks
export function useTargets(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Target>, ApiError>
) {
  return useQuery<PaginatedResponse<Target>, ApiError>({
    queryKey: rdQueryKeys.targets(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Target>>('/rd/targets', { params: filters }),
    ...options,
  });
}

export function useTarget(
  id: string,
  options?: UseQueryOptions<Target, ApiError>
) {
  return useQuery<Target, ApiError>({
    queryKey: rdQueryKeys.target(id),
    queryFn: () => apiClient.get<Target>(`/rd/targets/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Assays hooks - Note: Backend doesn't have this endpoint yet, returning empty data
export function useAssays(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Assay>, ApiError>
) {
  return useQuery<PaginatedResponse<Assay>, ApiError>({
    queryKey: rdQueryKeys.assays(filters),
    queryFn: async () => {
      try {
        return await apiClient.get<PaginatedResponse<Assay>>('/rd/assays', { params: filters });
      } catch {
        return { items: [], total: 0, page: 1, pageSize: 20 };
      }
    },
    ...options,
  });
}

export function useAssay(
  id: string,
  options?: UseQueryOptions<Assay, ApiError>
) {
  return useQuery<Assay, ApiError>({
    queryKey: rdQueryKeys.assay(id),
    queryFn: async () => {
      try {
        return await apiClient.get<Assay>(`/rd/assays/${id}`);
      } catch {
        return null;
      }
    },
    enabled: !!id,
    ...options,
  });
}

// Pathways hooks - Note: Backend doesn't have this endpoint yet, returning empty data
export function usePathways(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Pathway>, ApiError>
) {
  return useQuery<PaginatedResponse<Pathway>, ApiError>({
    queryKey: rdQueryKeys.pathways(filters),
    queryFn: async () => {
      try {
        return await apiClient.get<PaginatedResponse<Pathway>>('/rd/pathways', { params: filters });
      } catch {
        return { items: [], total: 0, page: 1, pageSize: 20 };
      }
    },
    ...options,
  });
}

export function usePathway(
  id: string,
  options?: UseQueryOptions<Pathway, ApiError>
) {
  return useQuery<Pathway, ApiError>({
    queryKey: rdQueryKeys.pathway(id),
    queryFn: async () => {
      try {
        return await apiClient.get<Pathway>(`/rd/pathways/${id}`);
      } catch {
        return null;
      }
    },
    enabled: !!id,
    ...options,
  });
}

// Relationship hooks
export function useCompoundTargets(
  compoundId: string,
  options?: UseQueryOptions<Target[], ApiError>
) {
  return useQuery<Target[], ApiError>({
    queryKey: rdQueryKeys.compoundTargets(compoundId),
    queryFn: () => apiClient.get<Target[]>(`/rd/compounds/${compoundId}/targets`),
    enabled: !!compoundId,
    ...options,
  });
}

export function useTargetCompounds(
  targetId: string,
  options?: UseQueryOptions<Compound[], ApiError>
) {
  return useQuery<Compound[], ApiError>({
    queryKey: rdQueryKeys.targetCompounds(targetId),
    queryFn: () => apiClient.get<Compound[]>(`/rd/targets/${targetId}/compounds`),
    enabled: !!targetId,
    ...options,
  });
}

// Bioactivities - Note: Backend doesn't have this endpoint yet, returning empty data
export function useBioactivities(
  compoundId: string,
  options?: UseQueryOptions<BioactivityData[], ApiError>
) {
  return useQuery<BioactivityData[], ApiError>({
    queryKey: rdQueryKeys.bioactivities(compoundId),
    queryFn: async () => {
      try {
        return await apiClient.get<BioactivityData[]>(`/rd/compounds/${compoundId}/bioactivities`);
      } catch {
        return [];
      }
    },
    enabled: !!compoundId,
    ...options,
  });
}

// Target pathways - Note: Backend doesn't have this endpoint yet, returning empty data
export function useTargetPathways(
  targetId: string,
  options?: UseQueryOptions<Pathway[], ApiError>
) {
  return useQuery<Pathway[], ApiError>({
    queryKey: rdQueryKeys.targetPathways(targetId),
    queryFn: async () => {
      try {
        return await apiClient.get<Pathway[]>(`/rd/targets/${targetId}/pathways`);
      } catch {
        return [];
      }
    },
    enabled: !!targetId,
    ...options,
  });
}

// Statistics hook
export function useRDStatistics(options?: UseQueryOptions<any, ApiError>) {
  return useQuery<any, ApiError>({
    queryKey: rdQueryKeys.statistics(),
    queryFn: () => apiClient.get<any>('/rd/statistics'),
    ...options,
  });
}
