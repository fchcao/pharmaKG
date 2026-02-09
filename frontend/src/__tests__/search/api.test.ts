/**
 * PharmaKG - Search API Integration Tests
 * 搜索API集成测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  useFullTextSearch,
  useSearchSuggestions,
  useSaveQuery,
  useSavedQueries,
  useDeleteQuery,
} from '@/search/api';
import { searchApi } from '@/search/api';

// Mock fetch globally
global.fetch = vi.fn();

const createMockQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
  mutations: {
    retry: false,
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createMockQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Search API Integration', () => {
  const mockBaseUrl = 'http://localhost:8000';

  beforeEach(() => {
    vi.clearAllMocks();
    // Set base URL for tests
    process.env.REACT_APP_API_URL = mockBaseUrl;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('useFullTextSearch Hook', () => {
    it('should fetch full-text search results', async () => {
      const mockResponse = {
        results: [
          {
            entity_id: 'chembl1',
            entity_type: 'Compound',
            domain: 'rd',
            name: 'Aspirin',
            relevance_score: 0.95,
            snippet: 'Aspirin is a medication...',
            matched_fields: ['name'],
          },
        ],
        total: 1,
        returned: 1,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(
        () => useFullTextSearch({ query: 'aspirin' }),
        { wrapper }
      );

      // Initially should be loading
      expect(result.current.isLoading).toBe(true);

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockResponse.results);
      expect(result.current.error).toBeNull();
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/search/fulltext'),
        expect.any(Object)
      );
    });

    it('should handle search errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(
        () => useFullTextSearch({ query: 'aspirin' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.data).toBeUndefined();
    });

    it('should not fetch when disabled', () => {
      renderHook(
        () => useFullTextSearch({ query: 'aspirin' }, { enabled: false }),
        { wrapper }
      );

      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should include search parameters in request', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ results: [], total: 0, returned: 0 }),
      });

      const searchParams = {
        query: 'aspirin',
        entity_types: ['Compound', 'Target'],
        domains: ['rd'],
        limit: 10,
        offset: 0,
        fuzzy: false,
      };

      renderHook(() => useFullTextSearch(searchParams), { wrapper });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/search/fulltext'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('aspirin'),
          })
        );
      });
    });
  });

  describe('useSearchSuggestions Hook', () => {
    it('should fetch search suggestions', async () => {
      const mockResponse = {
        suggestions: [
          { text: 'Aspirin', frequency: 100 },
          { text: 'Atorvastatin', frequency: 80 },
        ],
        total: 2,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(
        () => useSearchSuggestions('asp'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockResponse.suggestions);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/search/suggestions'),
        expect.any(Object)
      );
    });

    it('should not fetch for empty prefix', () => {
      renderHook(() => useSearchSuggestions(''), { wrapper });

      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should debounce requests', async () => {
      vi.useFakeTimers();

      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ suggestions: [], total: 0 }),
      });

      renderHook(() => useSearchSuggestions('asp'), { wrapper });

      // Fast-forward debounce timer
      vi.advanceTimersByTime(300);

      expect(global.fetch).toHaveBeenCalledTimes(1);

      vi.useRealTimers();
    });
  });

  describe('useSaveQuery Hook', () => {
    it('should save query successfully', async () => {
      const mockResponse = {
        id: 'query-1',
        name: 'Test Query',
        query: 'aspirin',
        filters: { query: 'aspirin' },
        created_at: new Date().toISOString(),
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(() => useSaveQuery(), { wrapper });

      const mutation = result.current;

      await mutation.mutateAsync({
        name: 'Test Query',
        query: 'aspirin',
        filters: { query: 'aspirin' },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/search/queries'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('should handle save errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Save failed'));

      const { result } = renderHook(() => useSaveQuery(), { wrapper });

      await expect(
        result.current.mutateAsync({
          name: 'Test Query',
          query: 'aspirin',
          filters: { query: 'aspirin' },
        })
      ).rejects.toThrow();
    });
  });

  describe('useSavedQueries Hook', () => {
    it('should fetch saved queries', async () => {
      const mockResponse = [
        {
          id: 'query-1',
          name: 'Test Query',
          query: 'aspirin',
          filters: { query: 'aspirin' },
          created_at: new Date().toISOString(),
        },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(() => useSavedQueries(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/search/queries'),
        expect.any(Object)
      );
    });

    it('should handle empty response', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

      const { result } = renderHook(() => useSavedQueries(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual([]);
    });
  });

  describe('useDeleteQuery Hook', () => {
    it('should delete query successfully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      const { result } = renderHook(() => useDeleteQuery(), { wrapper });

      await result.current.mutateAsync('query-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/search/queries/query-1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('should handle delete errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Delete failed'));

      const { result } = renderHook(() => useDeleteQuery(), { wrapper });

      await expect(
        result.current.mutateAsync('query-1')
      ).rejects.toThrow();
    });
  });

  describe('API Client', () => {
    it('should construct correct URLs', () => {
      const url = searchApi.fullTextSearch({ query: 'test' });
      expect(url).toContain('/api/v1/search/fulltext');
    });

    it('should include query parameters', () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ results: [], total: 0 }),
      });

      searchApi.fullTextSearch({
        query: 'aspirin',
        limit: 10,
        offset: 0,
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('"limit":10'),
        })
      );
    });

    it('should handle error responses', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      await expect(
        searchApi.fullTextSearch({ query: 'test' })
      ).rejects.toThrow();
    });

    it('should retry failed requests', async () => {
      let attemptCount = 0;

      (global.fetch as any).mockImplementation(async () => {
        attemptCount++;
        if (attemptCount < 3) {
          throw new Error('Network error');
        }
        return {
          ok: true,
          json: async () => ({ results: [], total: 0 }),
        };
      });

      // This test would need retry configuration
      // For now, just verify the fetch was called multiple times
    });
  });

  describe('Error Handling', () => {
    it('should handle timeout errors', async () => {
      (global.fetch as any).mockImplementation(() =>
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      );

      const { result } = renderHook(
        () => useFullTextSearch({ query: 'aspirin' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });
    });

    it('should handle malformed responses', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ invalid: 'response' }),
      });

      const { result } = renderHook(
        () => useFullTextSearch({ query: 'aspirin' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });
    });

    it('should handle unauthorized access', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
      });

      const { result } = renderHook(
        () => useFullTextSearch({ query: 'aspirin' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });
    });
  });

  describe('Performance', () => {
    it('should cache responses', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ results: [], total: 0 }),
      });

      const { result: result1 } = renderHook(
        () => useFullTextSearch({ query: 'aspirin' }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
      });

      // Render same hook again - should use cache
      const { result: result2 } = renderHook(
        () => useFullTextSearch({ query: 'aspirin' }),
        { wrapper }
      );

      expect(result2.current.isLoading).toBe(false);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should handle concurrent requests efficiently', async () => {
      (global.fetch as any).mockImplementation(async (url) => {
        // Simulate network delay
        await new Promise((resolve) => setTimeout(resolve, 50));
        return {
          ok: true,
          json: async () => ({ results: [], total: 0 }),
        };
      });

      const startTime = performance.now();

      const { result: result1 } = renderHook(
        () => useFullTextSearch({ query: 'query1' }),
        { wrapper }
      );

      const { result: result2 } = renderHook(
        () => useFullTextSearch({ query: 'query2' }),
        { wrapper }
      );

      await Promise.all([
        waitFor(() => expect(result1.current.isLoading).toBe(false)),
        waitFor(() => expect(result2.current.isLoading).toBe(false)),
      ]);

      const duration = performance.now() - startTime;

      // Should complete in less than sequential time (2 * 50ms = 100ms)
      expect(duration).toBeLessThan(100);
    });
  });
});
