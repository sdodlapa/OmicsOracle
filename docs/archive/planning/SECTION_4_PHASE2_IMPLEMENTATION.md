# Section 4: Phase 2 Implementation (Core Features)

**Document**: Modern Web Interface Development Plan
**Section**: 4 of 10
**Focus**: Core Features - Search, Results, and Basic Functionality

---

## 🎯 **PHASE 2 OBJECTIVES**

### **Primary Goals**
- Implement core search functionality with advanced filtering
- Build results display with multiple view modes
- Create data export and visualization features
- Integrate with existing OmicsOracle backend API
- Implement responsive design across all features
- Add comprehensive error handling and loading states

### **Success Criteria**
- ✅ Search interface fully functional with filters
- ✅ Results display supports table, card, and chart views
- ✅ Export functionality works for multiple formats
- ✅ Backend API integration complete and tested
- ✅ Mobile responsiveness across all features
- ✅ Comprehensive error handling and user feedback

### **Timeline Estimation**
- **Duration**: 3-4 weeks
- **Effort**: 100-120 hours
- **Team Size**: 2-3 developers + 1 designer

---

## 🏗️ **IMPLEMENTATION ROADMAP**

### **Week 1: Search Interface & State Management**

#### **Days 1-3: Search State Management & API Integration**

**Task 2.1: Search Store Implementation**

**Search Types** (`src/types/search.ts`):
```typescript
export interface SearchQuery {
  query: string;
  filters: SearchFilters;
  pagination: PaginationParams;
  sortBy?: SortOption;
  sortOrder?: 'asc' | 'desc';
}

export interface SearchFilters {
  category?: OmicsCategory[];
  dateRange?: DateRange;
  organism?: string[];
  studyType?: StudyType[];
  sampleSize?: NumberRange;
  significanceLevel?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  description: string;
  category: OmicsCategory;
  organism: string;
  studyType: StudyType;
  sampleSize: number;
  datePublished: string;
  significance: number;
  metadata: Record<string, any>;
  highlights?: SearchHighlight[];
}

export interface SearchResponse {
  results: SearchResult[];
  pagination: PaginationInfo;
  aggregations: SearchAggregations;
  totalResults: number;
  executionTime: number;
}

export interface SearchAggregations {
  categories: { [key: string]: number };
  organisms: { [key: string]: number };
  studyTypes: { [key: string]: number };
  dateDistribution: DateHistogram[];
}

export type OmicsCategory = 'genomics' | 'proteomics' | 'metabolomics' | 'transcriptomics';
export type StudyType = 'case-control' | 'cohort' | 'cross-sectional' | 'experimental';
```

**Search Store Implementation** (`src/store/slices/searchSlice.ts`):
```typescript
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import { searchAPI } from '@api/search';
import type { SearchQuery, SearchResult, SearchFilters, SearchResponse } from '@types/search';

interface SearchState {
  // Current search state
  query: string;
  filters: SearchFilters;
  sortBy: string;
  sortOrder: 'asc' | 'desc';

  // Results state
  results: SearchResult[];
  totalResults: number;
  pagination: {
    page: number;
    size: number;
    total: number;
  };

  // UI state
  loading: boolean;
  error: string | null;
  suggestions: string[];
  recentSearches: string[];

  // Aggregations for filters
  aggregations: SearchAggregations | null;

  // Actions
  setQuery: (query: string) => void;
  setFilters: (filters: Partial<SearchFilters>) => void;
  setSorting: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  setPagination: (page: number, size?: number) => void;

  // Async actions
  search: () => Promise<void>;
  loadMore: () => Promise<void>;
  getSuggestions: (query: string) => Promise<void>;
  clearSearch: () => void;

  // Utility actions
  addToRecentSearches: (query: string) => void;
  removeFromRecentSearches: (query: string) => void;
}

export const useSearchStore = create<SearchState>()(
  devtools(
    immer((set, get) => ({
      // Initial state
      query: '',
      filters: {},
      sortBy: 'relevance',
      sortOrder: 'desc',
      results: [],
      totalResults: 0,
      pagination: { page: 1, size: 20, total: 0 },
      loading: false,
      error: null,
      suggestions: [],
      recentSearches: JSON.parse(localStorage.getItem('recentSearches') || '[]'),
      aggregations: null,

      // Setters
      setQuery: (query: string) =>
        set((state) => {
          state.query = query;
          state.error = null;
        }),

      setFilters: (filters: Partial<SearchFilters>) =>
        set((state) => {
          state.filters = { ...state.filters, ...filters };
          state.pagination.page = 1; // Reset to first page when filters change
        }),

      setSorting: (sortBy: string, sortOrder: 'asc' | 'desc') =>
        set((state) => {
          state.sortBy = sortBy;
          state.sortOrder = sortOrder;
          state.pagination.page = 1;
        }),

      setPagination: (page: number, size?: number) =>
        set((state) => {
          state.pagination.page = page;
          if (size) state.pagination.size = size;
        }),

      // Search action
      search: async () => {
        const { query, filters, sortBy, sortOrder, pagination } = get();

        if (!query.trim()) {
          set((state) => {
            state.error = 'Please enter a search query';
          });
          return;
        }

        set((state) => {
          state.loading = true;
          state.error = null;
        });

        try {
          const searchQuery: SearchQuery = {
            query: query.trim(),
            filters,
            pagination: { page: pagination.page, size: pagination.size },
            sortBy,
            sortOrder,
          };

          const response = await searchAPI.search(searchQuery);

          set((state) => {
            state.results = response.results;
            state.totalResults = response.totalResults;
            state.pagination.total = Math.ceil(response.totalResults / pagination.size);
            state.aggregations = response.aggregations;
            state.loading = false;
          });

          // Add to recent searches
          get().addToRecentSearches(query.trim());

        } catch (error) {
          console.error('Search error:', error);
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Search failed';
            state.loading = false;
            state.results = [];
          });
        }
      },

      // Load more results (pagination)
      loadMore: async () => {
        const { pagination, loading } = get();

        if (loading || pagination.page >= pagination.total) return;

        set((state) => {
          state.pagination.page += 1;
        });

        await get().search();
      },

      // Get search suggestions
      getSuggestions: async (query: string) => {
        if (!query.trim()) {
          set((state) => {
            state.suggestions = [];
          });
          return;
        }

        try {
          const suggestions = await searchAPI.getSuggestions(query.trim());
          set((state) => {
            state.suggestions = suggestions;
          });
        } catch (error) {
          console.error('Suggestions error:', error);
        }
      },

      // Clear search
      clearSearch: () =>
        set((state) => {
          state.query = '';
          state.results = [];
          state.totalResults = 0;
          state.pagination = { page: 1, size: 20, total: 0 };
          state.error = null;
          state.suggestions = [];
          state.aggregations = null;
        }),

      // Recent searches management
      addToRecentSearches: (query: string) =>
        set((state) => {
          const recent = state.recentSearches.filter(q => q !== query);
          recent.unshift(query);
          state.recentSearches = recent.slice(0, 10); // Keep only last 10
          localStorage.setItem('recentSearches', JSON.stringify(state.recentSearches));
        }),

      removeFromRecentSearches: (query: string) =>
        set((state) => {
          state.recentSearches = state.recentSearches.filter(q => q !== query);
          localStorage.setItem('recentSearches', JSON.stringify(state.recentSearches));
        }),
    })),
    { name: 'search-store' }
  )
);
```

**Search API Client** (`src/api/search.ts`):
```typescript
import { apiClient } from './client';
import type { SearchQuery, SearchResponse, SearchResult } from '@types/search';

export const searchAPI = {
  // Main search endpoint
  search: async (query: SearchQuery): Promise<SearchResponse> => {
    return apiClient.post<SearchResponse>('/search', query);
  },

  // Get search suggestions
  getSuggestions: async (query: string): Promise<string[]> => {
    return apiClient.get<string[]>('/search/suggestions', { query });
  },

  // Get search result details
  getResult: async (id: string): Promise<SearchResult> => {
    return apiClient.get<SearchResult>(`/search/results/${id}`);
  },

  // Export search results
  exportResults: async (
    query: SearchQuery,
    format: 'csv' | 'json' | 'xlsx'
  ): Promise<Blob> => {
    return apiClient.post<Blob>('/search/export',
      { ...query, format },
      { responseType: 'blob' }
    );
  },

  // Get search analytics
  getAnalytics: async (timeRange: string = '30d') => {
    return apiClient.get('/search/analytics', { timeRange });
  },
};
```

#### **Days 4-5: Search Interface Components**

**Task 2.2: Advanced Search Bar Component**

**Search Bar Implementation** (`src/components/features/search/SearchBar.tsx`):
```typescript
import React, { useState, useRef, useEffect } from 'react';
import { useSearchStore } from '@store/slices/searchSlice';
import { useDebounce } from '@hooks/useDebounce';
import { Button } from '@components/ui/Button/Button';
import { Input } from '@components/ui/Input/Input';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  ClockIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import { cn } from '@utils/cn';

export const SearchBar: React.FC = () => {
  const {
    query,
    suggestions,
    recentSearches,
    loading,
    setQuery,
    search,
    getSuggestions,
    addToRecentSearches,
    removeFromRecentSearches
  } = useSearchStore();

  const [localQuery, setLocalQuery] = useState(query);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);

  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounce(localQuery, 300);

  // Get suggestions when query changes
  useEffect(() => {
    if (debouncedQuery && debouncedQuery !== query) {
      getSuggestions(debouncedQuery);
    }
  }, [debouncedQuery, getSuggestions, query]);

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalQuery(value);
    setQuery(value);
    setShowSuggestions(true);
    setSelectedSuggestionIndex(-1);
  };

  // Handle search submission
  const handleSearch = (searchQuery?: string) => {
    const queryToSearch = searchQuery || localQuery;
    if (queryToSearch.trim()) {
      setQuery(queryToSearch);
      search();
      setShowSuggestions(false);
      setSelectedSuggestionIndex(-1);
      inputRef.current?.blur();
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions) return;

    const allSuggestions = [...recentSearches, ...suggestions];

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev =>
          prev < allSuggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => prev > -1 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          handleSearch(allSuggestions[selectedSuggestionIndex]);
        } else {
          handleSearch();
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  };

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const allSuggestions = [...recentSearches, ...suggestions];
  const showRecentSearches = recentSearches.length > 0 && !localQuery.trim();

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>

        <Input
          ref={inputRef}
          type="text"
          placeholder="Search omics data, studies, or genes..."
          value={localQuery}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowSuggestions(true)}
          className="pl-10 pr-20 h-12 text-lg"
          size="lg"
        />

        <div className="absolute inset-y-0 right-0 flex items-center">
          {localQuery && (
            <button
              type="button"
              onClick={() => {
                setLocalQuery('');
                setQuery('');
                setShowSuggestions(false);
                inputRef.current?.focus();
              }}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          )}

          <Button
            onClick={() => handleSearch()}
            disabled={!localQuery.trim() || loading}
            loading={loading}
            className="mr-2"
          >
            Search
          </Button>
        </div>
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && (showRecentSearches || suggestions.length > 0) && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-96 overflow-y-auto"
        >
          {/* Recent Searches */}
          {showRecentSearches && (
            <div className="p-2">
              <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                Recent Searches
              </div>
              {recentSearches.map((recentQuery, index) => (
                <button
                  key={`recent-${index}`}
                  onClick={() => handleSearch(recentQuery)}
                  className={cn(
                    'w-full text-left px-3 py-2 rounded-md flex items-center space-x-3 transition-colors',
                    selectedSuggestionIndex === index
                      ? 'bg-primary-50 text-primary-700'
                      : 'hover:bg-gray-50'
                  )}
                >
                  <ClockIcon className="h-4 w-4 text-gray-400" />
                  <span className="flex-1 truncate">{recentQuery}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFromRecentSearches(recentQuery);
                    }}
                    className="p-1 text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </button>
              ))}
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="p-2 border-t border-gray-100">
              <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                Suggestions
              </div>
              {suggestions.map((suggestion, index) => {
                const adjustedIndex = recentSearches.length + index;
                return (
                  <button
                    key={`suggestion-${index}`}
                    onClick={() => handleSearch(suggestion)}
                    className={cn(
                      'w-full text-left px-3 py-2 rounded-md flex items-center space-x-3 transition-colors',
                      selectedSuggestionIndex === adjustedIndex
                        ? 'bg-primary-50 text-primary-700'
                        : 'hover:bg-gray-50'
                    )}
                  >
                    <ArrowTrendingUpIcon className="h-4 w-4 text-gray-400" />
                    <span className="flex-1 truncate">{suggestion}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

**Task 2.3: Advanced Filters Component**

**Advanced Filters Implementation** (`src/components/features/search/AdvancedFilters.tsx`):
```typescript
import React, { useState } from 'react';
import { useSearchStore } from '@store/slices/searchSlice';
import { Button } from '@components/ui/Button/Button';
import { Input } from '@components/ui/Input/Input';
import {
  ChevronDownIcon,
  ChevronUpIcon,
  FunnelIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { cn } from '@utils/cn';
import type { SearchFilters, OmicsCategory, StudyType } from '@types/search';

const OMICS_CATEGORIES: { value: OmicsCategory; label: string }[] = [
  { value: 'genomics', label: 'Genomics' },
  { value: 'proteomics', label: 'Proteomics' },
  { value: 'metabolomics', label: 'Metabolomics' },
  { value: 'transcriptomics', label: 'Transcriptomics' },
];

const STUDY_TYPES: { value: StudyType; label: string }[] = [
  { value: 'case-control', label: 'Case-Control' },
  { value: 'cohort', label: 'Cohort' },
  { value: 'cross-sectional', label: 'Cross-Sectional' },
  { value: 'experimental', label: 'Experimental' },
];

const COMMON_ORGANISMS = [
  'Homo sapiens',
  'Mus musculus',
  'Drosophila melanogaster',
  'Caenorhabditis elegans',
  'Saccharomyces cerevisiae',
  'Escherichia coli',
];

export const AdvancedFilters: React.FC = () => {
  const { filters, aggregations, setFilters } = useSearchStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [tempFilters, setTempFilters] = useState<SearchFilters>(filters);

  const hasActiveFilters = Object.keys(filters).some(key => {
    const value = filters[key as keyof SearchFilters];
    return Array.isArray(value) ? value.length > 0 : value != null;
  });

  const updateTempFilter = <K extends keyof SearchFilters>(
    key: K,
    value: SearchFilters[K]
  ) => {
    setTempFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    setFilters(tempFilters);
    setIsExpanded(false);
  };

  const clearFilters = () => {
    const emptyFilters: SearchFilters = {};
    setTempFilters(emptyFilters);
    setFilters(emptyFilters);
  };

  const handleCategoryChange = (category: OmicsCategory, checked: boolean) => {
    const currentCategories = tempFilters.category || [];
    const newCategories = checked
      ? [...currentCategories, category]
      : currentCategories.filter(c => c !== category);

    updateTempFilter('category', newCategories.length > 0 ? newCategories : undefined);
  };

  const handleStudyTypeChange = (studyType: StudyType, checked: boolean) => {
    const currentTypes = tempFilters.studyType || [];
    const newTypes = checked
      ? [...currentTypes, studyType]
      : currentTypes.filter(t => t !== studyType);

    updateTempFilter('studyType', newTypes.length > 0 ? newTypes : undefined);
  };

  const handleOrganismChange = (organism: string, checked: boolean) => {
    const currentOrganisms = tempFilters.organism || [];
    const newOrganisms = checked
      ? [...currentOrganisms, organism]
      : currentOrganisms.filter(o => o !== organism);

    updateTempFilter('organism', newOrganisms.length > 0 ? newOrganisms : undefined);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Filter Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-500" />
            <span className="font-medium text-gray-900">Filters</span>
            {hasActiveFilters && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                Active
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="text-red-600 hover:text-red-700"
              >
                Clear All
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center space-x-1"
            >
              <span>{isExpanded ? 'Hide' : 'Show'} Filters</span>
              {isExpanded ? (
                <ChevronUpIcon className="h-4 w-4" />
              ) : (
                <ChevronDownIcon className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Filter Content */}
      {isExpanded && (
        <div className="p-4 space-y-6">
          {/* Omics Categories */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-3">
              Omics Categories
            </label>
            <div className="grid grid-cols-2 gap-2">
              {OMICS_CATEGORIES.map(({ value, label }) => {
                const isChecked = tempFilters.category?.includes(value) || false;
                const count = aggregations?.categories[value] || 0;

                return (
                  <label
                    key={value}
                    className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => handleCategoryChange(value, e.target.checked)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 flex-1">
                      {label}
                    </span>
                    {count > 0 && (
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {count.toLocaleString()}
                      </span>
                    )}
                  </label>
                );
              })}
            </div>
          </div>

          {/* Study Types */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-3">
              Study Types
            </label>
            <div className="grid grid-cols-2 gap-2">
              {STUDY_TYPES.map(({ value, label }) => {
                const isChecked = tempFilters.studyType?.includes(value) || false;
                const count = aggregations?.studyTypes[value] || 0;

                return (
                  <label
                    key={value}
                    className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => handleStudyTypeChange(value, e.target.checked)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 flex-1">
                      {label}
                    </span>
                    {count > 0 && (
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {count.toLocaleString()}
                      </span>
                    )}
                  </label>
                );
              })}
            </div>
          </div>

          {/* Organisms */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-3">
              Model Organisms
            </label>
            <div className="space-y-2">
              {COMMON_ORGANISMS.map((organism) => {
                const isChecked = tempFilters.organism?.includes(organism) || false;
                const count = aggregations?.organisms[organism] || 0;

                return (
                  <label
                    key={organism}
                    className="flex items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => handleOrganismChange(organism, e.target.checked)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 flex-1 italic">
                      {organism}
                    </span>
                    {count > 0 && (
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {count.toLocaleString()}
                      </span>
                    )}
                  </label>
                );
              })}
            </div>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-3">
              Publication Date Range
            </label>
            <div className="grid grid-cols-2 gap-4">
              <Input
                type="date"
                label="From"
                value={tempFilters.dateRange?.start?.toISOString().split('T')[0] || ''}
                onChange={(e) => {
                  const date = e.target.value ? new Date(e.target.value) : undefined;
                  updateTempFilter('dateRange', {
                    ...tempFilters.dateRange,
                    start: date
                  });
                }}
              />
              <Input
                type="date"
                label="To"
                value={tempFilters.dateRange?.end?.toISOString().split('T')[0] || ''}
                onChange={(e) => {
                  const date = e.target.value ? new Date(e.target.value) : undefined;
                  updateTempFilter('dateRange', {
                    ...tempFilters.dateRange,
                    end: date
                  });
                }}
              />
            </div>
          </div>

          {/* Sample Size Range */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-3">
              Sample Size Range
            </label>
            <div className="grid grid-cols-2 gap-4">
              <Input
                type="number"
                label="Minimum"
                placeholder="e.g., 100"
                value={tempFilters.sampleSize?.min || ''}
                onChange={(e) => {
                  const min = e.target.value ? parseInt(e.target.value) : undefined;
                  updateTempFilter('sampleSize', {
                    ...tempFilters.sampleSize,
                    min
                  });
                }}
              />
              <Input
                type="number"
                label="Maximum"
                placeholder="e.g., 10000"
                value={tempFilters.sampleSize?.max || ''}
                onChange={(e) => {
                  const max = e.target.value ? parseInt(e.target.value) : undefined;
                  updateTempFilter('sampleSize', {
                    ...tempFilters.sampleSize,
                    max
                  });
                }}
              />
            </div>
          </div>

          {/* Significance Level */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-3">
              Minimum Significance Level (p-value)
            </label>
            <select
              value={tempFilters.significanceLevel || ''}
              onChange={(e) => {
                const value = e.target.value ? parseFloat(e.target.value) : undefined;
                updateTempFilter('significanceLevel', value);
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="">Any significance level</option>
              <option value="0.05">p ≤ 0.05</option>
              <option value="0.01">p ≤ 0.01</option>
              <option value="0.001">p ≤ 0.001</option>
              <option value="0.0001">p ≤ 0.0001</option>
            </select>
          </div>

          {/* Apply/Cancel Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button
              variant="outline"
              onClick={() => {
                setTempFilters(filters);
                setIsExpanded(false);
              }}
            >
              Cancel
            </Button>
            <Button onClick={applyFilters}>
              Apply Filters
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

### **Week 2: Results Display & Visualization**

#### **Days 6-8: Results Display Components**

**Task 2.4: Results List Component**

**Results List Implementation** (`src/components/features/results/ResultsList.tsx`):
```typescript
import React, { useState } from 'react';
import { useSearchStore } from '@store/slices/searchSlice';
import { Button } from '@components/ui/Button/Button';
import { ResultCard } from './ResultCard';
import { ResultsTable } from './ResultsTable';
import { ResultsChart } from './ResultsChart';
import {
  Squares2X2Icon,
  TableCellsIcon,
  ChartBarIcon,
  ArrowDownIcon,
  ArrowUpIcon
} from '@heroicons/react/24/outline';
import { cn } from '@utils/cn';

type ViewMode = 'cards' | 'table' | 'chart';

const VIEW_MODES = [
  { mode: 'cards' as const, label: 'Cards', icon: Squares2X2Icon },
  { mode: 'table' as const, label: 'Table', icon: TableCellsIcon },
  { mode: 'chart' as const, label: 'Charts', icon: ChartBarIcon },
];

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'date', label: 'Publication Date' },
  { value: 'significance', label: 'Statistical Significance' },
  { value: 'sampleSize', label: 'Sample Size' },
  { value: 'title', label: 'Title' },
];

export const ResultsList: React.FC = () => {
  const {
    results,
    totalResults,
    pagination,
    loading,
    error,
    sortBy,
    sortOrder,
    setSorting,
    loadMore,
  } = useSearchStore();

  const [viewMode, setViewMode] = useState<ViewMode>('cards');

  const handleSortChange = (newSortBy: string) => {
    if (sortBy === newSortBy) {
      // Toggle sort order if same field
      setSorting(newSortBy, sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Default to desc for new field
      setSorting(newSortBy, 'desc');
    }
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-red-600 font-medium mb-2">Search Error</div>
        <div className="text-red-500 text-sm">{error}</div>
      </div>
    );
  }

  if (!loading && results.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <div className="text-gray-500 font-medium mb-2">No Results Found</div>
        <div className="text-gray-400 text-sm">
          Try adjusting your search query or filters
        </div>
      </div>
    );
  }

  const hasMoreResults = pagination.page < pagination.total;

  return (
    <div className="space-y-6">
      {/* Results Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Search Results
          </h2>
          {totalResults > 0 && (
            <span className="text-sm text-gray-500">
              {totalResults.toLocaleString()} results found
            </span>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Sort Dropdown */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-700">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
              className="text-sm border-gray-300 rounded-md focus:border-primary-500 focus:ring-primary-500"
            >
              {SORT_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSorting(sortBy, sortOrder === 'asc' ? 'desc' : 'asc')}
              className="p-1"
            >
              {sortOrder === 'asc' ? (
                <ArrowUpIcon className="h-4 w-4" />
              ) : (
                <ArrowDownIcon className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            {VIEW_MODES.map(({ mode, label, icon: Icon }) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  'flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                  viewMode === mode
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
                title={label}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Content */}
      <div className="min-h-[400px]">
        {viewMode === 'cards' && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {results.map((result) => (
              <ResultCard key={result.id} result={result} />
            ))}
          </div>
        )}

        {viewMode === 'table' && (
          <ResultsTable results={results} />
        )}

        {viewMode === 'chart' && (
          <ResultsChart results={results} />
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="flex items-center space-x-2 text-gray-500">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-500"></div>
              <span>Loading results...</span>
            </div>
          </div>
        )}
      </div>

      {/* Load More Button */}
      {!loading && hasMoreResults && (
        <div className="flex justify-center py-6">
          <Button
            onClick={loadMore}
            disabled={loading}
            variant="outline"
            size="lg"
          >
            Load More Results
          </Button>
        </div>
      )}

      {/* Results Summary */}
      {results.length > 0 && (
        <div className="text-center text-sm text-gray-500 py-4">
          Showing {results.length} of {totalResults.toLocaleString()} results
          {pagination.page > 1 && (
            <span> • Page {pagination.page} of {pagination.total}</span>
          )}
        </div>
      )}
    </div>
  );
};
```

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Search Functionality**
- [ ] Search store with Zustand and Immer implemented
- [ ] Advanced search bar with autocomplete and suggestions
- [ ] Comprehensive filtering system with aggregations
- [ ] Search history and recent searches functionality
- [ ] Debounced search queries and API optimization

### **Results Display**
- [ ] Multiple view modes (cards, table, charts)
- [ ] Sorting and pagination functionality
- [ ] Responsive design for all screen sizes
- [ ] Loading states and error handling
- [ ] Infinite scroll or load more functionality

### **API Integration**
- [ ] Search API client with proper error handling
- [ ] Request/response interceptors configured
- [ ] Caching strategy for improved performance
- [ ] Export functionality for different formats
- [ ] Analytics and usage tracking

### **State Management**
- [ ] Centralized search state with Zustand
- [ ] Proper TypeScript typing throughout
- [ ] Optimistic updates and error rollback
- [ ] Local storage for user preferences
- [ ] Performance optimization with selectors

---

**Next Section**: [Section 5: Phase 3 Implementation (Advanced Features)](./SECTION_5_PHASE3_IMPLEMENTATION.md)
