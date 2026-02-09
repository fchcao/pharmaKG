// Dashboard and Monitoring Types

export interface DashboardStats {
  total_nodes: number;
  total_relationships: number;
  domains: DomainStats;
  system_health: SystemHealth;
  recent_activity: RecentActivity[];
  data_quality: DataQualityMetrics;
}

export interface DomainStats {
  rd: {
    compounds: number;
    targets: number;
    assays: number;
    pathways: number;
    total: number;
  };
  clinical: {
    trials: number;
    subjects: number;
    interventions: number;
    conditions: number;
    total: number;
  };
  supply: {
    manufacturers: number;
    facilities: number;
    suppliers: number;
    shortages: number;
    total: number;
  };
  regulatory: {
    submissions: number;
    approvals: number;
    agencies: number;
    documents: number;
    total: number;
  };
}

export interface SystemHealth {
  api_status: 'healthy' | 'degraded' | 'down';
  neo4j_status: 'healthy' | 'degraded' | 'down';
  avg_response_time_ms: number;
  uptime_percentage: number;
  last_updated: string;
}

export interface RecentActivity {
  id: string;
  type: 'compound' | 'trial' | 'submission' | 'shortage' | 'manufacturer';
  domain: 'rd' | 'clinical' | 'supply' | 'regulatory';
  title: string;
  timestamp: string;
  status?: 'active' | 'pending' | 'completed' | 'resolved';
}

export interface DataQualityMetrics {
  overall_score: number;
  completeness: {
    rd: number;
    clinical: number;
    supply: number;
    regulatory: number;
  };
  consistency: number;
  accuracy: number;
  last_validated: string;
}

export interface TimelineData {
  date: string;
  count: number;
  domain?: string;
}

export interface GeographicDistribution {
  country: string;
  count: number;
  percentage: number;
}

export interface RelationshipTypeStats {
  type: string;
  count: number;
  domain: string;
}

export interface NetworkMetrics {
  avg_degree: number;
  diameter: number;
  avg_path_length: number;
  clustering_coefficient: number;
  connected_components: number;
}

// Monitoring specific types
export interface ActiveShortage {
  id: string;
  drug_name: string;
  severity: 'critical' | 'moderate' | 'low';
  start_date: string;
  expected_resolve_date?: string;
  affected_manufacturers: string[];
}

export interface RecentSubmission {
  id: string;
  type: string;
  sponsor: string;
  submitted_date: string;
  status: string;
  domain?: string;
}

export interface ActiveTrial {
  id: string;
  title: string;
  phase: string;
  status: string;
  enrollment: number;
  start_date: string;
}

export interface SystemAlert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  type: string;
  message: string;
  timestamp: string;
  resolved: boolean;
}
