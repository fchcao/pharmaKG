# PharmaKG Frontend

Pharmaceutical Knowledge Graph Visualization Platform - Modern React TypeScript frontend.

## Tech Stack

- **Framework**: React 18.2 with TypeScript 5.3
- **Build Tool**: Vite 5.0
- **UI Library**: Ant Design 5.12
- **Routing**: React Router DOM 6.21
- **State Management**: Zustand 4.5
- **Data Fetching**: TanStack React Query 5.17
- **Graph Visualization**: Cytoscape.js 3.28 with COSE-Bilkent layout
- **Charts**: Chart.js 4.4
- **HTTP Client**: Axios 1.6
- **Styling**: Tailwind CSS 3.4

## Project Structure

```
frontend/
├── src/
│   ├── domains/              # Domain-specific pages and types
│   │   ├── research/         # R&D domain (compounds, targets, pathways)
│   │   ├── clinical/         # Clinical trials domain
│   │   ├── supply/           # Supply chain domain
│   │   └── regulatory/       # Regulatory domain
│   ├── layouts/              # Layout components
│   │   └── MainLayout.tsx    # Main app layout with navigation
│   ├── pages/                # Top-level pages
│   │   └── HomePage.tsx      # Home/dashboard page
│   ├── shared/               # Shared utilities and components
│   │   ├── api/              # API client configuration
│   │   ├── components/       # Reusable UI components
│   │   ├── graphs/           # Graph visualization components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── search/           # Search functionality
│   │   ├── types/            # TypeScript type definitions
│   │   └── utils/            # Utility functions
│   ├── App.tsx               # Root component with routing
│   ├── main.tsx              # Application entry point
│   └── index.css             # Global styles with Tailwind
├── public/                   # Static assets
├── index.html                # HTML template
├── package.json              # Dependencies and scripts
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Tailwind CSS configuration
└── .eslintrc.json            # ESLint configuration
```

## Development Setup

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running on port 8000 (or configure via env)

### Installation

```bash
cd frontend
npm install
```

### Environment Configuration

Create `.env.development`:

```
VITE_API_BASE_URL=http://localhost:8000
```

### Development Server

```bash
npm run dev
```

Access at: http://localhost:3000

### Build for Production

```bash
npm run build
```

Output: `dist/` directory

### Preview Production Build

```bash
npm run preview
```

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm run test` - Run Vitest tests

## Key Features

### Domain-Specific Pages

Each domain has dedicated pages:
- **R&D**: Compounds, Targets, Assays, Pathways
- **Clinical**: Trials, Conditions, Interventions
- **Supply Chain**: Manufacturers, Facilities, Shortages
- **Regulatory**: Submissions, Approvals, Documents

### Graph Visualization

- GraphViewer: Interactive force-directed graph
- SubgraphExplorer: Neighborhood exploration
- PathVisualizer: Path finding and visualization
- TimelineChart: Temporal data visualization

### Shared Components

- DataTable: Sortable, filterable data tables
- EntityCard: Entity display cards
- RelationshipViewer: Relationship visualization
- SearchBar: Global search with autocomplete

## API Integration

The frontend connects to the PharmaKG backend API:

- Base URL: Configured via `VITE_API_BASE_URL`
- Proxy: Development proxy to backend on port 8000
- Authentication: Token-based (stored in localStorage)
- Error Handling: Global interceptors with user feedback

## TypeScript Configuration

- Strict mode enabled
- Path aliases: `@/*` maps to `src/*`
- Module resolution: Bundler (Vite)
- JSX: react-jsx transform

## Tailwind CSS

- Utility-first CSS framework
- Custom theme with domain-specific colors
- Ant Design compatibility
- Responsive utilities

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ features
- CSS Grid and Flexbox

## Performance Optimizations

- Code splitting by domain and vendor
- Lazy loading for heavy components
- Virtual scrolling for large datasets
- Memoization for expensive computations

## Development Guidelines

### Component Structure

```typescript
import React from 'react';
import { Card, Typography } from 'antd';

const { Title } = Typography;

interface MyComponentProps {
  title: string;
  data: DataType[];
}

export const MyComponent: React.FC<MyComponentProps> = ({ title, data }) => {
  return (
    <Card title={title}>
      {/* Component content */}
    </Card>
  );
};

export default MyComponent;
```

### Type Definitions

Place domain-specific types in `src/domains/{domain}/types.ts`
Shared types go in `src/shared/types/index.ts`

### Styling

- Use Ant Design components for UI
- Use Tailwind utilities for layout and spacing
- Custom styles in component files or `index.css`

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 3000
npx kill-port 3000
# or use a different port
npm run dev -- --port 3001
```

### Module Not Found

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors

```bash
# Regenerate type definitions
npm run build -- --mode development
```

## Contributing

When adding new features:

1. Create components in appropriate domain directories
2. Add types to domain type files
3. Export from domain index.ts
4. Add routes in App.tsx
5. Update shared types if needed

## License

Part of the PharmaKG project.
