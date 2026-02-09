import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import {
  Agency,
  Submission,
  Approval,
  Compliance,
  Document,
  SubmissionTimeline,
  PaginatedResponse,
  ApiError,
} from './types';

// Query keys factory
export const regulatoryQueryKeys = {
  agencies: (filters?: Record<string, unknown>) => ['regulatory', 'agencies', filters] as const,
  agency: (id: string) => ['regulatory', 'agency', id] as const,
  submissions: (filters?: Record<string, unknown>) => ['regulatory', 'submissions', filters] as const,
  submission: (id: string) => ['regulatory', 'submission', id] as const,
  approvals: (filters?: Record<string, unknown>) => ['regulatory', 'approvals', filters] as const,
  approval: (id: string) => ['regulatory', 'approval', id] as const,
  documents: (filters?: Record<string, unknown>) => ['regulatory', 'documents', filters] as const,
  document: (id: string) => ['regulatory', 'document', id] as const,
  submissionTimeline: (id: string) => ['regulatory', 'submissionTimeline', id] as const,
  compliance: (entityId: string) => ['regulatory', 'compliance', entityId] as const,
  statistics: () => ['regulatory', 'statistics'] as const,
  timeline: (filters?: Record<string, unknown>) => ['regulatory', 'timeline', filters] as const,
};

// Agencies hooks
export function useAgencies(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Agency>, ApiError>
) {
  return useQuery<PaginatedResponse<Agency>, ApiError>({
    queryKey: regulatoryQueryKeys.agencies(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Agency>>('/regulatory/agencies', { params: filters }),
    ...options,
  });
}

export function useAgency(
  id: string,
  options?: UseQueryOptions<Agency, ApiError>
) {
  return useQuery<Agency, ApiError>({
    queryKey: regulatoryQueryKeys.agency(id),
    queryFn: () => apiClient.get<Agency>(`/regulatory/agencies/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Submissions hooks
export function useSubmissions(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Submission>, ApiError>
) {
  return useQuery<PaginatedResponse<Submission>, ApiError>({
    queryKey: regulatoryQueryKeys.submissions(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Submission>>('/regulatory/submissions', { params: filters }),
    ...options,
  });
}

export function useSubmission(
  id: string,
  options?: UseQueryOptions<Submission, ApiError>
) {
  return useQuery<Submission, ApiError>({
    queryKey: regulatoryQueryKeys.submission(id),
    queryFn: () => apiClient.get<Submission>(`/regulatory/submissions/${id}`),
    enabled: !!id,
    ...options,
  });
}

export function useSubmissionTimeline(
  id: string,
  options?: UseQueryOptions<SubmissionTimeline[], ApiError>
) {
  return useQuery<SubmissionTimeline[], ApiError>({
    queryKey: regulatoryQueryKeys.submissionTimeline(id),
    queryFn: () => apiClient.get<SubmissionTimeline[]>(`/regulatory/submissions/${id}/timeline`),
    enabled: !!id,
    ...options,
  });
}

export function useSubmissionApprovals(
  submissionId: string,
  options?: UseQueryOptions<Approval[], ApiError>
) {
  return useQuery<Approval[], ApiError>({
    queryKey: ['regulatory', 'submissionApprovals', submissionId] as const,
    queryFn: () => apiClient.get<Approval[]>(`/regulatory/submissions/${submissionId}/approvals`),
    enabled: !!submissionId,
    ...options,
  });
}

export function useSubmissionDocuments(
  submissionId: string,
  options?: UseQueryOptions<Document[], ApiError>
) {
  return useQuery<Document[], ApiError>({
    queryKey: ['regulatory', 'submissionDocuments', submissionId] as const,
    queryFn: () => apiClient.get<Document[]>(`/regulatory/submissions/${submissionId}/documents`),
    enabled: !!submissionId,
    ...options,
  });
}

// Approvals hooks
export function useApprovals(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Approval>, ApiError>
) {
  return useQuery<PaginatedResponse<Approval>, ApiError>({
    queryKey: regulatoryQueryKeys.approvals(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Approval>>('/regulatory/approvals', { params: filters }),
    ...options,
  });
}

export function useApproval(
  id: string,
  options?: UseQueryOptions<Approval, ApiError>
) {
  return useQuery<Approval, ApiError>({
    queryKey: regulatoryQueryKeys.approval(id),
    queryFn: () => apiClient.get<Approval>(`/regulatory/approvals/${id}`),
    enabled: !!id,
    ...options,
  });
}

export function useApprovalSubmission(
  approvalId: string,
  options?: UseQueryOptions<Submission, ApiError>
) {
  return useQuery<Submission, ApiError>({
    queryKey: ['regulatory', 'approvalSubmission', approvalId] as const,
    queryFn: () => apiClient.get<Submission>(`/regulatory/approvals/${approvalId}/submission`),
    enabled: !!approvalId,
    ...options,
  });
}

// Documents hooks
export function useDocuments(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<PaginatedResponse<Document>, ApiError>
) {
  return useQuery<PaginatedResponse<Document>, ApiError>({
    queryKey: regulatoryQueryKeys.documents(filters),
    queryFn: () => apiClient.get<PaginatedResponse<Document>>('/regulatory/documents', { params: filters }),
    ...options,
  });
}

export function useDocument(
  id: string,
  options?: UseQueryOptions<Document, ApiError>
) {
  return useQuery<Document, ApiError>({
    queryKey: regulatoryQueryKeys.document(id),
    queryFn: () => apiClient.get<Document>(`/regulatory/documents/${id}`),
    enabled: !!id,
    ...options,
  });
}

// Compliance hooks
export function useCompliance(
  entityId: string,
  options?: UseQueryOptions<Compliance[], ApiError>
) {
  return useQuery<Compliance[], ApiError>({
    queryKey: regulatoryQueryKeys.compliance(entityId),
    queryFn: () => apiClient.get<Compliance[]>(`/regulatory/compliance/${entityId}`),
    enabled: !!entityId,
    ...options,
  });
}

// Timeline hook
export function useRegulatoryTimeline(
  filters?: Record<string, unknown>,
  options?: UseQueryOptions<any, ApiError>
) {
  return useQuery<any, ApiError>({
    queryKey: regulatoryQueryKeys.timeline(filters),
    queryFn: () => apiClient.get<any>('/regulatory/timeline', { params: filters }),
    ...options,
  });
}

// Statistics hook
export function useRegulatoryStatistics(options?: UseQueryOptions<any, ApiError>) {
  return useQuery<any, ApiError>({
    queryKey: regulatoryQueryKeys.statistics(),
    queryFn: () => apiClient.get<any>('/regulatory/statistics'),
    ...options,
  });
}
