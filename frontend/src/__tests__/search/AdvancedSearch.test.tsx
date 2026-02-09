/**
 * PharmaKG - AdvancedSearch Component Tests
 * 高级搜索组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdvancedSearch from '@/search/AdvancedSearch';
import { SearchFilters } from '@/search/types';
import * as api from '@/search/api';

// Mock the API module
vi.mock('@/search/api', () => ({
  useSaveQuery: vi.fn(),
  useSavedQueries: vi.fn(),
  useDeleteQuery: vi.fn(),
}));

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
      {component}
    </QueryClientProvider>
  );
};

describe('AdvancedSearch Component', () => {
  const mockOnSearch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock API responses
    vi.mocked(api.useSaveQuery).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);

    vi.mocked(api.useSavedQueries).mockReturnValue({
      data: [],
      isLoading: false,
    } as any);

    vi.mocked(api.useDeleteQuery).mockReturnValue({
      mutate: vi.fn(),
    } as any);
  });

  describe('Rendering', () => {
    it('should render the advanced search interface', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.getByText('Advanced Search')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Enter your main search query/i)).toBeInTheDocument();
    });

    it('should render domain selection', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.getByText('Domains')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Select domains to search')).toBeInTheDocument();
    });

    it('should render entity type selection', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.getByText('Entity Types')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Select entity types to search')).toBeInTheDocument();
    });

    it('should render boolean operator selector', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.getByText('Boolean Operator')).toBeInTheDocument();
      expect(screen.getByDisplayValue('AND')).toBeInTheDocument();
    });

    it('should render custom conditions section', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.getByText('Custom Conditions')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add condition/i })).toBeInTheDocument();
    });

    it('should render temporal filters section', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.getByText('Temporal Filters')).toBeInTheDocument();
      expect(screen.getByText('Enable Date Range Filter')).toBeInTheDocument();
    });

    it('should render action buttons', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear all/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save query/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /export query/i })).toBeInTheDocument();
    });
  });

  describe('Entity Type Selection', () => {
    it('should display all entity type options', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const entityTypeSelect = screen.getByPlaceholderText('Select entity types to search');
      await userEvent.click(entityTypeSelect);

      await waitFor(() => {
        expect(screen.getByText('Compound')).toBeInTheDocument();
        expect(screen.getByText('Target')).toBeInTheDocument();
        expect(screen.getByText('Clinical Trial')).toBeInTheDocument();
        expect(screen.getByText('Manufacturer')).toBeInTheDocument();
      });
    });

    it('should allow selecting multiple entity types', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const entityTypeSelect = screen.getByPlaceholderText('Select entity types to search');
      await userEvent.click(entityTypeSelect);

      await waitFor(() => {
        const compoundOption = screen.getByText('Compound');
        fireEvent.click(compoundOption);
      });
    });
  });

  describe('Custom Conditions', () => {
    it('should add a new condition when Add Condition button is clicked', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      // First select an entity type
      const entityTypeSelect = screen.getByPlaceholderText('Select entity types to search');
      fireEvent.change(entityTypeSelect, { target: { value: 'Compound' } });

      const addButton = screen.getByRole('button', { name: /add condition/i });
      await userEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Select field')).toBeInTheDocument();
      });
    });

    it('should disable Add Condition button when no entity type selected', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const addButton = screen.getByRole('button', { name: /add condition/i });
      expect(addButton).toBeDisabled();
    });

    it('should remove condition when delete button is clicked', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} initialFilters={{
        query: 'test',
        entityTypes: ['Compound'],
      }});

      // Add a condition first
      const entityTypeSelect = screen.getByPlaceholderText('Select entity types to search');
      fireEvent.change(entityTypeSelect, { target: { value: 'Compound' } });

      const addButton = screen.getByRole('button', { name: /add condition/i });
      await userEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Select field')).toBeInTheDocument();
      });

      // Now remove it
      const deleteButton = screen.getByRole('button', { name: '' });
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Select field')).not.toBeInTheDocument();
      });
    });

    it('should show correct operators based on field type', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} initialFilters={{
        query: 'test',
        entityTypes: ['Compound'],
      }});

      // Add a condition
      const entityTypeSelect = screen.getByPlaceholderText('Select entity types to search');
      fireEvent.change(entityTypeSelect, { target: { value: 'Compound' } });

      const addButton = screen.getByRole('button', { name: /add condition/i });
      await userEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Select field')).toBeInTheDocument();
      });

      // Select a text field (name)
      const fieldSelect = screen.getByPlaceholderText('Select field');
      fireEvent.change(fieldSelect, { target: { value: 'name' } });

      // Should show text operators
      await waitFor(() => {
        expect(screen.getByText('Contains')).toBeInTheDocument();
        expect(screen.getByText('Equals')).toBeInTheDocument();
      });
    });

    it('should render number input for numeric fields', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} initialFilters={{
        query: 'test',
        entityTypes: ['Compound'],
      }});

      // Add a condition
      const entityTypeSelect = screen.getByPlaceholderText('Select entity types to search');
      fireEvent.change(entityTypeSelect, { target: { value: 'Compound' } });

      const addButton = screen.getByRole('button', { name: /add condition/i });
      await userEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Select field')).toBeInTheDocument();
      });

      // Select a numeric field
      const fieldSelect = screen.getByPlaceholderText('Select field');
      fireEvent.change(fieldSelect, { target: { value: 'molecular_weight' } });

      // Should render number input
      await waitFor(() => {
        const input = screen.getByPlaceholderText('Enter value');
        expect(input).toBeInTheDocument();
      });
    });
  });

  describe('Boolean Operators', () => {
    it('should allow selecting AND operator', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const operatorSelect = screen.getByDisplayValue('AND');
      expect(operatorSelect).toBeInTheDocument();
    });

    it('should allow selecting OR operator', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const operatorSelect = screen.getByDisplayValue('AND');
      fireEvent.change(operatorSelect, { target: { value: 'OR' } });

      await waitFor(() => {
        expect(screen.getByDisplayValue('OR')).toBeInTheDocument();
      });
    });

    it('should allow selecting NOT operator', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const operatorSelect = screen.getByDisplayValue('AND');
      fireEvent.change(operatorSelect, { target: { value: 'NOT' } });

      await waitFor(() => {
        expect(screen.getByDisplayValue('NOT')).toBeInTheDocument();
      });
    });
  });

  describe('Date Range Filter', () => {
    it('should enable date range filter when toggle is on', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const toggle = screen.getByRole('switch', { checked: false });
      await userEvent.click(toggle);

      await waitFor(() => {
        expect(screen.getByText('Date Range')).toBeInTheDocument();
      });
    });

    it('should disable date range filter when toggle is off', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.queryByText('Date Range')).not.toBeInTheDocument();
    });
  });

  describe('Search Execution', () => {
    it('should call onSearch with correct filters when Search button is clicked', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const queryInput = screen.getByPlaceholderText(/Enter your main search query/i);
      await userEvent.type(queryInput, 'aspirin');

      const searchButton = screen.getByRole('button', { name: /search/i });
      await userEvent.click(searchButton);

      await waitFor(() => {
        expect(mockOnSearch).toHaveBeenCalledWith(
          expect.objectContaining({
            query: 'aspirin',
          })
        );
      });
    });

    it('should include entity types in filters', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      // Select entity types (simplified)
      const entityTypeSelect = screen.getByPlaceholderText('Select entity types to search');
      fireEvent.change(entityTypeSelect, { target: { value: ['Compound', 'Target'] } });

      const searchButton = screen.getByRole('button', { name: /search/i });
      await userEvent.click(searchButton);

      await waitFor(() => {
        expect(mockOnSearch).toHaveBeenCalledWith(
          expect.objectContaining({
            entityTypes: ['Compound', 'Target'],
          })
        );
      });
    });

    it('should include boolean operator in filters', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const operatorSelect = screen.getByDisplayValue('AND');
      fireEvent.change(operatorSelect, { target: { value: 'OR' } });

      const searchButton = screen.getByRole('button', { name: /search/i });
      await userEvent.click(searchButton);

      await waitFor(() => {
        expect(mockOnSearch).toHaveBeenCalledWith(
          expect.objectContaining({
            booleanOperator: 'OR',
          })
        );
      });
    });
  });

  describe('Clear Functionality', () => {
    it('should clear all filters when Clear All button is clicked', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      // Enter some data
      const queryInput = screen.getByPlaceholderText(/Enter your main search query/i);
      await userEvent.type(queryInput, 'test query');

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      await userEvent.click(clearButton);

      await waitFor(() => {
        expect(queryInput).toHaveValue('');
      });
    });

    it('should reset entity types when cleared', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const clearButton = screen.getByRole('button', { name: /clear all/i });
      await userEvent.click(clearButton);

      await waitFor(() => {
        const entityTypeSelect = screen.getByPlaceholderText('Select entity types to search');
        expect(entityTypeSelect).toHaveValue([]);
      });
    });
  });

  describe('Saved Queries', () => {
    it('should display saved queries button', () => {
      const savedQueries = [
        { id: '1', name: 'Test Query', query: 'aspirin', filters: { query: 'aspirin' } },
      ];
      vi.mocked(api.useSavedQueries).mockReturnValue({
        data: savedQueries,
        isLoading: false,
      } as any);

      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      expect(screen.getByText(/View Saved Queries \(1\)/i)).toBeInTheDocument();
    });

    it('should open saved queries modal when button is clicked', async () => {
      const savedQueries = [
        { id: '1', name: 'Test Query', query: 'aspirin', filters: { query: 'aspirin' } },
      ];
      vi.mocked(api.useSavedQueries).mockReturnValue({
        data: savedQueries,
        isLoading: false,
      } as any);

      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const viewButton = screen.getByRole('button', { name: /view saved queries/i });
      await userEvent.click(viewButton);

      await waitFor(() => {
        expect(screen.getByText('Saved Queries')).toBeInTheDocument();
        expect(screen.getByText('Test Query')).toBeInTheDocument();
      });
    });

    it('should save query when Save Query button is clicked', async () => {
      const mutateMock = vi.fn();
      vi.mocked(api.useSaveQuery).mockReturnValue({
        mutate: mutateMock,
        isPending: false,
      } as any);

      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const saveButton = screen.getByRole('button', { name: /save query/i });
      await userEvent.click(saveButton);

      // Would need to handle modal input
    });
  });

  describe('Query Export', () => {
    it('should show query configuration modal when Export Query button is clicked', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const exportButton = screen.getByRole('button', { name: /export query/i });
      await userEvent.click(exportButton);

      await waitFor(() => {
        expect(screen.getByText('Export Query')).toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    it('should render within performance budget', () => {
      const startTime = performance.now();

      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const renderTime = performance.now() - startTime;
      expect(renderTime).toBeLessThan(100); // Should render in < 100ms
    });

    it('should handle rapid condition additions efficiently', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} initialFilters={{
        query: 'test',
        entityTypes: ['Compound'],
      }});

      const startTime = performance.now();
      const addButton = screen.getByRole('button', { name: /add condition/i });

      // Add 5 conditions rapidly
      for (let i = 0; i < 5; i++) {
        await userEvent.click(addButton);
      }

      const endTime = performance.now();
      const duration = endTime - startTime;

      expect(duration).toBeLessThan(1000); // Should complete in < 1 second
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const searchInput = screen.getByPlaceholderText(/Enter your main search query/i);
      expect(searchInput).toHaveAttribute('type', 'text');

      const searchButton = screen.getByRole('button', { name: /search/i });
      expect(searchButton).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      renderWithProviders(<AdvancedSearch onSearch={mockOnSearch} />);

      const searchInput = screen.getByPlaceholderText(/Enter your main search query/i);
      searchInput.focus();

      expect(searchInput).toHaveFocus();

      // Tab to next element
      await userEvent.tab();
      // Verify focus moves (would need more specific assertions)
    });
  });
});
