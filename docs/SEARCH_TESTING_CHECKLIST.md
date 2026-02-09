# PharmaKG Search Testing Checklist
# 搜索功能测试清单

## Backend Testing

### Full-Text Search (全文搜索)
- [ ] Basic search with single word
- [ ] Search with multiple words
- [ ] Search with special characters
- [ ] Search with different languages (English, Chinese)
- [ ] Search with empty query
- [ ] Search with very long query (>100 characters)
- [ ] Search results pagination
- [ ] Search result relevance scoring
- [ ] Entity type filtering
- [ ] Domain filtering

### Fuzzy Search (模糊搜索)
- [ ] Search with typos (1 character difference)
- [ ] Search with typos (2 characters difference)
- [ ] Search with typos (>2 characters difference)
- [ ] Partial word matching
- [ ] Case-insensitive matching
- [ ] Fuzzy search fallback when APOC not available

### Search Suggestions (搜索建议)
- [ ] Autocomplete for single character
- [ ] Autocomplete for multiple characters
- [ ] Autocomplete for common prefixes
- [ ] Autocomplete for rare prefixes
- [ ] Suggestion ranking by frequency
- [ ] Empty suggestions for invalid prefix

### Aggregation Search (聚合搜索)
- [ ] Group by entity type
- [ ] Group by domain
- [ ] Mixed entity type results
- [ ] Large result set aggregation
- [ ] Empty result handling

### API Endpoints
- [ ] POST /api/v1/search/fulltext
- [ ] GET /api/v1/search/suggestions
- [ ] POST /api/v1/search/aggregate
- [ ] GET /api/v1/search/queries (saved queries)
- [ ] POST /api/v1/search/queries (save query)
- [ ] DELETE /api/v1/search/queries/{id}

### Performance Tests
- [ ] P95 response time < 500ms
- [ ] Concurrent requests (10 simultaneous)
- [ ] Large result sets (>500 results)
- [ ] API availability > 99%
- [ ] Error rate < 1%

## Frontend Testing

### UnifiedSearch Component
#### Rendering
- [ ] Component renders without errors
- [ ] Search bar displays correctly
- [ ] Filter button is visible
- [ ] Domain selector is functional
- [ ] Entity type selector is functional
- [ ] Recent searches display
- [ ] Saved queries display

#### Search Functionality
- [ ] Search on Enter key
- [ ] Search on button click
- [ ] Debounced search input
- [ ] URL parameter handling
- [ ] Query persistence in URL

#### Results Display
- [ ] Results grouped by entity type
- [ ] Tab navigation between entity types
- [ ] Result cards display correctly
- [ ] Relevance score display
- [ ] Snippet display
- [ ] Matched fields display

#### Filtering
- [ ] Apply domain filters
- [ ] Apply entity type filters
- [ ] Clear all filters
- [ ] Filter badge count updates
- [ ] URL updates with filters

#### Pagination
- [ ] Previous button disabled on first page
- [ ] Next button functionality
- [ ] Page number display
- [ ] Page size control

#### Export
- [ ] Export as CSV
- [ ] Export as JSON
- [ ] Export with filters applied
- [ ] Export filename generation

### AdvancedSearch Component
#### Rendering
- [ ] All filter sections display
- [ ] Domain selector is functional
- [ ] Entity type selector is functional
- [ ] Boolean operator selector
- [ ] Custom conditions section
- [ ] Temporal filters section
- [ ] Action buttons display

#### Query Building
- [ ] Main query input
- [ ] Add condition button
- [ ] Remove condition button
- [ ] Field selection per condition
- [ ] Operator selection per condition
- [ ] Value input per condition

#### Condition Types
- [ ] Text field conditions
- [ ] Numeric field conditions
- [ ] Date field conditions
- [ ] Enum field conditions
- [ ] Range conditions

#### Boolean Operators
- [ ] AND operator
- [ ] OR operator
- [ ] NOT operator
- [ ] Operator application to conditions

#### Temporal Filters
- [ ] Date range enable/disable
- [ ] Start date selection
- [ ] End date selection
- [ ] Date range validation

#### Saved Queries
- [ ] Save query button
- [ ] Load query from saved
- [ ] Delete saved query
- [ ] Saved queries modal
- [ ] Query name input

#### Export
- [ ] Export query configuration
- [ ] Copy query to clipboard
- [ ] Query JSON display

### SearchResults Component
#### Rendering
- [ ] Results list display
- [ ] Result card rendering
- [ ] Empty state display
- [ ] Loading state display
- [ ] Error state display

#### Result Cards
- [ ] Entity type badge
- [ ] Domain badge
- [ ] Relevance indicator
- [ ] Name display
- [ ] Snippet display
- [ ] Click navigation

#### Interaction
- [ ] Card click navigation
- [ ] Card hover effect
- [ ] Keyboard navigation
- [ ] Accessibility attributes

### Graph Navigation
#### Visualization
- [ ] Graph renders correctly
- [ ] Nodes display
- [ ] Edges display
- [ ] Labels display
- [ ] Colors by domain

#### Interaction
- [ ] Zoom in/out
- [ ] Pan functionality
- [ ] Click on node
- [ ] Select multiple nodes
- [ ] Drag nodes

#### Performance
- [ ] Render time < 1s for 1000 nodes
- [ ] Smooth zoom/pan
- [ ] Responsive layout

## Integration Testing

### API Integration
- [ ] Successful API calls
- [ ] Error handling
- [ ] Timeout handling
- [ ] Retry logic
- [ ] Request cancellation

### State Management
- [ ] Query state persistence
- [ ] Filter state persistence
- [ ] Results caching
- [ ] Cache invalidation

### URL Handling
- [ ] Query parameter parsing
- [ ] URL updates on search
- [ ] Browser back/forward
- [ ] Shareable URLs

### Error Handling
- [ ] Network errors
- [ ] API errors
- [ ] Timeout errors
- [ ] Malformed responses
- [ ] User-friendly error messages

## Performance Testing

### Backend Performance
- [ ] Search response time < 500ms (P95)
- [ ] Suggestion response time < 200ms
- [ ] Aggregation response time < 1s
- [ ] Concurrent request handling (10+ simultaneous)
- [ ] Large result set performance (>500 results)
- [ ] Database query optimization

### Frontend Performance
- [ ] Initial page load < 2s
- [ ] Search results render < 500ms
- [ ] Graph visualization < 1s (1000 nodes)
- [ ] Debounced search input (500ms)
- [ ] Smooth animations (60fps)

### Network Performance
- [ ] API response size optimization
- [ ] Gzip compression enabled
- [ ] CDN usage for static assets
- [ ] Browser caching headers

## Manual Testing Scenarios

### Scenario 1: Basic Drug Search
1. Navigate to search page
2. Enter "aspirin" in search bar
3. Verify results appear
4. Check result relevance
5. Click on a result
6. Verify navigation to entity detail

### Scenario 2: Cross-Domain Search
1. Navigate to advanced search
2. Select multiple domains (R&D, Clinical)
3. Enter "cancer" in query
4. Apply search
5. Verify results from both domains
6. Check domain grouping

### Scenario 3: Complex Query Building
1. Navigate to advanced search
2. Select "Compound" entity type
3. Add condition: molecular_weight between 200-400
4. Add condition: logp < 5
5. Enter "kinase inhibitor" in main query
6. Apply search
7. Verify filtered results

### Scenario 4: Graph Exploration
1. Perform search for "aspirin"
2. Click on a compound result
3. View entity detail page
4. Click "View in Graph" button
5. Verify graph visualization
6. Explore connected nodes
7. Test zoom and pan

### Scenario 5: Query Saving and Loading
1. Build complex query in advanced search
2. Click "Save Query"
3. Enter query name
4. Verify save success
5. Clear search
6. Click "View Saved Queries"
7. Load saved query
8. Verify filters restored

### Scenario 6: Export Functionality
1. Perform search with results
2. Click "Export" button
3. Select "Export as CSV"
4. Verify file download
5. Open file and verify data
6. Repeat with JSON export

## Accessibility Testing

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Enter/Space to activate buttons
- [ ] Arrow keys for list navigation
- [ ] Escape to close modals

### Screen Reader
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] ARIA labels for complex widgets
- [ ] Error messages are announced

### Visual Accessibility
- [ ] Sufficient color contrast
- [ ] Text is resizable
- [ ] Focus indicators visible
- [ ] No seizure-inducing content

## Browser Compatibility

### Desktop Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Mobile Browsers
- [ ] iOS Safari
- [ ] Chrome Mobile
- [ ] Samsung Internet
- [ ] Firefox Mobile

## Success Criteria Verification

### Performance Targets
- [ ] Search response time P95 < 500ms ✓
- [ ] API availability > 99% ✓
- [ ] Frontend page load < 2s ✓
- [ ] Graph render < 1s (1000 nodes) ✓

### Quality Targets
- [ ] Relevance precision > 80% ✓
- [ ] Error rate < 1% ✓
- [ ] Test coverage > 70% ✓
- [ ] No critical bugs ✓

## Test Results Summary

### Backend Tests
- Full-Text Search: PASS/FAIL
- Fuzzy Search: PASS/FAIL
- Suggestions: PASS/FAIL
- Aggregation: PASS/FAIL
- API Endpoints: PASS/FAIL
- Performance: PASS/FAIL

### Frontend Tests
- UnifiedSearch: PASS/FAIL
- AdvancedSearch: PASS/FAIL
- SearchResults: PASS/FAIL
- Integration: PASS/FAIL
- Performance: PASS/FAIL

### Manual Tests
- Basic Search: PASS/FAIL
- Cross-Domain: PASS/FAIL
- Complex Queries: PASS/FAIL
- Graph Navigation: PASS/FAIL
- Query Saving: PASS/FAIL
- Export: PASS/FAIL

## Notes and Observations

### Issues Found
1. [Description]
2. [Description]

### Recommendations
1. [Recommendation]
2. [Recommendation]

### Performance Bottlenecks
1. [Bottleneck]
2. [Bottleneck]

### User Experience Feedback
1. [Feedback]
2. [Feedback]

---

**Tested by**: ___________
**Date**: ___________
**Version**: ___________
