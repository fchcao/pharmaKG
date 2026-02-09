// R&D Domain specific types

export interface Compound {
  id: string;
  chemblId: string;
  name: string;
  smiles?: string;
  inchikey?: string;
  molecularWeight?: number;
  logp?: number;
  hbondDonors?: number;
  hbondAcceptors?: number;
  rotatableBonds?: number;
  drugType?: string;
  maxPhase?: number;
  isApproved?: boolean;
  developmentStage?: string;
  description?: string;
  targets?: Target[];
  pathways?: Pathway[];
}

export interface Target {
  id: string;
  chemblId?: string;
  uniprotId: string;
  name: string;
  geneSymbol?: string;
  proteinType?: string;
  organism?: string;
  geneFamily?: string;
  description?: string;
  compounds?: Compound[];
  pathways?: Pathway[];
}

export interface Assay {
  id: string;
  chemblId: string;
  assayType: string;
  assayFormat: string;
  description?: string;
  targets?: Target[];
}

export interface Pathway {
  id: string;
  keggId: string;
  name: string;
  category?: string;
  organism?: string;
  description?: string;
  targets?: Target[];
  compounds?: Compound[];
}

export interface BioactivityData {
  id: string;
  compoundId: string;
  targetId: string;
  activityType: string;
  activityValue: number;
  activityUnit: string;
  confidenceScore?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
