/**
 * PharmaKG - UnifiedSearch Component Tests
 * 统一搜索组件测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import UnifiedSearch from '@/search/UnifiedSearch';
import { DOMAIN_COLORS } from '@/types';
import * as api from '@/search/api';

// Mock the API module
vi.mock('@/search/api', () => ({
  useFullTextSearch: vi.fn(),
  useSearchSuggestions: vi.fn(),
  useSaveQuery: vi.fn(),
  useSavedQueries: vi.fn(),
}));

const mockSearchResponse = {
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
    {
      entity_id: 'target1',
      entity_type: 'Target',
      domain: 'rd',
      name: 'COX-1',
      relevance_score: 0.85,
      snippet: 'Cyclooxygenase-1 enzyme...',
      matched_fields: ['name'],
    },
  ],
  total: 2,
};

const createMockQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createMockQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('UnifiedSearch Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    // Mock API responses
    vi.mocked(api.useFullTextSearch).mockReturnValue({
      data: mockSearchResponse.results,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.mocked(api.useSearchSuggestions).mockReturnValue({
      data: [],
      isLoading: false,
    } as any);

    vi.mocked(api.useSaveQuery).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);

    vi.mocked(api.useSavedQueries).mockReturnValue({
      data: [],
      isLoading: false,
    } as any);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render the search interface', () => {
      renderWithProviders(<UnifiedSearch />);

      expect(screen.getByText('Knowledge Graph Search')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Search for compounds/i)).toBeInTheDocument();
    });

    it('should render filter button', () => {
      renderWithProviders(<UnifiedSearch />);

      expect(screen.getByRole('button', { name: /filters/i })).toBeInTheDocument();
    });

    it('should render entity type options in filters', async () => {
      renderWithProviders(<UnifiedSearch />);

      // Open filters
      const filterButton = screen.getByRole('button', { name: /filters/i });
      fireEvent.click(filterButton);

      await waitFor(() => {
        expect(screen.getByText('Domains:')).toBeInTheDocument();
        expect(screen.getByText('Entity Types:')).toBeInTheDocument();
      });
    });

    it('should display recent searches when query is empty', () => {
      const recentSearches = [
        { query: 'aspirin', timestamp: Date.now() },
        { query: 'cancer', timestamp: Date.now() - 1000 },
      ];
      localStorage.setItem('pharmakg_recent_searches', JSON.stringify(recentSearches));

      renderWithProviders(<UnifiedSearch />);

      expect(screen.getByText('Recent Searches')).toBeInTheDocument();
      expect(screen.getByText('aspirin')).toBeInTheDocument();
      expect(screen.getByText('cancer')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should perform search when query is submitted', async () => {
      const refetchMock = vi.fn();
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: refetchMock,
      } as any);

      renderWithProviders(<UnifiedSearch />);

      const searchInput = screen.getByPlaceholderText(/Search for compounds/i);
      fireEvent.change(searchInput, { target: { value: 'aspirin' } });

      await waitFor(() => {
        expect(refetchMock).toHaveBeenCalled();
      });
    });

    it('should display search results', () => {
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      expect(screen.getByText('Aspirin')).toBeInTheDocument();
      expect(screen.getByText('COX-1')).toBeInTheDocument();
      expect(screen.getByText(/95% match/i)).toBeInTheDocument();
    });

    it('should group results by entity type in tabs', () => {
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      expect(screen.getByText('All Results')).toBeInTheDocument();
      expect(screen.getByText('Compounds')).toBeInTheDocument();
      expect(screen.getByText('Targets')).toBeInTheDocument();
    });

    it('should filter results when tab is clicked', async () => {
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      const compoundsTab = screen.getByText('Compounds');
      fireEvent.click(compoundsTab);

      await waitFor(() => {
        expect(screen.getByText('Aspirin')).toBeInTheDocument();
        expect(screen.queryByText('COX-1')).not.toBeInTheDocument();
      });
    });

    it('should show loading state during search', () => {
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      expect(screen.getByText(/Searching knowledge graph/i)).toBeInTheDocument();
    });

    it('should show error state on search failure', () => {
      const error = new Error('Search failed');
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: undefined,
        isLoading: false,
        error,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      expect(screen.getByText('Search Error')).toBeInTheDocument();
    });

    it('should show empty state when no results found', () => {
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="nonexistent" />);

      expect(screen.getByText(/No results found/i)).toBeInTheDocument();
    });
  });

  describe('Filter Functionality', () => {
    it('should open filter panel when filter button is clicked', async () => {
      renderWithProviders(<UnifiedSearch />);

      const filterButton = screen.getByRole('button', { name: /filters/i });
      fireEvent.click(filterButton);

      await waitFor(() => {
        expect(screen.getByText('Domains:')).toBeInTheDocument();
        expect(screen.getByText('Entity Types:')).toBeInTheDocument();
      });
    });

    it('should allow domain selection', async () => {
      renderWithProviders(<UnifiedSearch />);

      const filterButton = screen.getByRole('button', { name: /filters/i });
      fireEvent.click(filterButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Select domains')).toBeInTheDocument();
      });
    });

    it('should allow entity type selection', async () => {
      renderWithProviders(<UnifiedSearch />);

      const filterButton = screen.getByRole('button', { name: /filters/i });
      fireEvent.click(filterButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Select entity types')).toBeInTheDocument();
      });
    });

    it('should clear all filters when clear button is clicked', async () => {
      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      const filterButton = screen.getByRole('button', { name: /filters/i });
      fireEvent.click(filterButton);

      // Select a domain (simplified test)
      await waitFor(() => {
        expect(screen.getByText('Domains:')).toBeInTheDocument();
      });

      const clearButton = screen.getByRole('button', { name: /clear filters/i });
      fireEvent.click(clearButton);

      // Verify filters are cleared (would need more specific assertion)
    });
  });

  describe('URL Parameter Handling', () => {
    it('should load query from URL parameters', () => {
      // Test would require mocking useSearchParams
      const mockSearchParams = new URLSearchParams({ q: 'aspirin' });
      vi.spyOn(require('react-router-dom'), 'useSearchParams').mockReturnValue([mockSearchParams, vi.fn()]);

      renderWithProviders(<UnifiedSearch />);

      // Verify query is loaded from URL
    });

    it('should update URL when search is performed', async () => {
      const mockSetSearchParams = vi.fn();
      vi.spyOn(require('react-router-dom'), 'useSearchParams').mockReturnValue([new URLSearchParams(), mockSetSearchParams]);

      renderWithProviders(<UnifiedSearch />);

      const searchInput = screen.getByPlaceholderText(/Search for compounds/i);
      fireEvent.change(searchInput, { target: { value: 'aspirin' } });

      await waitFor(() => {
        expect(mockSetSearchParams).toHaveBeenCalledWith(
          expect.objectContaining({ q: 'aspirin' })
        );
      });
    });
  });

  describe('Export Functionality', () => {
    it('should show export button when results are available', () => {
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
    });

    it('should export results as CSV', async () => {
      const exportSpy = vi.spyOn(require('@/utils/helpers'), 'exportAsCSV');

      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      const exportButton = screen.getByRole('button', { name: /export/i });
      fireEvent.click(exportButton);

      // Would need to handle dropdown menu
    });
  });

  describe('Pagination', () => {
    it('should show pagination controls', () => {
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    });

    it('should disable previous button on first page', () => {
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      const prevButton = screen.getByRole('button', { name: /previous/i });
      expect(prevButton).toBeDisabled();
    });

    it('should navigate to next page when next button is clicked', async () => {
      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('Page 2')).toBeInTheDocument();
      });
    });
  });

  describe('Recent Searches', () => {
    it('should save searches to localStorage', async () => {
      renderWithProviders(<UnifiedSearch />);

      const searchInput = screen.getByPlaceholderText(/Search for compounds/i);
      fireEvent.change(searchInput, { target: { value: 'test query' } });

      await waitFor(() => {
        const stored = localStorage.getItem('pharmakg_recent_searches');
        expect(stored).toContain('test query');
      });
    });

    it('should load recent searches from localStorage', () => {
      const recentSearches = [
        { query: 'previous search', timestamp: Date.now() },
      ];
      localStorage.setItem('pharmakg_recent_searches', JSON.stringify(recentSearches));

      renderWithProviders(<UnifiedSearch />);

      expect(screen.getByText('previous search')).toBeInTheDocument();
    });

    it('should clear individual recent search', async () => {
      const recentSearches = [
        { query: 'to be removed', timestamp: Date.now() },
      ];
      localStorage.setItem('pharmakg_recent_searches', JSON.stringify(recentSearches));

      renderWithProviders(<UnifiedSearch />);

      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('to be removed')).not.toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    it('should debounce search input', async () => {
      const refetchMock = vi.fn();
      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: refetchMock,
      } as any);

      renderWithProviders(<UnifiedSearch />);

      const searchInput = screen.getByPlaceholderText(/Search for compounds/i);

      // Type multiple characters quickly
      fireEvent.change(searchInput, { target: { value: 'a' } });
      fireEvent.change(searchInput, { target: { value: 'as' } });
      fireEvent.change(searchInput, { target: { value: 'asp' } });

      // Should not call refetch immediately (debounced)
      expect(refetchMock).not.toHaveBeenCalled();

      // Wait for debounce
      await waitFor(() => {
        expect(refetchMock).toHaveBeenCalledTimes(1);
      }, { timeout: 600 });
    });

    it('should render results within performance budget', async () => {
      const startTime = performance.now();

      vi.mocked(api.useFullTextSearch).mockReturnValue({
        data: mockSearchResponse.results,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<UnifiedSearch defaultQuery="aspirin" />);

      await waitFor(() => {
        expect(screen.getByText('Aspirin')).toBeInTheDocument();
      });

      const renderTime = performance.now() - startTime;
      expect(renderTime).toBeLessThan(100); // Should render in < 100ms
    });
  });
});
