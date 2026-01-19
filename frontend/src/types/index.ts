/**
 * TypeScript type definitions for the application.
 */

// API Request Types
export interface ChatRequest {
  message: string;
  session_id?: string;
  language?: string;
}

export interface PlanRequest {
  city: string;
  duration_days: number;
  interests?: string[];
  pace?: 'relaxed' | 'moderate' | 'fast';
  budget?: string;
  start_date?: string;
  constraints?: Record<string, any>;
}

export interface EditRequest {
  session_id: string;
  edit_command: string;
  edit_type?: string;
}

export interface ExplainRequest {
  session_id: string;
  question: string;
  context?: Record<string, any>;
}

export interface GeneratePDFRequest {
  session_id: string;
  email?: string;
  itinerary_data?: Record<string, any>;
}

// API Response Types
export interface ChatResponse {
  status: 'success' | 'clarifying' | 'error' | 'confirmation_required';
  message?: string;
  itinerary?: Itinerary;
  sources?: Source[];
  evaluation?: Evaluation;
  session_id: string;
  clarifying_questions_count?: number;
  question?: string;
  preferences?: Record<string, any>;
}

export interface PlanResponse {
  status: string;
  itinerary: Itinerary;
  sources: Source[];
  evaluation: Evaluation;
  explanation?: string;
  message?: string;
}

export interface EditResponse {
  status: string;
  edit_type: string;
  modified_section: string;
  itinerary: Itinerary;
  evaluation?: Evaluation;
  explanation?: string;
  previous_travel_time?: number;
  total_travel_time?: number;
}

export interface ExplainResponse {
  status: string;
  explanation: string;
  sources: Source[];
  reasoning?: Record<string, any>;
  alternatives?: Record<string, any>[];
  uncertainty?: boolean;
}

export interface PDFResponse {
  status: string;
  message: string;
  email_sent: boolean;
  pdf_url?: string;
  email_address?: string;
  generated_at?: string;
}

export interface ErrorResponse {
  status: 'error';
  error_type: string;
  message: string;
  details?: Record<string, any>;
  suggestions?: string[];
}

// Itinerary Types
export interface Location {
  lat: number;
  lon: number;
}

export interface Activity {
  activity: string;
  time: string;
  duration_minutes: number;
  travel_time_from_previous?: number;
  location?: Location;
  category?: string;
  source_id?: string;
  description?: string;
  indoor?: boolean;
  note?: string;
  opening_hours?: string;
}

export interface TimeBlock {
  activities: Activity[];
}

export interface DayItinerary {
  morning: TimeBlock;
  afternoon: TimeBlock;
  evening: TimeBlock;
}

export interface Itinerary {
  city: string;
  duration_days: number;
  pace?: string;
  interests?: string[];
  budget?: string;
  travel_dates?: string[];
  travel_mode?: string;
  starting_point?: string;
  day_1?: DayItinerary;
  day_2?: DayItinerary;
  day_3?: DayItinerary;
  total_travel_time?: number;
}

// Source Types
export interface Source {
  type: string;
  poi?: string;
  topic?: string;
  source_id?: string;
  url?: string;
  section?: string;
  snippet?: string;
}

// Evaluation Types
export interface FeasibilityEvaluation {
  is_feasible: boolean;
  score: number;
  violations: string[];
  warnings: string[];
}

export interface GroundingEvaluation {
  is_grounded: boolean;
  score: number;
  missing_citations: string[];
  uncertain_data: string[];
  all_pois_have_sources: boolean;
}

export interface EditCorrectnessEvaluation {
  is_correct: boolean;
  modified_sections: string[];
  unchanged_sections: string[];
  violations: string[];
}

export interface Evaluation {
  feasibility?: FeasibilityEvaluation;
  grounding?: GroundingEvaluation;
  edit_correctness?: EditCorrectnessEvaluation;
}

// Conversation Types
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

// Component Props Types
export interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export interface ItineraryViewProps {
  itinerary: Itinerary | null;
  onExplainActivity?: (activityName: string) => void;
  onGeneratePDF?: () => void;
  isGeneratingPDF?: boolean;
}

export interface TranscriptDisplayProps {
  messages: Message[];
}

export interface SourcesViewProps {
  sources: Source[];
}

export interface ExplanationPanelProps {
  explanation: string | null;
  sources: Source[];
}
