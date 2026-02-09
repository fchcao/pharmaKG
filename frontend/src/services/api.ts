/**
 * API client service for PharmaKG
 * Handles all HTTP requests to the backend API
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// API base URL - adjust for your environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // Server responded with error status
          console.error('API Error:', error.response.data);
          return Promise.reject(error);
        } else if (error.request) {
          // Request was made but no response received
          console.error('Network Error:', error.request);
          return Promise.reject(new Error('Network error. Please check your connection.'));
        } else {
          // Error in setting up request
          console.error('Request Error:', error.message);
          return Promise.reject(error);
        }
      }
    );
  }

  /**
   * Make a GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  /**
   * Make a POST request
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  /**
   * Make a PUT request
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  /**
   * Make a DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }

  /**
   * Health check
   */
  async healthCheck() {
    return this.get('/health');
  }

  /**
   * Get overview stats
   */
  async getOverview() {
    return this.get('/overview');
  }

  // R&D Domain endpoints

  /**
   * Get compound by ID
   */
  async getCompound(compoundId: string) {
    return this.get(`/rd/compounds/${compoundId}`);
  }

  /**
   * Search compounds
   */
  async searchCompounds(params?: any) {
    return this.get('/rd/compounds', { params });
  }

  /**
   * Get target by ID
   */
  async getTarget(targetId: string) {
    return this.get(`/rd/targets/${targetId}`);
  }

  /**
   * Search targets
   */
  async searchTargets(params?: any) {
    return this.get('/rd/targets', { params });
  }

  /**
   * Get pathway by ID
   */
  async getPathway(pathwayId: string) {
    return this.get(`/rd/pathways/${pathwayId}`);
  }

  // Clinical Domain endpoints

  /**
   * Get clinical trial by ID
   */
  async getTrial(trialId: string) {
    return this.get(`/clinical/trials/${trialId}`);
  }

  /**
   * Search clinical trials
   */
  async searchTrials(params?: any) {
    return this.get('/clinical/trials', { params });
  }

  /**
   * Get condition by ID
   */
  async getCondition(conditionId: string) {
    return this.get(`/clinical/conditions/${conditionId}`);
  }

  // Supply Chain endpoints

  /**
   * Get manufacturer by ID
   */
  async getManufacturer(manufacturerId: string) {
    return this.get(`/supply/manufacturers/${manufacturerId}`);
  }

  /**
   * Search manufacturers
   */
  async searchManufacturers(params?: any) {
    return this.get('/supply/manufacturers', { params });
  }

  /**
   * Get drug shortages
   */
  async getDrugShortages(params?: any) {
    return this.get('/supply/shortages', { params });
  }

  // Regulatory endpoints

  /**
   * Get submission by ID
   */
  async getSubmission(submissionId: string) {
    return this.get(`/regulatory/submissions/${submissionId}`);
  }

  /**
   * Search submissions
   */
  async searchSubmissions(params?: any) {
    return this.get('/regulatory/submissions', { params });
  }

  /**
   * Get approval by ID
   */
  async getApproval(approvalId: string) {
    return this.get(`/regulatory/approvals/${approvalId}`);
  }

  // Advanced Query endpoints

  /**
   * Find shortest path between entities
   */
  async findShortestPath(params: {
    start_entity_type: string;
    start_entity_id?: string;
    end_entity_type: string;
    end_entity_id?: string;
    max_path_length?: number;
    relationship_types?: string;
  }) {
    return this.get('/advanced/path/shortest', { params });
  }

  /**
   * Multi-hop query
   */
  async multiHopQuery(params: any) {
    return this.get('/advanced/multi-hop', { params });
  }

  /**
   * Get subgraph data
   */
  async getSubgraph(entityId: string, params?: any) {
    return this.get(`/advanced/subgraph/${entityId}`, { params });
  }

  /**
   * Get compound repurposing opportunities
   */
  async getCompoundRepurposing(compoundId: string, params?: any) {
    return this.get(`/advanced/compounds/${compoundId}/repurposing-opportunities`, { params });
  }

  /**
   * Get disease competitive landscape
   */
  async getDiseaseCompetitiveLandscape(diseaseId: string, params?: any) {
    return this.get(`/advanced/diseases/${diseaseId}/competitive-landscape`, { params });
  }

  /**
   * Get target competitive landscape
   */
  async getTargetCompetitiveLandscape(targetId: string, params?: any) {
    return this.get(`/advanced/targets/${targetId}/competitive-landscape`, { params });
  }

  /**
   * Get compound safety profile
   */
  async getCompoundSafetyProfile(compoundId: string, params?: any) {
    return this.get(`/advanced/compounds/${compoundId}/safety-profile`, { params });
  }

  /**
   * Get manufacturer supply chain impact
   */
  async getSupplyChainImpact(manufacturerId: string, params?: any) {
    return this.get(`/advanced/manufacturers/${manufacturerId}/supply-chain-impact`, { params });
  }

  // Search endpoints

  /**
   * Full text search
   */
  async fullTextSearch(query: string, params?: any) {
    return this.post('/search/fulltext', { query, ...params });
  }

  /**
   * Fuzzy search
   */
  async fuzzySearch(query: string, params?: any) {
    return this.post('/search/fuzzy', { query, ...params });
  }

  /**
   * Get search suggestions
   */
  async getSuggestions(query: string, params?: any) {
    return this.post('/search/suggestions', { query, ...params });
  }

  // Graph Analytics endpoints

  /**
   * Get centrality measures
   */
  async getCentrality(entityId: string, params?: any) {
    return this.get(`/analytics/centrality/${entityId}`, { params });
  }

  /**
   * Get community detection
   */
  async getCommunities(params?: any) {
    return this.get('/analytics/communities', { params });
  }

  /**
   * Get shortest path
   */
  async getShortestPath(startId: string, endId: string, params?: any) {
    return this.get(`/analytics/path/${startId}/${endId}`, { params });
  }
}

// Create and export singleton instance
const api = new ApiClient();
export default api;
