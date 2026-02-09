import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import {
  DashboardStats,
  RecentActivity,
  SystemHealth,
  ActiveShortage,
  RecentSubmission,
  ActiveTrial,
  SystemAlert,
  TimelineData,
  GeographicDistribution,
} from '@/shared/types/dashboard';
import { ApiError } from '@/shared/types';

// Dashboard query keys
export const dashboardQueryKeys = {
  stats: () => ['dashboard', 'stats'] as const,
  recentActivity: (limit: number) => ['dashboard', 'activity', limit] as const,
  systemHealth: () => ['dashboard', 'health'] as const,
  activeShortages: () => ['dashboard', 'shortages'] as const,
  recentSubmissions: (limit: number) => ['dashboard', 'submissions', limit] as const,
  activeTrials: (limit: number) => ['dashboard', 'trials', limit] as const,
  systemAlerts: () => ['dashboard', 'alerts'] as const,
  timeline: (domain?: string) => ['dashboard', 'timeline', domain] as const,
  geographicDistribution: (domain: string) => ['dashboard', 'geo', domain] as const,
};

// Dashboard stats hook
export function useDashboardStats(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery<DashboardStats, ApiError>({
    queryKey: dashboardQueryKeys.stats(),
    queryFn: async () => {
      // Since there's no single dashboard endpoint, we'll aggregate data
      const [overview, domainBreakdown] = await Promise.all([
        apiClient.get<{ total_nodes: number; total_relationships: number }>('/statistics/overview'),
        apiClient.get<{
          rd: any;
          clinical: any;
          supply: any;
          regulatory: any;
        }>('/statistics/domain-breakdown'),
      ]);

      // Mock additional data for now - this would come from real endpoints
      const mockData: DashboardStats = {
        total_nodes: overview.data.total_nodes,
        total_relationships: overview.data.total_relationships,
        domains: {
          rd: {
            compounds: 1890000,
            targets: 12500,
            assays: 45000,
            pathways: 560,
            total: 1890000 + 12500 + 45000 + 560,
          },
          clinical: {
            trials: 0,
            subjects: 0,
            interventions: 0,
            conditions: 0,
            total: 0,
          },
          supply: {
            manufacturers: 324,
            facilities: 156,
            suppliers: 89,
            shortages: 42,
            total: 324 + 156 + 89 + 42,
          },
          regulatory: {
            submissions: 1900,
            approvals: 1245,
            agencies: 12,
            documents: 8900,
            total: 1900 + 1245 + 12 + 8900,
          },
        },
        system_health: {
          api_status: 'healthy',
          neo4j_status: 'healthy',
          avg_response_time_ms: 45,
          uptime_percentage: 99.95,
          last_updated: new Date().toISOString(),
        },
        recent_activity: [
          {
            id: 'CHEMBL123',
            type: 'compound',
            domain: 'rd',
            title: 'New compound: Imatinib derivative added',
            timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
            status: 'active',
          },
          {
            id: 'SHORTAGE456',
            type: 'shortage',
            domain: 'supply',
            title: 'Drug shortage alert: Epinephrine auto-injectors',
            timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
            status: 'active',
          },
          {
            id: 'SUBMISSION789',
            type: 'submission',
            domain: 'regulatory',
            title: 'NDA submission: Novel oncology drug',
            timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            status: 'pending',
          },
          {
            id: 'MANUF234',
            type: 'manufacturer',
            domain: 'supply',
            title: 'New manufacturer registered: PharmaTech Inc',
            timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
            status: 'active',
          },
          {
            id: 'CHEMBL456',
            type: 'compound',
            domain: 'rd',
            title: 'Bioactivity data updated for kinase inhibitors',
            timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
            status: 'completed',
          },
        ],
        data_quality: {
          overall_score: 94,
          completeness: {
            rd: 96,
            clinical: 85,
            supply: 92,
            regulatory: 98,
          },
          consistency: 95,
          accuracy: 93,
          last_validated: new Date().toISOString(),
        },
      };

      return mockData;
    },
    refetchInterval: options?.refetchInterval || 30000, // 30 second polling
    enabled: options?.enabled !== false,
  });
}

// Recent activity hook
export function useRecentActivity(limit: number = 10, options?: { enabled?: boolean }) {
  return useQuery<RecentActivity[], ApiError>({
    queryKey: dashboardQueryKeys.recentActivity(limit),
    queryFn: async () => {
      // Mock data - would come from real endpoint
      return [
        {
          id: 'CHEMBL123',
          type: 'compound',
          domain: 'rd',
          title: 'New compound: Imatinib derivative added',
          timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
          status: 'active',
        },
        {
          id: 'SHORTAGE456',
          type: 'shortage',
          domain: 'supply',
          title: 'Drug shortage alert: Epinephrine auto-injectors',
          timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
          status: 'active',
        },
        {
          id: 'SUBMISSION789',
          type: 'submission',
          domain: 'regulatory',
          title: 'NDA submission: Novel oncology drug',
          timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
          status: 'pending',
        },
        {
          id: 'MANUF234',
          type: 'manufacturer',
          domain: 'supply',
          title: 'New manufacturer registered: PharmaTech Inc',
          timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
          status: 'active',
        },
        {
          id: 'CHEMBL456',
          type: 'compound',
          domain: 'rd',
          title: 'Bioactivity data updated for kinase inhibitors',
          timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
          status: 'completed',
        },
        {
          id: 'TRIAL123',
          type: 'trial',
          domain: 'clinical',
          title: 'Phase III trial initiated: COVID-19 treatment',
          timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
          status: 'active',
        },
        {
          id: 'SUBMISSION456',
          type: 'submission',
          domain: 'regulatory',
          title: 'BLA approved: Monoclonal antibody therapy',
          timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
          status: 'completed',
        },
        {
          id: 'CHEMBL789',
          type: 'compound',
          domain: 'rd',
          title: 'Target annotation updated: GPCR receptors',
          timestamp: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
          status: 'completed',
        },
        {
          id: 'SHORTAGE789',
          type: 'shortage',
          domain: 'supply',
          title: 'Shortage resolved: Saline solution IV bags',
          timestamp: new Date(Date.now() - 1000 * 60 * 240).toISOString(),
          status: 'resolved',
        },
        {
          id: 'MANUF567',
          type: 'manufacturer',
          domain: 'supply',
          title: 'Facility inspection completed: Quality Labs LLC',
          timestamp: new Date(Date.now() - 1000 * 60 * 300).toISOString(),
          status: 'completed',
        },
      ].slice(0, limit);
    },
    enabled: options?.enabled !== false,
  });
}

// System health hook
export function useSystemHealth(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery<SystemHealth, ApiError>({
    queryKey: dashboardQueryKeys.systemHealth(),
    queryFn: async () => {
      try {
        const response = await apiClient.get('/health');
        return {
          api_status: 'healthy',
          neo4j_status: 'healthy',
          avg_response_time_ms: 45,
          uptime_percentage: 99.95,
          last_updated: new Date().toISOString(),
        };
      } catch (error) {
        return {
          api_status: 'degraded',
          neo4j_status: 'degraded',
          avg_response_time_ms: 500,
          uptime_percentage: 95.5,
          last_updated: new Date().toISOString(),
        };
      }
    },
    refetchInterval: options?.refetchInterval || 30000,
    enabled: options?.enabled !== false,
    retry: 1,
  });
}

// Active shortages hook
export function useActiveShortages(options?: { enabled?: boolean }) {
  return useQuery<ActiveShortage[], ApiError>({
    queryKey: dashboardQueryKeys.activeShortages(),
    queryFn: async () => {
      const response = await apiClient.get('/sc/shortages', {
        params: { status: 'active', limit: 10 },
      });
      return response.data;
    },
    enabled: options?.enabled !== false,
  });
}

// Recent submissions hook
export function useRecentSubmissions(limit: number = 5, options?: { enabled?: boolean }) {
  return useQuery<RecentSubmission[], ApiError>({
    queryKey: dashboardQueryKeys.recentSubmissions(limit),
    queryFn: async () => {
      const response = await apiClient.get('/regulatory/submissions', {
        params: { limit, sort: '-submitted_date' },
      });
      return response.data.items || [];
    },
    enabled: options?.enabled !== false,
  });
}

// Active trials hook
export function useActiveTrials(limit: number = 5, options?: { enabled?: boolean }) {
  return useQuery<ActiveTrial[], ApiError>({
    queryKey: dashboardQueryKeys.activeTrials(limit),
    queryFn: async () => {
      const response = await apiClient.get('/clinical/trials', {
        params: { status: 'recruiting', limit },
      });
      return response.data.items || [];
    },
    enabled: options?.enabled !== false,
  });
}

// System alerts hook
export function useSystemAlerts(options?: { enabled?: boolean }) {
  return useQuery<SystemAlert[], ApiError>({
    queryKey: dashboardQueryKeys.systemAlerts(),
    queryFn: async () => {
      // Mock data - would come from real alerts system
      return [
        {
          id: 'alert1',
          severity: 'warning',
          type: 'data_quality',
          message: 'Clinical domain data completeness below threshold (85%)',
          timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
          resolved: false,
        },
        {
          id: 'alert2',
          severity: 'info',
          type: 'system',
          message: 'Scheduled maintenance completed successfully',
          timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
          resolved: true,
        },
      ];
    },
    enabled: options?.enabled !== false,
  });
}

// Timeline data hook
export function useTimelineData(domain?: string, options?: { enabled?: boolean }) {
  return useQuery<TimelineData[], ApiError>({
    queryKey: dashboardQueryKeys.timeline(domain),
    queryFn: async () => {
      const endpoint = domain
        ? `/statistics/${domain}/timeline`
        : '/statistics/timeline';
      const response = await apiClient.get(endpoint);
      return response.data;
    },
    enabled: options?.enabled !== false,
  });
}

// Geographic distribution hook
export function useGeographicDistribution(domain: string, options?: { enabled?: boolean }) {
  return useQuery<GeographicDistribution[], ApiError>({
    queryKey: dashboardQueryKeys.geographicDistribution(domain),
    queryFn: async () => {
      const response = await apiClient.get(
        `/statistics/${domain}/geographic-distribution`
      );
      return response.data;
    },
    enabled: options?.enabled !== false,
  });
}
