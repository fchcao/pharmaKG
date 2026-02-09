// Clinical Domain specific types

export interface ClinicalTrial {
  id: string;
  nctId: string;
  title: string;
  phase?: string;
  status?: string;
  studyType?: string;
  startDate?: string;
  completionDate?: string;
  enrollment?: number;
  allocation?: string;
  masking?: string;
  purpose?: string;
  conditions?: string[];
  interventions?: Intervention[];
  outcomes?: Outcome[];
  locations?: Location[];
  sponsors?: string[];
  collaborators?: string[];
}

export interface Subject {
  id: string;
  trialId: string;
  subjectId: string;
  age?: number;
  sex?: string;
  condition?: string;
  status?: string;
  enrollmentDate?: string;
  completionDate?: string;
}

export interface Intervention {
  id: string;
  trialId: string;
  interventionType: string;
  name: string;
  description?: string;
  dosage?: string;
  frequency?: string;
  armGroupLabel?: string;
}

export interface Outcome {
  id: string;
  trialId: string;
  outcomeType: string;
  title: string;
  description?: string;
  timeFrame?: string;
  category?: string;
}

export interface Location {
  id: string;
  trialId: string;
  facility: string;
  city?: string;
  state?: string;
  country?: string;
  status?: string;
  latitude?: number;
  longitude?: number;
}

export interface Condition {
  id: string;
  name: string;
  meshId?: string;
  code?: string;
  description?: string;
  trialCount?: number;
  phase?: string;
}

export interface TimelineEvent {
  date: string;
  event: string;
  description?: string;
  category?: 'start' | 'milestone' | 'completion' | 'result';
}
