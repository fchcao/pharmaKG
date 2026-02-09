/**
 * Type definitions for PharmaKG graph visualization
 */

export type EntityType =
  | 'Compound'
  | 'Target'
  | 'Assay'
  | 'Drug'
  | 'Protein'
  | 'Gene'
  | 'Pathway'
  | 'Disease'
  | 'ClinicalTrial'
  | 'Manufacturer'
  | 'Supplier'
  | 'Facility'
  | 'Submission'
  | 'Approval'
  | 'RegulatoryAgency'
  | 'Document'
  | 'Patent';

export type RelationType =
  | 'TARGETS'
  | 'BINDS_TO'
  | 'INHIBITS'
  | 'ACTIVATES'
  | 'PARTICIPATES_IN'
  | 'ASSOCIATED_WITH'
  | 'MANUFACTURES'
  | 'SUPPLIES'
  | 'SUBMITTED_TO'
  | 'APPROVED_BY'
  | 'CONDUCTS_AT'
  | 'REFERENCES';

export interface GraphNode {
  id: string;
  label: string;
  type: EntityType;
  properties?: Record<string, any>;
  x?: number;
  y?: number;
  weight?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type: RelationType;
  properties?: Record<string, any>;
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface PathResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  length: number;
  path: string[];
}

export interface SubgraphQuery {
  centerNodeId: string;
  depth: number;
  relationshipTypes?: RelationType[];
  limit?: number;
}

export interface TimelineDataPoint {
  date: string;
  count: number;
  category?: string;
}

export interface EntityStyleConfig {
  backgroundColor: string;
  borderColor?: string;
  shape: 'ellipse' | 'rectangle' | 'roundrectangle' | 'triangle' | 'diamond';
  width: number;
  height: number;
  fontSize: number;
  labelColor?: string;
}

export const ENTITY_STYLES: Record<EntityType, EntityStyleConfig> = {
  Compound: {
    backgroundColor: '#4CAF50',
    borderColor: '#2E7D32',
    shape: 'ellipse',
    width: 60,
    height: 60,
    fontSize: 12,
    labelColor: '#FFFFFF'
  },
  Target: {
    backgroundColor: '#2196F3',
    borderColor: '#1565C0',
    shape: 'roundrectangle',
    width: 50,
    height: 40,
    fontSize: 11,
    labelColor: '#FFFFFF'
  },
  Assay: {
    backgroundColor: '#FF9800',
    borderColor: '#E65100',
    shape: 'rectangle',
    width: 45,
    height: 35,
    fontSize: 10,
    labelColor: '#FFFFFF'
  },
  Drug: {
    backgroundColor: '#9C27B0',
    borderColor: '#6A1B9A',
    shape: 'ellipse',
    width: 55,
    height: 55,
    fontSize: 11,
    labelColor: '#FFFFFF'
  },
  Protein: {
    backgroundColor: '#00BCD4',
    borderColor: '#00838F',
    shape: 'roundrectangle',
    width: 50,
    height: 40,
    fontSize: 11,
    labelColor: '#FFFFFF'
  },
  Gene: {
    backgroundColor: '#00BCD4',
    borderColor: '#00838F',
    shape: 'rectangle',
    width: 45,
    height: 35,
    fontSize: 10,
    labelColor: '#FFFFFF'
  },
  Pathway: {
    backgroundColor: '#FFC107',
    borderColor: '#FF8F00',
    shape: 'diamond',
    width: 70,
    height: 50,
    fontSize: 11,
    labelColor: '#000000'
  },
  Disease: {
    backgroundColor: '#F44336',
    borderColor: '#C62828',
    shape: 'ellipse',
    width: 55,
    height: 55,
    fontSize: 11,
    labelColor: '#FFFFFF'
  },
  ClinicalTrial: {
    backgroundColor: '#E91E63',
    borderColor: '#AD1457',
    shape: 'roundrectangle',
    width: 60,
    height: 45,
    fontSize: 11,
    labelColor: '#FFFFFF'
  },
  Manufacturer: {
    backgroundColor: '#795548',
    borderColor: '#4E342E',
    shape: 'rectangle',
    width: 65,
    height: 45,
    fontSize: 11,
    labelColor: '#FFFFFF'
  },
  Supplier: {
    backgroundColor: '#607D8B',
    borderColor: '#37474F',
    shape: 'rectangle',
    width: 60,
    height: 40,
    fontSize: 11,
    labelColor: '#FFFFFF'
  },
  Facility: {
    backgroundColor: '#8BC34A',
    borderColor: '#558B2F',
    shape: 'roundrectangle',
    width: 55,
    height: 45,
    fontSize: 10,
    labelColor: '#000000'
  },
  Submission: {
    backgroundColor: '#FF5722',
    borderColor: '#BF360C',
    shape: 'diamond',
    width: 50,
    height: 50,
    fontSize: 10,
    labelColor: '#FFFFFF'
  },
  Approval: {
    backgroundColor: '#4CAF50',
    borderColor: '#1B5E20',
    shape: 'triangle',
    width: 55,
    height: 55,
    fontSize: 10,
    labelColor: '#FFFFFF'
  },
  RegulatoryAgency: {
    backgroundColor: '#3F51B5',
    borderColor: '#1A237E',
    shape: 'rectangle',
    width: 70,
    height: 50,
    fontSize: 11,
    labelColor: '#FFFFFF'
  },
  Document: {
    backgroundColor: '#9E9E9E',
    borderColor: '#424242',
    shape: 'rectangle',
    width: 50,
    height: 40,
    fontSize: 10,
    labelColor: '#FFFFFF'
  },
  Patent: {
    backgroundColor: '#FF9800',
    borderColor: '#E65100',
    shape: 'rectangle',
    width: 55,
    height: 45,
    fontSize: 10,
    labelColor: '#FFFFFF'
  }
};

export const RELATION_STYLES: Record<RelationType, { color: string; width: number; style: string }> = {
  TARGETS: { color: '#1976D2', width: 2, style: 'solid' },
  BINDS_TO: { color: '#388E3C', width: 2, style: 'solid' },
  INHIBITS: { color: '#D32F2F', width: 3, style: 'solid' },
  ACTIVATES: { color: '#7B1FA2', width: 3, style: 'solid' },
  PARTICIPATES_IN: { color: '#F57C00', width: 2, style: 'dashed' },
  ASSOCIATED_WITH: { color: '#0097A7', width: 2, style: 'dotted' },
  MANUFACTURES: { color: '#5D4037', width: 2, style: 'solid' },
  SUPPLIES: { color: '#455A64', width: 2, style: 'solid' },
  SUBMITTED_TO: { color: '#C2185B', width: 2, style: 'solid' },
  APPROVED_BY: { color: '#2E7D32', width: 3, style: 'solid' },
  CONDUCTS_AT: { color: '#00838F', width: 2, style: 'dashed' },
  REFERENCES: { color: '#757575', width: 1, style: 'dotted' }
};

export interface GraphViewerProps {
  data: GraphData;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  onBackgroundClick?: () => void;
  height?: string | number;
  width?: string | number;
  selectable?: boolean;
  zoomEnabled?: boolean;
  panEnabled?: boolean;
}

export interface GraphViewerRef {
  cy: any;
  fit: (padding?: number) => void;
  center: () => void;
  zoom: (level: number) => void;
  exportAs: (format: 'png' | 'jpg' | 'json') => string | void;
  getSelectedElements: () => any[];
  clearSelection: () => void;
}
