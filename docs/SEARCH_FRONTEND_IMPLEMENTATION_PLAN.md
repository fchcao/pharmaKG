# PharmaKG Search & Frontend Implementation Plan
## Building Interactive User Interface and Enhanced Search Capabilities

---

## Context

### Current State Assessment

**Backend API Status:**
- **62 REST endpoints** across 4 domains (R&D, Clinical, Supply Chain, Regulatory)
- **5 service classes** with 60+ methods
- **Comprehensive data models** in Pydantic
- **Neo4j singleton connection** pattern implemented

**Current Capabilities:**
- Single entity lookup by ID
- Direct relationship queries (1-hop)
- Basic attribute filtering with pagination
- Multi-hop queries (advanced service)
- Statistical aggregations and timelines
- Cross-domain queries

**Current Limitations:**
- **No full-text search** - only CONTAINS for string matching
- **No fuzzy matching** - exact matches required
- **No semantic search** - no vector/embedding-based search
- **No autocomplete** - no prefix/suffix search endpoints
- **Limited sorting** - fixed ORDER BY in queries
- **No result scoring** - no relevance ranking

**Knowledge Graph State:**
- **1,894,173 nodes** (99.8% R&D domain from ChEMBL)
- **6,781 relationships** (low ratio: ~0.0036)
- **24 node labels** defined (only 6 populated)
- **67 indexes** online and 100% populated
- **17 constraints** for data integrity

**Frontend Status:**
- **No frontend exists** - entirely new development
- Docker compose references non-existent frontend/backend directories
- Roadmap plans frontend in Month 3 (basic), Phase 2 (quality monitoring), Phase 3 (advanced)

**Data Distribution:**
- R&D Domain: 1,891,311 nodes (Compounds, Targets, Assays, Pathways)
- Regulatory Domain: 1,938 nodes (Documents, Agencies, Submissions)
- Supply Chain Domain: 324 nodes (Manufacturers)
- Clinical Domain: 0 nodes (empty)

---

## Strategic Vision

Transform PharmaKG from a backend-only API into a **complete interactive knowledge graph platform** by:

1. **Enhancing backend search** with full-text, fuzzy, and semantic search capabilities
2. **Building modern frontend** with interactive graph visualization
3. **Creating intuitive query interface** for both simple and complex queries
4. **Implementing real-time updates** for safety signals and shortages
5. **Providing domain-specific dashboards** for each business domain

---

## Phase 1: Enhanced Backend Search (Week 1-2)

### Objective
Add advanced search capabilities to the existing FastAPI backend

### 1.1 Full-Text Search Implementation

**Create:** `api/services/search_service.py`

**Features:**
- Neo4j full-text search indexes
- Multi-field search (name, description, properties)
- Relevance scoring and ranking
- Faceted search by domain, entity type
- Search suggestions and autocomplete

**Endpoints to Add:**
```
POST /api/v1/search/fulltext
  - query: string
  - entity_types: list[str] (optional)
  - domains: list[str] (optional)
  - limit: int (default: 20)
  - offset: int (default: 0)

GET /api/v1/search/suggestions
  - q: string (prefix)
  - entity_type: str (optional)
  - limit: int (default: 10)
```

**Implementation:**
- Create Neo4j full-text indexes for each entity type
- Use CALL db.index.fulltext.queryNodes() for search
- Return relevance scores with results
- Support multi-language (English, Chinese)

### 1.2 Fuzzy Search Implementation

**Features:**
- Approximate string matching (Levenshtein distance)
- Phonetic search for names
- InChIKey prefix search for compounds
- UniProt ID fuzzy matching

**Endpoints to Add:**
```
POST /api/v1/search/fuzzy
  - query: string
  - entity_type: str
  - max_distance: int (default: 2)
  - limit: int (default: 20)
```

**Implementation:**
- Use Neo4j APOC procedures (apoc.text.distance)
- Implement phonetic algorithms (Soundex, Metaphone)
- Cache common fuzzy matches in Redis

### 1.3 Semantic Search (Optional - Future Enhancement)

**Requirements:**
- Generate embeddings for entities (using property data)
- Store vectors in Neo4j or separate vector DB
- Implement similarity search
- Support "find similar entities" queries

**Endpoints to Add:**
```
POST /api/v1/search/semantic
  - entity_id: str
  - entity_type: str
  - limit: int (default: 10)

GET /api/v1/search/similar/{entity_id}
  - limit: int (default: 10)
```

### 1.4 Search Aggregation Endpoint

**Endpoint:**
```
POST /api/v1/search/aggregate
  - query: string
  - group_by: str (domain, entity_type, etc.)
  - filters: dict (optional)
```

**Returns:**
- Faceted counts by entity type
- Domain distribution
- Top results with snippets

---

## Phase 2: Frontend Foundation (Week 3-4)

### Objective
Set up modern frontend development environment with core infrastructure

### 2.1 Technology Stack Selection (CONFIRMED)

**Selected: React + TypeScript + Vite**

**Rationale:**
- TypeScript: Type safety matches project's data quality emphasis
- Vite: Fast development, modern build tool
- React: Largest ecosystem for graph visualization
- Excellent FastAPI integration with OpenAPI code generation

**Graph Visualization: Cytoscape.js**
- Most powerful, handles 1000+ nodes smoothly
- Excellent layout algorithms (force-directed, hierarchical)
- Mature ecosystem with React integration

**Development Approach: Parallel**
- Backend search endpoints and frontend UI developed simultaneously
- Weekly integration syncs to ensure API contracts align

### 2.2 Project Structure

```
frontend/
├── src/
│   ├── domains/
│   │   ├── rd/              # R&D domain components
│   │   ├── clinical/        # Clinical domain components
│   │   ├── supply/          # Supply chain components
│   │   └── regulatory/      # Regulatory components
│   ├── shared/
│   │   ├── components/      # Shared UI components
│   │   ├── graphs/          # Graph visualization components
│   │   ├── search/          # Search components
│   │   ├── api/             # API client setup
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # Utility functions
│   ├── layouts/             # Page layouts
│   ├── pages/               # Route pages
│   └── main.tsx             # Entry point
├── public/                  # Static assets
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

### 2.3 Core Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "react-flow-renderer": "^10.3.0",
    "cytoscape": "^3.28.0",
    "cytoscape-react": "^2.0.0",
    "antd": "^5.12.0",
    "@ant-design/icons": "^5.2.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "openapi-typescript": "^6.7.0",
    "openapi-fetch": "^0.0.3",
    "vitest": "^1.0.0"
  }
}
```

### 2.4 API Client Generation

**Generate OpenAPI client:**
```bash
# Generate TypeScript types from FastAPI OpenAPI spec
npx openapi-typescript http://localhost:8000/openapi.json -o src/shared/types/api.ts
```

**Create API client:**
- `src/shared/api/client.ts` - Axios instance with interceptors
- `src/shared/api/endpoints/` - Domain-specific endpoint functions
- `src/shared/api/hooks/` - React Query hooks

---

## Phase 3: Core UI Components (Week 5-6)

### Objective
Build reusable UI components and graph visualization components

### 3.1 Shared Components

**Location:** `src/shared/components/`

**Components to Create:**

1. **SearchBar** - Unified search input
   - Autocomplete dropdown
   - Recent searches
   - Domain filters

2. **EntityCard** - Display entity information
   - Type-specific styling
   - Quick actions
   - Expandable details

3. **RelationshipViewer** - Show entity relationships
   - List view
   - Compact graph view

4. **DataTable** - Paginated data tables
   - Sortable columns
   - Filtering
   - Export

5. **LoadingSpinner**, **ErrorBoundary**, **EmptyState**

### 3.2 Graph Visualization Components

**Location:** `src/shared/graphs/`

**Components to Create:**

1. **GraphViewer** - Main graph visualization
   - Uses React Flow or Cytoscape.js
   - Force-directed layout
   - Zoom/pan controls
   - Node/edge styling by type
   - Click to expand neighbors
   - Path highlighting

2. **SubgraphExplorer** - Explore local neighborhoods
   - Depth control
   - Relationship type filters
   - Export subgraph

3. **PathVisualizer** - Visualize paths between entities
   - Animate path traversal
   - Show intermediate nodes
   - Highlight alternatives

4. **TimelineChart** - Visualize temporal data
   - Submissions, approvals, trials over time
   - Interactive filtering

### 3.3 Search Components

**Location:** `src/shared/search/`

**Components to Create:**

1. **UnifiedSearch** - Main search interface
   - Full-text search input
   - Entity type filters
   - Domain filters
   - Results with snippets

2. **AdvancedSearch** - Complex query builder
   - Multi-field filters
   - Range sliders for numerical values
   - Date range pickers
   - Boolean operators (AND/OR/NOT)

3. **SearchResults** - Results display
   - Tabbed by entity type
   - Relevance scores
   - Faceted navigation
   - Export options

---

## Phase 4: Domain-Specific Pages (Week 7-10)

### Objective
Build pages for each business domain with domain-specific features

### 4.1 R&D Domain Pages

**Routes:**
- `/rd/compounds` - Compound catalog
- `/rd/compounds/:id` - Compound detail page
- `/rd/targets` - Target catalog
- `/rd/targets/:id` - Target detail page
- `/rd/assays` - Assay browser
- `/rd/pathways` - Pathway browser

**Features:**
- Compound structure viewer (SMILES to 2D/3D)
- Target protein information
- Bioactivity data tables
- Pathway diagrams
- Drug repurposing suggestions

### 4.2 Clinical Domain Pages

**Routes:**
- `/clinical/trials` - Clinical trial catalog
- `/clinical/trials/:id` - Trial detail page
- `/clinical/conditions` - Condition browser
- `/clinical/interventions` - Intervention browser

**Features:**
- Trial phase distribution
- Site maps (geographic)
- Enrollment timeline
- Adverse event summaries
- Trial comparison

### 4.3 Supply Chain Domain Pages

**Routes:**
- `/supply/manufacturers` - Manufacturer catalog
- `/supply/manufacturers/:id` - Manufacturer detail
- `/supply/shortages` - Drug shortage monitor
- `/supply/facilities` - Facility browser

**Features:**
- Manufacturer quality scores
- Supply chain network visualization
- Shortage cascade analysis
- API dependency tracking

### 4.4 Regulatory Domain Pages

**Routes:**
- `/regulatory/submissions` - Submission catalog
- `/regulatory/submissions/:id` - Submission detail
- `/regulatory/approvals` - Approval catalog
- `/regulatory/documents` - Document browser

**Features:**
- Submission timeline
- Approval pathway visualization
- Compliance tracking
- Safety signal monitoring

---

## Phase 5: Cross-Domain Features (Week 11-12)

### Objective
Implement advanced cross-domain query and visualization

### 5.1 Cross-Domain Query Interface

**Route:** `/cross-domain`

**Features:**
- Visual query builder
- Multi-hop path queries
- Drug → Trial → Submission → Approval chains
- Manufacturer → Inspection → Compliance → Shortage chains
- Competitive landscape analysis

### 5.2 Dashboard Pages

**Route:** `/dashboard`

**Features:**
- Knowledge graph statistics
- Data quality metrics
- Real-time safety signals
- Active shortages
- Recent submissions
- Network health indicators

### 5.3 Export and Reporting

**Features:**
- Export query results (CSV, JSON, Excel)
- Generate PDF reports
- Save queries for later
- Share visualization links

---

## Critical Files to Modify

### Backend Changes

1. **`api/main.py`**
   - Add search endpoints
   - Add CORS configuration for frontend
   - Add rate limiting for search

2. **`api/services/search_service.py`** (NEW)
   - Full-text search implementation
   - Fuzzy search implementation
   - Search aggregation

3. **`api/models.py`**
   - Add search request/response models
   - Add pagination models

4. **`api/database.py`**
   - Add full-text index creation methods
   - Add connection pooling for search

### Frontend Creation

1. **`frontend/`** (NEW DIRECTORY)
   - Complete React + TypeScript + Vite setup
   - All source code as outlined above

2. **`frontend/src/shared/api/`** (NEW)
   - API client setup
   - React Query hooks
   - Error handling

3. **`frontend/src/shared/graphs/`** (NEW)
   - Graph visualization components
   - Cytoscape.js/React Flow integration

4. **`deploy/docker/docker-compose.yml`** (MODIFY)
   - Add frontend service
   - Configure network between frontend and API

---

## Implementation Details

### Backend Search Implementation

**Full-Text Index Creation:**
```python
# In api/database.py or separate migration script
def create_fulltext_indexes(db):
    indexes = [
        ("compound_fulltext", ["Compound"], ["name", "pref_name", "canonical_smiles"]),
        ("target_fulltext", ["Target"], ["name", "gene_symbol", "uniprot_id"]),
        ("assay_fulltext", ["Assay"], ["name", "description", "assay_type"]),
        # ... more indexes for each entity type
    ]

    for name, labels, properties in indexes:
        cypher = f"""
        CALL db.index.fulltext.createNodeIndex('{name}', {labels}, {properties})
        """
        db.execute_write(cypher)
```

**Search Query Pattern:**
```python
def search_entities(self, query: str, entity_types: List[str] = None, limit: int = 20):
    entity_filter = ""
    if entity_types:
        entity_filter = f"AND e:{'|'.join(entity_types)}"

    cypher = f"""
    CALL db.index.fulltext.queryNodes('entity_fulltext', $query) AS e
    WHERE e.score > 0.1
    {entity_filter}
    RETURN e.node AS entity, e.score AS relevance
    ORDER BY e.score DESC
    LIMIT $limit
    """
    return self.db.execute_query(cypher, {"query": query, "limit": limit})
```

### Frontend State Management

**Zustand Store Structure:**
```typescript
// src/shared/stores/useGraphStore.ts
interface GraphState {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  addNode: (node: GraphNode) => void;
  removeNode: (id: string) => void;
  expandNeighbors: (id: string, depth: number) => Promise<void>;
}

// src/shared/stores/useSearchStore.ts
interface SearchState {
  query: string;
  results: SearchResult[];
  filters: SearchFilters;
  setQuery: (query: string) => void;
  setResults: (results: SearchResult[]) => void;
}
```

### Graph Visualization Setup

**Cytoscape.js Configuration:**
```typescript
// src/shared/graphs/GraphViewer.tsx
const cytoscapeConfig = {
  style: [
    {
      selector: 'node[type="Compound"]',
      style: {
        'background-color': '#4CAF50',
        'label': 'data(name)',
        'width': 30,
        'height': 30
      }
    },
    {
      selector: 'node[type="Target"]',
      style: {
        'background-color': '#2196F3',
        'label': 'data(name)',
        'width': 25,
        'height': 25
      }
    },
    // ... more styles for each entity type
  ],
  layout: {
    name: 'cose',
    idealEdgeLength: 100,
    nodeOverlap: 20
  }
};
```

---

## Verification & Testing

### Backend Testing

1. **Search Endpoint Tests**
   - Test full-text search with various queries
   - Test fuzzy search with typos
   - Test faceted search by domain
   - Test pagination and sorting
   - Test relevance scoring

2. **Performance Tests**
   - Measure search response time (< 500ms target)
   - Test concurrent search requests
   - Test with large result sets

### Frontend Testing

1. **Component Tests**
   - Test all UI components with Vitest
   - Test graph visualization with sample data
   - Test search functionality end-to-end

2. **Integration Tests**
   - Test API integration
   - Test error handling
   - Test loading states

3. **Manual Testing**
   - Test graph navigation (zoom, pan, click)
   - Test search autocomplete
   - Test cross-domain queries
   - Test export functionality

---

## Success Metrics

### Backend
- Full-text search response time < 500ms
- Search relevance precision > 80%
- API availability > 99%

### Frontend
- Page load time < 2 seconds
- Graph rendering < 1 second for 1000 nodes
- Time to interactive < 3 seconds
- User session duration > 5 minutes (engagement)

### User Experience
- Zero training required for basic search
- < 3 clicks to find any entity
- Graph visualization supports 1000+ nodes smoothly
- Mobile responsive (tablet support)

---

## Risk Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Neo4j full-text search performance | High | Implement Redis caching for common queries |
| Frontend graph performance with large graphs | High | Implement virtualization, lazy loading |
| API rate limits exceeded | Medium | Implement request queuing, pagination |
| Browser compatibility | Low | Test on Chrome, Firefox, Safari, Edge |
| CORS issues | Low | Configure CORS properly in FastAPI |

---

## Next Steps After Approval

### Week 1 (Parallel Development)
**Backend:**
- Create Neo4j full-text indexes for all entity types
- Implement `SearchService` class with full-text search
- Add search endpoints to `api/main.py`

**Frontend:**
- Set up React + TypeScript + Vite project
- Generate OpenAPI client from FastAPI spec
- Create basic routing structure

### Week 2 (Parallel Development)
**Backend:**
- Implement fuzzy search with APOC procedures
- Add autocomplete/suggestions endpoint
- Create search aggregation endpoint

**Frontend:**
- Build shared UI components (SearchBar, EntityCard, DataTable)
- Set up Zustand stores for state management
- Configure Cytoscape.js integration

### Week 3-4 (Integration Focus)
**Frontend:**
- Implement GraphViewer component with Cytoscape.js
- Build UnifiedSearch interface
- Create R&D domain pages (Compounds, Targets)

**Backend:**
- Performance optimization for search queries
- Add Redis caching for common searches
- Implement rate limiting

### Week 5-12 (Continued Parallel Development)
- Complete all domain-specific pages
- Implement cross-domain query interface
- Build dashboard with real-time updates
- Testing, optimization, deployment preparation

---

**This plan transforms PharmaKG from a backend API into a complete interactive platform with modern search capabilities and an intuitive user interface.**
