# Search Testing Guide
# 搜索功能测试指南

## Prerequisites

Before running tests, ensure:
1. Neo4j is running and accessible
2. Backend API is running on port 8000
3. Conda environment is activated
4. Test data is loaded in Neo4j

## Backend Performance Testing

### Quick Start

```bash
# Activate conda environment
conda activate pharmakg-api

# Run all performance tests
cd /root/autodl-tmp/pj-pharmaKG
python scripts/test_search_performance.py

# Run with custom API URL
python scripts/test_search_performance.py --api-url http://localhost:8000

# Run with custom concurrent request count
python scripts/test_search_performance.py --concurrent 20
```

### What Gets Tested

1. **Full-Text Search** - Tests search performance with various queries
2. **Fuzzy Search** - Tests typo tolerance and similarity matching
3. **Search Suggestions** - Tests autocomplete performance
4. **Aggregation Search** - Tests grouping and aggregation performance
5. **Concurrent Requests** - Tests load handling (10 simultaneous by default)
6. **Large Result Sets** - Tests performance with 50-500 results
7. **API Endpoints** - Tests HTTP endpoint performance

### Understanding Results

The test outputs:
- **Response times** (avg, min, max, P50, P95, P99)
- **Success rates** (successful vs failed requests)
- **Throughput** (requests per second for concurrent tests)
- **Result counts** (average number of results returned)

### Success Criteria

- P95 response time < 500ms ✓
- API availability > 99% ✓
- Concurrent request handling without failures ✓
- Error rate < 1% ✓

### Output Files

Test results are saved to:
- `/root/autodl-tmp/pj-pharmaKG/docs/SEARCH_PERFORMANCE_REPORT.md` - Human-readable report
- `/root/autodl-tmp/pj-pharmaKG/docs/SEARCH_PERFORMANCE_REPORT.json` - Machine-readable data

## Frontend Testing

### Setup

```bash
cd /root/autodl-tmp/pj-pharmaKG/frontend

# Install test dependencies (if not already installed)
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitest/coverage-v8 @vitest/ui

# Run tests in watch mode
npm test

# Run tests once
npm run test:run

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### Test Files

- `src/__tests__/search/UnifiedSearch.test.tsx` - Unified search component tests
- `src/__tests__/search/AdvancedSearch.test.tsx` - Advanced search component tests
- `src/__tests__/search/api.test.ts` - API integration tests

### What Gets Tested

1. **Component Rendering** - Correct display of UI elements
2. **User Interactions** - Click, type, form submissions
3. **State Management** - Query persistence, filter handling
4. **API Integration** - Network requests, error handling
5. **Performance** - Render times, debouncing
6. **Accessibility** - Keyboard navigation, ARIA attributes

### Coverage Goals

- Unit tests: > 80% coverage
- Integration tests: Key user flows covered
- E2E tests: Critical paths covered

## Manual Testing

Use the checklist in `docs/SEARCH_TESTING_CHECKLIST.md` for comprehensive manual testing.

### Quick Manual Tests

1. **Basic Search**
   - Open frontend in browser
   - Type "aspirin" in search bar
   - Verify results appear within 500ms
   - Click a result and verify navigation

2. **Advanced Search**
   - Navigate to Advanced Search
   - Select entity types
   - Add conditions
   - Apply search
   - Verify filtered results

3. **Graph Visualization**
   - Search for any entity
   - Click "View in Graph"
   - Verify graph renders within 1 second
   - Test zoom and pan

4. **Export Functionality**
   - Perform search
   - Click Export → CSV
   - Verify file download
   - Open and verify data

## Troubleshooting

### Backend Tests Fail

**Problem**: Cannot connect to Neo4j
```
Solution:
1. Check Neo4j is running: systemctl status neo4j
2. Check connection: cypher-shell -a bolt://localhost:7687
3. Verify credentials in api/.env
```

**Problem**: No full-text indexes found
```
Solution:
1. Start the API server
2. Call POST /api/v1/admin/init-search-indexes
3. Or manually create indexes via cypher-shell
```

**Problem**: API connection refused
```
Solution:
1. Check API is running: curl http://localhost:8000/health
2. Start API: cd api && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend Tests Fail

**Problem**: Import errors
```
Solution:
1. Check vitest.config.ts has correct path aliases
2. Ensure @ alias points to ./src
3. Reinstall dependencies: rm -rf node_modules && npm install
```

**Problem**: Test timeouts
```
Solution:
1. Increase timeout in vitest.config.ts
2. Check for async operations not being awaited
3. Verify mocks are correctly configured
```

**Problem**: Component tests fail to render
```
Solution:
1. Check all providers are wrapped (QueryClient, BrowserRouter)
2. Verify required props are provided
3. Check for missing context providers
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Search Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      neo4j:
        image: neo4j:5.15
        env:
          NEO4J_AUTH: neo4j/pharmaKG2024!
        ports:
          - 7687:7687
          - 7474:7474
    steps:
      - uses: actions/checkout@v3
      - uses: conda-incubator/setup-miniconda@v2
        with:
          activate-environment: pharmakg-api
          environment-file: environment.yml
      - name: Run performance tests
        run: |
          conda activate pharmakg-api
          python scripts/test_search_performance.py
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: docs/SEARCH_PERFORMANCE_REPORT.*

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      - name: Run tests
        run: |
          cd frontend
          npm run test:run
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: ./frontend/coverage
```

## Performance Optimization Checklist

### Backend Optimizations

- [ ] Create full-text indexes on all searchable fields
- [ ] Implement Redis caching for frequent queries
- [ ] Add query result caching
- [ ] Optimize Cypher queries
- [ ] Implement rate limiting
- [ ] Add database connection pooling
- [ ] Use prepared statements
- [ ] Implement query pagination

### Frontend Optimizations

- [ ] Implement debouncing on search input
- [ ] Add React.memo for expensive components
- [ ] Use virtual scrolling for large result sets
- [ ] Implement lazy loading for images
- [ ] Add service worker for caching
- [ ] Optimize bundle size
- [ ] Use code splitting
- [ ] Implement request deduplication

## Monitoring

### Key Metrics to Track

1. **Backend**
   - Search response times (P50, P95, P99)
   - Error rates
   - Request throughput
   - Database query times
   - Cache hit rates

2. **Frontend**
   - Page load times
   - First contentful paint
   - Time to interactive
   - API response handling
   - User interaction latency

### Alerting Rules

- P95 response time > 1s for 5 minutes
- Error rate > 5% for 5 minutes
- API availability < 95%
- Database connection failures

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [React Query Testing](https://tanstack.com/query/latest/docs/react/testing)
- [Neo4j Performance Tuning](https://neo4j.com/docs/operations-manual/current/performance/)

---

For questions or issues, please refer to the main documentation or create an issue in the project repository.
