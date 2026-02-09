/**
 * Supply Chain Domain API Service
 * Handles API calls for manufacturers, facilities, and drug shortages
 */

import { apiClient } from '@/shared/api/client';
import type {
  Manufacturer,
  Facility,
  Supplier,
  Product,
  Shortage
} from './types';

// API Response Types
interface ManufacturersResponse {
  data: Manufacturer[];
  total: number;
  page: number;
  page_size: number;
}

interface ManufacturerResponse {
  data: Manufacturer;
}

interface FacilitiesResponse {
  data: Facility[];
  total: number;
}

interface ShortagesResponse {
  data: Shortage[];
  total: number;
}

interface TimelineResponse {
  data: Array<{
    date: string;
    count: number;
    category: string;
  }>;
}

// Query Parameters
interface ManufacturersQuery {
  page?: number;
  page_size?: number;
  manufacturer_type?: string;
  country?: string;
  status?: string;
  quality_score_min?: number;
  search?: string;
}

interface FacilitiesQuery {
  page?: number;
  page_size?: number;
  facility_type?: string;
  country?: string;
  certification?: string;
  manufacturer_id?: string;
}

interface ShortagesQuery {
  page?: number;
  page_size?: number;
  severity?: 'low' | 'medium' | 'high';
  status?: string;
  drug_class?: string;
  therapeutic_area?: string;
  start_date?: string;
  end_date?: string;
}

/**
 * Supply Chain API Service
 */
export const supplyChainApi = {
  /**
   * Get all manufacturers with filtering and pagination
   */
  async getManufacturers(params: ManufacturersQuery = {}): Promise<ManufacturersResponse> {
    return apiClient.get<ManufacturersResponse>('/supply/manufacturers', { params });
  },

  /**
   * Get manufacturer by ID
   */
  async getManufacturerById(id: string): Promise<ManufacturerResponse> {
    return apiClient.get<ManufacturerResponse>(`/supply/manufacturers/${id}`);
  },

  /**
   * Get manufacturer's products
   */
  async getManufacturerProducts(id: string): Promise<{ data: Product[] }> {
    return apiClient.get<{ data: Product[] }>(`/supply/manufacturers/${id}/products`);
  },

  /**
   * Get manufacturer's facilities
   */
  async getManufacturerFacilities(id: string): Promise<{ data: Facility[] }> {
    return apiClient.get<{ data: Facility[] }>(`/supply/manufacturers/${id}/facilities`);
  },

  /**
   * Get manufacturer's inspection history
   */
  async getManufacturerInspections(id: string): Promise<any> {
    return apiClient.get<any>(`/supply/manufacturers/${id}/inspections`);
  },

  /**
   * Get manufacturer's compliance actions
   */
  async getManufacturerCompliance(id: string): Promise<any> {
    return apiClient.get<any>(`/supply/manufacturers/${id}/compliance`);
  },

  /**
   * Get manufacturer's supply chain network
   */
  async getManufacturerNetwork(id: string): Promise<any> {
    return apiClient.get<any>(`/supply/manufacturers/${id}/network`);
  },

  /**
   * Get all facilities with filtering and pagination
   */
  async getFacilities(params: FacilitiesQuery = {}): Promise<FacilitiesResponse> {
    return apiClient.get<FacilitiesResponse>('/supply/facilities', { params });
  },

  /**
   * Get facility by ID
   */
  async getFacilityById(id: string): Promise<{ data: Facility }> {
    return apiClient.get<{ data: Facility }>(`/supply/facilities/${id}`);
  },

  /**
   * Get active drug shortages
   */
  async getActiveShortages(params: ShortagesQuery = {}): Promise<ShortagesResponse> {
    return apiClient.get<ShortagesResponse>('/supply/shortages', {
      params: { ...params, status: 'active' }
    });
  },

  /**
   * Get all shortages with filtering
   */
  async getShortages(params: ShortagesQuery = {}): Promise<ShortagesResponse> {
    return apiClient.get<ShortagesResponse>('/supply/shortages', { params });
  },

  /**
   * Get shortage by ID
   */
  async getShortageById(id: string): Promise<{ data: Shortage }> {
    return apiClient.get<{ data: Shortage }>(`/supply/shortages/${id}`);
  },

  /**
   * Get shortage cascade analysis
   */
  async getShortageCascade(id: string): Promise<any> {
    return apiClient.get<any>(`/supply/shortages/${id}/cascade`);
  },

  /**
   * Get supply chain timeline data
   */
  async getTimeline(params: {
    start_date?: string;
    end_date?: string;
    aggregation?: 'day' | 'week' | 'month' | 'quarter' | 'year';
  } = {}): Promise<TimelineResponse> {
    return apiClient.get<TimelineResponse>('/supply/timeline', { params });
  },

  /**
   * Get geographic distribution of manufacturers
   */
  async getGeographicDistribution(): Promise<any> {
    return apiClient.get<any>('/supply/manufacturers/geographic-distribution');
  },

  /**
   * Get shortage trends over time
   */
  async getShortageTrends(params: {
    start_date?: string;
    end_date?: string;
    drug_class?: string;
  } = {}): Promise<any> {
    return apiClient.get<any>('/supply/shortages/trends', { params });
  },

  /**
   * Get suppliers
   */
  async getSuppliers(params: {
    page?: number;
    page_size?: number;
    supplier_type?: string;
    country?: string;
  } = {}): Promise<{ data: Supplier[]; total: number }> {
    return apiClient.get<{ data: Supplier[]; total: number }>('/supply/suppliers', { params });
  },

  /**
   * Get supplier by ID
   */
  async getSupplierById(id: string): Promise<{ data: Supplier }> {
    return apiClient.get<{ data: Supplier }>(`/supply/suppliers/${id}`);
  }
};

export default supplyChainApi;
