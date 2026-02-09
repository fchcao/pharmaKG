# Clinical Domain Pages Implementation

## Overview
This directory contains the React components and pages for the Clinical domain of the PharmaKG frontend application. These pages provide comprehensive interfaces for browsing and analyzing clinical trials data from ClinicalTrials.gov.

## Pages Implemented

### 1. Trials Catalog Page (`/clinical/trials`)
**File**: `TrialsPage.tsx`

**Features**:
- Searchable and filterable table of clinical trials
- Advanced filters: phase, status, study type, condition, enrollment
- Grid/Table view toggle
- Quick statistics dashboard showing:
  - Total trials
  - Recruiting trials
  - Active trials
  - Completed trials
  - Total conditions
  - Average enrollment
- Pagination for large datasets
- Real-time trial timeline progress visualization
- Export functionality

**Mock Data**: Uses `mockClinicalTrials` array since domain is currently empty

### 2. Trial Detail Page (`/clinical/trials/:id`)
**File**: `TrialDetailPage.tsx`

**Features**:
- Comprehensive trial information display
- Tabbed interface for:
  - **Overview**: Study design, conditions, timeline, sponsors/collaborators
  - **Interventions**: Detailed information on all trial arms
  - **Outcomes**: Primary and secondary outcome measures
  - **Locations**: List of trial sites with status
  - **Timeline Chart**: Visual timeline using TimelineChart component
- Progress bar showing trial completion status
- Quick actions: view related compounds, locations map, protocol
- External link to ClinicalTrials.gov
- Back navigation to trials catalog

**Mock Data**: Uses `mockTrialDetail` with sample interventions, outcomes, and locations

### 3. Conditions Browser Page (`/clinical/conditions`)
**File**: `ConditionsPage.tsx`

**Features**:
- Searchable list of medical conditions
- Filters: phase, minimum trial count
- Grid/Table view toggle
- Statistics dashboard:
  - Total conditions
  - Phase 3 trials count
  - Active trials
  - Average trials per condition
- Shows condition codes (ICD/Mesh)
- Links to related trials

**Mock Data**: Uses `mockConditions` array with 12 sample conditions

### 4. Interventions Browser Page (`/clinical/interventions`)
**File**: `InterventionsPage.tsx`

**Features**:
- Browse all interventions across trials
- Filters: intervention type, arm group
- Categorized by type:
  - Drug
  - Biological
  - Procedure
  - Genetic
  - Behavioral
  - Device
- Grid/Table view toggle
- Shows dosage, frequency, and arm group info
- Links back to parent trials

**Mock Data**: Uses `mockInterventions` array with 6 sample interventions

## Technical Implementation

### State Management
- Uses React Query (`@tanstack/react-query`) for API data fetching
- Custom hooks in `hooks.ts` for all API calls
- Mock data fallback when API returns empty or errors

### Components Used
- **DataTable**: Shared component for table display with pagination
- **EntityCard**: Shared component for displaying entity information
- **TimelineChart**: Graph visualization component for trial timelines
- **Grid/Card Views**: Custom grid layouts for visual browsing

### API Integration
All pages integrate with the following API endpoints:
- `GET /api/v1/clinical/trials` - List trials with filters
- `GET /api/v1/clinical/trials/{id}` - Trial details
- `GET /api/v1/clinical/trials/{id}/subjects` - Trial subjects
- `GET /api/v1/clinical/trials/{id}/interventions` - Trial interventions
- `GET /api/v1/clinical/trials/{id}/outcomes` - Trial outcomes
- `GET /api/v1/clinical/trials/{id}/locations` - Trial locations
- `GET /api/v1/clinical/conditions` - List conditions
- `GET /api/v1/clinical/interventions` - List interventions
- `GET /api/v1/clinical/statistics` - Domain statistics

### Mock Data
Since the Clinical domain currently has 0 nodes in the knowledge graph, comprehensive mock data is provided in `mockData.ts`:
- 8 sample clinical trials with various phases and statuses
- 12 sample medical conditions
- 6 sample interventions
- Sample locations, outcomes, and timeline events
- Mock statistics for dashboard displays

Users can toggle between mock and real API data using the "Using Mock Data" indicator badge.

## File Structure
```
clinical/
├── TrialsPage.tsx              # Main trials catalog
├── TrialDetailPage.tsx         # Trial detail view
├── ConditionsPage.tsx          # Conditions browser
├── InterventionsPage.tsx       # Interventions browser
├── hooks.ts                    # React Query hooks
├── types.ts                    # TypeScript interfaces
├── mockData.ts                 # Mock data for testing
├── index.ts                    # Exports
└── README.md                   # This file
```

## Styling and UX
- Domain-specific color scheme: Blue (`#2196F3`) as primary
- Responsive design with Ant Design Grid system
- Loading states and error handling
- Empty state handling with helpful messages
- Quick filters and advanced filtering options
- Export functionality for data tables

## Future Enhancements
- Detailed condition and intervention pages
- Interactive map for trial locations
- Trial comparison feature
- Advanced search with boolean operators
- Trial bookmarking and workspace integration
- Real-time trial status updates
- Adverse events integration
- Results data visualization

## Notes
- All pages handle the empty domain gracefully with mock data
- Easy transition to real data once Clinical domain is populated
- Consistent UI patterns with other domain pages
- Fully responsive design
- Accessible with keyboard navigation support
