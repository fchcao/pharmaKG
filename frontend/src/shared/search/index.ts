// Main search components
export { UnifiedSearch } from './UnifiedSearch';
export { AdvancedSearch } from './AdvancedSearch';
export { SearchResults } from './SearchResults';

// Search API hooks
export {
  useFullTextSearch,
  useFuzzySearch,
  useSearchSuggestions,
  useAggregateSearch,
  useMultiEntitySearch,
  useSavedQueries,
  useSaveQuery,
  useDeleteQuery,
  useUpdateQueryLastUsed,
  searchQueryKeys,
} from './api';

// Search types
export type {
  FullTextSearchRequest,
  FullTextSearchResult,
  FuzzySearchRequest,
  FuzzySearchResult,
  SearchSuggestion,
  AggregateSearchRequest,
  AggregateSearchResult,
  MultiEntitySearchRequest,
  MultiEntitySearchResult,
  SavedQuery,
  SearchFilters,
  SearchState,
  FilterOption,
  EntityTab,
} from './types';
