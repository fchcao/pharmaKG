import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import {
  ClinicalTrial,
  Subject,
  Intervention,
  Outcome,
  Location,
  Condition,
  PaginatedResponse,
  ApiError,
} from './types';

// Query keys factory
export const clinicalQueryKeys = {
  trials: (filters?: Record<string, unknown>) => ['clinical', 'trials', filters] as const,
  trial: (id: string) => ['clinical', 'trial', id] as const,
  subjects: (filters?: Record<string, unknown>) => ['clinical', 'subjects', filters] as const,
  subject: (id: string) => ['clinical', 'subject', id] as const,
  interventions: (filters?: Record<string, unknown>) => ['clinical', 'interventions', filters] as const,
  intervention: (id: string) => ['clinical', 'intervention', id] as const,
  outcomes: (filters?: Record<string, unknown>) => ['clinical', 'outcomes', filters] as const,
  outcome: (id: string) => ['clinical', 'outcome', id] as const,
  conditions: (filters?: Record<string, unknown>) => ['clinical', 'conditions', filters] as const,
  condition: (id: string) => ['clinical', 'condition', id] as const,
  locations: (trialId: string) => ['clinical', 'locations', trialId] as const,
  trialSubjects: (trialId: string) => ['clinical', 'trialSubjects', trialId] as const,
  trialInterventions: (trialId: string) => ['clinical', 'trialInterventions', trialId] as const,
  trialOutcomes: (trialId: string) => ['clinical', 'trialOutcomes', trialId] as const,
  statistics: () => ['clinical', 'statistics'] as const,
  timeline: (trialId: string) => ['clinical', 'timeline', trialId] as const,
};

// Clinical Trials hooks
export function useTrials(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<ClinicalTrial>, ApiError>
) {
  return useQuery<PaginatedResponse<ClinicalTrial>, ApiError>({
    queryKey: clinicalQueryKeys.trials(filters),
    queryFn: () => apiClient.get<PaginatedResponse<ClinicalTrial>>('/clinical/trials', { params: filters }),
    ...options,
  });
}

export function useTrial(
  id: string,
  options?: UseQueryOptions<ClinicalTrial, ApiError>
) {
  return useQuery<ClinicalTrial, ApiError>({
    queryKey: clinicalQueryKeys.trial(id),
    queryFn: () => apiClient.get<ClinicalTrial>(`/clinical/trials/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Subjects hooks
export function useSubjects(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Subject>, ApiError>
) {
  return useQuery<PaginatedResponse<Subject>, ApiError>({
    queryKey: clinicalQueryKeys.subjects(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Subject>>('/clinical/subjects', { params: filters }),
    ...options,
  });
}

export function useSubject(
  id: string,
  options?: UseQueryOptions<Subject, ApiError>
) {
  return useQuery<Subject, ApiError>({
    queryKey: clinicalQueryKeys.subject(id),
    queryFn: () => apiClient.get<Subject>(`/clinical/subjects/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Interventions hooks
export function useInterventions(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Intervention>, ApiError>
) {
  return useQuery<PaginatedResponse<Intervention>, ApiError>({
    queryKey: clinicalQueryKeys.interventions(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Intervention>>('/clinical/interventions', { params: filters }),
    ...options,
  });
}

export function useIntervention(
  id: string,
  options?: UseQueryOptions<Intervention, ApiError>
) {
  return useQuery<Intervention, ApiError>({
    queryKey: clinicalQueryKeys.intervention(id),
    queryFn: () => apiClient.get<Intervention>(`/clinical/interventions/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Outcomes hooks
export function useOutcomes(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Outcome>, ApiError>
) {
  return useQuery<PaginatedResponse<Outcome>, ApiError>({
    queryKey: clinicalQueryKeys.outcomes(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Outcome>>('/clinical/outcomes', { params: filters }),
    ...options,
  });
}

export function useOutcome(
  id: string,
  options?: UseQueryOptions<Outcome, ApiError>
) {
  return useQuery<Outcome, ApiError>({
    queryKey: clinicalQueryKeys.outcome(id),
    queryFn: () => apiClient.get<Outcome>(`/clinical/outcomes/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Conditions hooks
export function useConditions(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Condition>, ApiError>
) {
  return useQuery<PaginatedResponse<Condition>, ApiError>({
    queryKey: clinicalQueryKeys.conditions(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Condition>>('/clinical/conditions', { params: filters }),
    ...options,
  });
}

export function useCondition(
  id: string,
  options?: UseQueryOptions<Condition, ApiError>
) {
  return useQuery<Condition, ApiError>({
    queryKey: clinicalQueryKeys.condition(id),
    queryFn: () => apiClient.get<Condition>(`/clinical/conditions/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Relationship hooks
export function useTrialSubjects(
  trialId: string,
  options?: UseQueryOptions<Subject[], ApiError>
) {
  return useQuery<Subject[], ApiError>({
    queryKey: clinicalQueryKeys.trialSubjects(trialId),
    queryFn: () => apiClient.get<Subject[]>(`/clinical/trials/${trialId}/subjects`),
    enabled: !!trialId,
    ...options,
  });
}

export function useTrialInterventions(
  trialId: string,
  options?: UseQueryOptions<Intervention[], ApiError>
) {
  return useQuery<Intervention[], ApiError>({
    queryKey: clinicalQueryKeys.trialInterventions(trialId),
    queryFn: () => apiClient.get<Intervention[]>(`/clinical/trials/${trialId}/interventions`),
    enabled: !!trialId,
    ...options,
  });
}

export function useTrialOutcomes(
  trialId: string,
  options?: UseQueryOptions<Outcome[], ApiError>
) {
  return useQuery<Outcome[], ApiError>({
    queryKey: clinicalQueryKeys.trialOutcomes(trialId),
    queryFn: () => apiClient.get<Outcome[]>(`/clinical/trials/${trialId}/outcomes`),
    enabled: !!trialId,
    ...options,
  });
}

export function useTrialLocations(
  trialId: string,
  options?: UseQueryOptions<Location[], ApiError>
) {
  return useQuery<Location[], ApiError>({
    queryKey: clinicalQueryKeys.locations(trialId),
    queryFn: () => apiClient.get<Location[]>(`/clinical/trials/${trialId}/locations`),
    enabled: !!trialId,
    ...options,
  });
}

export function useTrialTimeline(
  trialId: string,
  options?: UseQueryOptions<any, ApiError>
) {
  return useQuery<any, ApiError>({
    queryKey: clinicalQueryKeys.timeline(trialId),
    queryFn: () => apiClient.get<any>(`/clinical/trials/${trialId}/timeline`),
    enabled: !!trialId,
    ...options,
  });
}

// Statistics hook
export function useClinicalStatistics(options?: UseQueryOptions<any, ApiError>) {
  return useQuery<any, ApiError>({
    queryKey: clinicalQueryKeys.statistics(),
    queryFn: () => apiClient.get<any>('/clinical/statistics'),
    ...options,
  });
}
