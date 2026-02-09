# Cross-Domain Query Interface

## Overview
The Cross-Domain Query Interface allows users to explore relationships across all four domains of PharmaKG: Research & Development, Clinical Trials, Supply Chain, and Regulatory Compliance.

## Features

### 1. Visual Query Builder
- **Start/End Entity Selection**: Choose any entity type from any domain as the starting and ending points
- **Path Length Control**: Specify the maximum number of hops (1-5) for the query
- **Relationship Filters**: Optionally filter by specific relationship types (67 types available)
- **Domain Selection**: Filter which domains to include in the query

### 2. Pre-built Query Templates
Quick-start templates for common cross-domain scenarios:

- **Drug to Approval**: Trace the complete journey from compound to regulatory approval
  - Path: Compound → ClinicalTrial → Submission → Approval
  - Domains: R&D, Clinical, Regulatory

- **Supply Chain Risk**: Analyze manufacturing risks and potential shortages
  - Path: Manufacturer → Facility → Inspection → ComplianceAction → Shortage
  - Domains: Supply Chain, Regulatory

- **Target Discovery**: Find compounds targeting specific proteins and their clinical outcomes
  - Path: Target → Compound → ClinicalTrial → Outcome
  - Domains: R&D, Clinical

- **Competitive Analysis**: Compare competing drugs and their development status
  - Path: Company → Compound → Trial → Submission → Approval
  - Domains: R&D, Clinical, Regulatory

- **Safety Signal Analysis**: Track safety signals across compounds, trials, and regulatory actions
  - Path: Compound → AdverseEvent → SafetySignal → ComplianceAction
  - Domains: R&D, Clinical, Regulatory

### 3. Results Visualization
- **Interactive Graph Viewer**: Visualize all paths using Cytoscape.js
  - Node styling by entity type and domain
  - Edge styling by relationship type
  - Zoom, pan, and selection capabilities
  - Click on nodes to view entity details

- **Tabular Results**: Detailed table showing all discovered paths
  - Path sequence with entity types
  - Path length (number of hops)
  - Quick link to visualize individual paths

### 4. Query History
- **Automatic Saving**: Recent queries are automatically saved to browser storage
- **Load Previous Queries**: Quickly reload and re-execute previous queries
- **Query Management**: Delete unwanted queries from history

### 5. Export Options
- **PNG Export**: Export graph visualization as high-resolution image
- **CSV Export**: Export path results as spreadsheet-compatible file
- **JSON Export**: Export complete query results for further analysis

### 6. Share Queries
- **URL Generation**: Generate shareable URLs for specific queries
- **Query Parameters**: All query configuration preserved in URL
- **Easy Distribution**: Share URLs with team members for collaborative analysis

## API Integration

The interface integrates with the following backend endpoints:

### Path Finding
- `GET /api/v1/advanced/path/shortest` - Find shortest paths between entities
  - Parameters:
    - `start_entity_type`: Type of starting entity
    - `start_entity_id`: Optional specific entity ID
    - `end_entity_type`: Type of ending entity
    - `end_entity_id`: Optional specific entity ID
    - `max_path_length`: Maximum hops (1-5)
    - `relationship_types`: Optional comma-separated list of relationship types

### Multi-hop Queries
- `GET /api/v1/advanced/multi-hop` - Execute complex multi-hop queries
  - Supports custom Cypher-like query syntax
  - Returns aggregated results across multiple paths

### Subgraph Extraction
- `GET /api/v1/advanced/subgraph/{id}` - Extract subgraph around entity
  - Parameters:
    - `depth`: Number of hops (default: 2)
    - `relationship_types`: Optional relationship type filters

## Usage Examples

### Example 1: Find Drug Approval Path
1. Select template "Drug to Approval"
2. Optionally specify a specific compound ID
3. Click "Execute Query"
4. View results in graph and table formats

### Example 2: Analyze Supply Chain Risk
1. Select template "Supply Chain Risk"
2. Enter manufacturer ID if known
3. Adjust max hops if needed (default: 4)
4. Execute and review potential risk paths

### Example 3: Custom Query
1. Go to "Custom Query" tab
2. Select "Target" as start entity type
3. Select "Disease" as end entity type
4. Set max hops to 3
5. Filter by "R&D" and "Clinical" domains
6. Execute query to discover target-disease associations

## Technical Implementation

### Frontend Components
- **Location**: `/frontend/src/pages/CrossDomainPage.tsx`
- **Dependencies**:
  - Ant Design (UI components)
  - Cytoscape.js (graph visualization)
  - React Router (navigation)
  - Axios (API client)

### State Management
- Local component state for query configuration
- localStorage for query history persistence
- URL query parameters for sharing

### Performance Considerations
- Graph rendering optimized for 1000+ nodes
- Batch updates to prevent UI freezing
- Lazy loading of query history
- Debounced search inputs

## Future Enhancements

### Planned Features
1. **Advanced Query Builder**: Drag-and-drop interface for complex queries
2. **Query Templates Marketplace**: Community-shared query templates
3. **Real-time Collaboration**: Multiple users viewing same query results
4. **Query Execution History**: Track query performance and optimization
5. **Natural Language Query**: NLP-powered query input
6. **Query Optimization**: AI-suggested query improvements

### Potential Improvements
1. **Caching Strategy**: Cache frequently used query results
2. **Incremental Loading**: Load large result sets progressively
3. **Query Validation**: Warn about potentially expensive queries
4. **Result Annotations**: Allow users to annotate and save findings
5. **Batch Operations**: Execute multiple queries simultaneously

## Troubleshooting

### Common Issues

**Issue**: No paths found between entities
- **Solution**: Increase max path length or broaden entity type filters

**Issue**: Query execution timeout
- **Solution**: Reduce max path length or add more specific filters

**Issue**: Graph visualization slow
- **Solution**: Use browser zoom to view smaller sections, or export and view in external tool

**Issue**: History not saving
- **Solution**: Check browser localStorage permissions and available space

## API Reference

### Entity Types by Domain

**R&D Domain**:
- Compound
- Target
- Assay
- Pathway
- Disease

**Clinical Domain**:
- ClinicalTrial
- Condition
- Intervention
- Outcome
- AdverseEvent

**Supply Chain Domain**:
- Manufacturer
- Supplier
- Facility
- DrugProduct
- DrugShortage

**Regulatory Domain**:
- Submission
- Approval
- RegulatoryAgency
- ComplianceAction
- Document

### Relationship Types

Complete list of 67 relationship types available for filtering:
- TARGETS, BINDS_TO, INHIBITS, ACTIVATES, MODULATES
- TREATS, PREVENTS, ASSOCIATED_WITH_DISEASE, BIOMARKER_FOR
- PARTICIPATES_IN, REGULATES_PATHWAY
- TESTED_IN_CLINICAL_TRIAL, REPORTED_ADVERSE_EVENT
- MANUFACTURES, PRODUCES_ACTIVE_INGREDIENT, SUPPLIES_TO
- EXPERIENCES_SHORTAGE, COMPETES_WITH
- SUBMITTED_TO, APPROVED_BY, REQUIRES_INSPECTION
- HAS_SAFETY_SIGNAL, CAUSES_ADVERSE_EVENT, WARNED_ABOUT
- And more...

## Contributing

When adding new features to the cross-domain query interface:

1. Update this documentation with new capabilities
2. Add TypeScript types for new data structures
3. Ensure responsive design for mobile devices
4. Test with large datasets (1000+ nodes)
5. Verify API integration with backend services

## License

Part of the PharmaKG project. See main LICENSE file for details.
