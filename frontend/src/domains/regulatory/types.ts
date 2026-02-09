// Regulatory Domain specific types

export interface Agency {
  id: string;
  name: string;
  country: string;
  type: string;
  jurisdiction?: string[];
}

export interface Submission {
  id: string;
  submissionType: string;
  submissionNumber: string;
  submissionDate?: string;
  status?: string;
  agencyId: string;
  drugId?: string;
  drugName?: string;
  reviewDate?: string;
  approvalDate?: string;
  agency?: Agency;
  relatedDrugs?: RelatedDrug[];
  relatedDocuments?: Document[];
  complianceStatus?: ComplianceStatus;
}

export interface RelatedDrug {
  id: string;
  name: string;
  type: string;
}

export interface ComplianceStatus {
  status: 'compliant' | 'warning' | 'non-compliant' | 'pending';
  lastReviewDate?: string;
  findingsCount?: number;
}

export interface Approval {
  id: string;
  submissionId: string;
  approvalNumber: string;
  approvalDate: string;
  approvalType: string;
  conditions?: string[];
  expiryDate?: string;
  therapeuticArea?: string;
  drugName?: string;
  agencyName?: string;
  submission?: Submission;
  postApprovalRequirements?: PostApprovalRequirement[];
}

export interface PostApprovalRequirement {
  id: string;
  requirement: string;
  dueDate?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
}

export interface Document {
  id: string;
  title: string;
  documentType: string;
  agencyId?: string;
  submissionId?: string;
  documentDate?: string;
  confidentiality?: string;
  url?: string;
  summary?: string;
  pages?: number;
  fileSize?: number;
  format?: string;
}

export interface SubmissionTimeline {
  id: string;
  eventType: string;
  eventDate: string;
  description: string;
  status?: string;
  decision?: string;
  nextSteps?: string[];
}

export interface Compliance {
  id: string;
  entityId: string;
  entityType: string;
  complianceType: string;
  status: string;
  lastReviewDate?: string;
  nextReviewDate?: string;
  findings?: Finding[];
}

export interface Finding {
  id: string;
  complianceId: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  description: string;
  status: string;
  dueDate?: string;
}

export interface TimelineDataPoint {
  date: string;
  count: number;
  category?: string;
}

// Filter types
export interface SubmissionFilters {
  agency?: string;
  type?: string;
  status?: string;
  startDate?: string;
  endDate?: string;
  drug?: string;
  page?: number;
  pageSize?: number;
}

export interface ApprovalFilters {
  agency?: string;
  startDate?: string;
  endDate?: string;
  drug?: string;
  therapeuticArea?: string;
  approvalType?: string;
  page?: number;
  pageSize?: number;
}

export interface DocumentFilters {
  type?: string;
  agency?: string;
  startDate?: string;
  endDate?: string;
  submissionId?: string;
  page?: number;
  pageSize?: number;
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// API error type
export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// Statistics types
export interface RegulatoryStatistics {
  totalSubmissions: number;
  totalApprovals: number;
  totalDocuments: number;
  pendingSubmissions: number;
  approvedSubmissions: number;
  rejectedSubmissions: number;
  submissionsByAgency: Record<string, number>;
  submissionsByType: Record<string, number>;
  approvalsByYear: Record<string, number>;
  averageReviewTime: number;
  complianceRate: number;
}
