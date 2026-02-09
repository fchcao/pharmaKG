# Graph Visualization Components

High-performance, interactive graph visualization components for PharmaKG, built with Cytoscape.js and Chart.js.

## Components

### 1. GraphViewer

Main graph visualization component using Cytoscape.js with the COSE-Bilkent layout algorithm.

**Features:**
- Optimized for rendering 1000+ nodes smoothly (< 1 second render time)
- Force-directed layout with customizable parameters
- Entity type styling (17 different entity types with distinct colors/shapes)
- Zoom and pan controls
- Node/edge selection with visual feedback
- Export to PNG/JPG/JSON formats
- Responsive design with automatic resize handling

**Usage:**
```tsx
import { GraphViewer } from '@/shared/graphs';

const data = {
  nodes: [
    { id: '1', label: 'Aspirin', type: 'Compound' },
    { id: '2', label: 'COX-1', type: 'Target' }
  ],
  edges: [
    { id: 'e1', source: '1', target: '2', type: 'TARGETS' }
  ]
};

<GraphViewer
  data={data}
  height="600px"
  onNodeClick={(node) => console.log('Clicked:', node)}
/>
```

**Entity Styling:**
- **Compound**: Green ellipse (60px)
- **Target**: Blue rounded rectangle (50px)
- **Assay**: Orange rectangle (45px)
- **Drug**: Purple ellipse (55px)
- **ClinicalTrial**: Pink rounded rectangle (60px)
- And 11 more entity types with distinct visual styles

### 2. SubgraphExplorer

Interactive neighborhood exploration with depth control and relationship filtering.

**Features:**
- Depth control slider (1-5 hops)
- Relationship type filters (12 types)
- Entity type filters
- Expand/collapse functionality
- Export subgraph data
- Real-time statistics display

**Usage:**
```tsx
import { SubgraphExplorer } from '@/shared/graphs';

<SubgraphExplorer
  initialCenterNode="CHEMBL25"
  apiBaseUrl="/api/v1"
  height={700}
  onNodeClick={(node) => handleNodeSelect(node)}
  onExport={(data) => saveSubgraph(data)}
/>
```

**Performance:**
- Fetches subgraph data from API
- Renders up to 2000 nodes with filters
- Lazy loading for large neighborhoods
- Batch rendering for smooth UX

### 3. PathVisualizer

Visualize and animate paths between entities in the knowledge graph.

**Features:**
- Find multiple paths between nodes
- Animated path traversal
- Step-by-step navigation
- Path comparison (up to 10 paths)
- Detailed step information
- Export path data

**Usage:**
```tsx
import { PathVisualizer } from '@/shared/graphs';

<PathVisualizer
  apiBaseUrl="/api/v1"
  height={600}
  onNodeClick={(node) => showNodeDetails(node)}
  onExport={(path) => savePath(path)}
/>
```

**Animation Controls:**
- Play/Pause animation
- Step forward/backward
- Adjustable speed (0.5s - 2s per step)
- Click on steps to jump directly

### 4. TimelineChart

Temporal visualization of pharmaceutical events using Chart.js.

**Features:**
- Multiple chart types (line, bar, doughnut)
- Data source selection (submissions, trials, approvals, all)
- Date range filtering
- Aggregation control (day, week, month, quarter, year)
- Interactive tooltips
- Export data/image

**Usage:**
```tsx
import { TimelineChart } from '@/shared/graphs';

<TimelineChart
  apiBaseUrl="/api/v1"
  height={400}
  onDataPointClick={(point) => showDetails(point)}
  onExport={(data) => saveTimeline(data)}
/>
```

**Statistics Display:**
- Total events
- Average per period
- Peak count
- Minimum count

## Performance Metrics

Based on testing with 1000 nodes and 2000 edges:

| Operation | Time | Notes |
|-----------|------|-------|
| Initialization | ~50ms | One-time setup cost |
| Data Loading | ~200ms | Including API call |
| Graph Rendering | ~400ms | Cytoscape layout |
| Animation Frame | ~16ms | 60fps smooth zoom/pan |

**Optimization Techniques:**
- Batch element operations
- Virtualized rendering for large graphs
- Efficient layout caching
- Debounced resize handling
- Memoized style calculations

## API Integration

All components integrate with the PharmaKG REST API:

```
GET /api/v1/advanced/subgraph/{nodeId}
  ?depth={1-5}
  &limit={max nodes}
  &relation_types={comma-separated list}
  &entity_types={comma-separated list}

GET /api/v1/advanced/paths
  ?source={nodeId}
  &target={nodeId}
  &max_paths={1-10}
  &max_length={1-6}

GET /api/v1/{domain}/timeline
  &start_date={YYYY-MM-DD}
  &end_date={YYYY-MM-DD}
  &aggregation={day|week|month|quarter|year}
```

## Styling System

### Entity Types
17 entity types with predefined styles:
- Color coding (HSL color space for visual distinction)
- Shape semantics (ellipse=entities, rectangle=processes, diamond=decisions)
- Size hierarchy (important types are larger)
- Label readability (auto-contrast text color)

### Relationship Types
12 relationship types with distinct styles:
- Color coding by semantic type
- Line width indicates importance
- Line style indicates certainty (solid=certain, dashed=inferred, dotted=weak)
- Directional arrows for asymmetric relations

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Dependencies

```json
{
  "cytoscape": "^3.28.1",
  "cytoscape-cose-bilkent": "^4.1.0",
  "chart.js": "^4.4.1",
  "react-chartjs-2": "^5.2.0",
  "antd": "^5.12.8",
  "@ant-design/icons": "^5.2.6"
}
```

## Future Enhancements

1. **3D Visualization**: Three.js integration for spatial layouts
2. **Collaborative Features**: Multi-user cursors and annotations
3. **Advanced Layouts**: Hierarchical, circular, and organic layouts
4. **Real-time Updates**: WebSocket integration for live data
5. **VR/AR Support**: WebXR for immersive exploration

## Development

Run the development server:
```bash
cd frontend
npm install
npm run dev
```

Build for production:
```bash
npm run build
```

## License

Copyright © 2024 PharmaKG. All rights reserved.
