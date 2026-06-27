export type Locale = "vi" | "en";

export interface InvestigationRequest {
  text: string;
  locale?: Locale;
  use_web_search?: boolean;
}

export type InvestigationStatus = "completed" | "partial" | "failed";

export type RiskLabel = "low" | "uncertain" | "suspicious" | "high_risk" | "critical";

export type FastCheckRiskBand = RiskLabel;

export type FastCheckSeverity = "medium" | "high" | "critical";

export interface FastCheckFlag {
  code: string;
  label: string;
  severity: FastCheckSeverity;
  evidence_span: string;
}

export interface FastCheckResponse {
  request_id: string;
  risk_band: FastCheckRiskBand;
  score: number;
  triggered_flags: FastCheckFlag[];
  message: string;
  immediate_actions: string[];
  latency_ms: number;
}

export interface EvidenceItem {
  evidence_id: string;
  title: string;
  url: string;
  source_name: string;
  published_at?: string | null;
  snippet: string;
  retrieved_at: string;
  credibility_score: number;
  relevance_score: number;
  [key: string]: unknown;
}

export interface ExpertAssessment {
  expert: string;
  cited_evidence_ids: string[];
  [key: string]: unknown;
}

export interface EvidenceStatus {
  provider: string;
  mode: "live" | "mock" | "disabled" | "failed";
  operation_status?: "completed" | "partial" | "disabled";
  success: boolean;
  queries_attempted: number;
  results_returned: number;
  errors: string[];
}

export interface BehavioralRedFlag {
  type: string;
  severity: "low" | "medium" | "high";
  evidence_span: string;
  explanation: string;
}

export interface BehavioralAnalysis {
  red_flags: BehavioralRedFlag[];
  behavioral_risk_score: number;
  summary: string;
}

export interface ExpertConsensusReport {
  consensus_score: number;
  consensus_label: string;
  supported_findings: string[];
  disagreements: string[];
  missing_evidence: string[];
}

export interface InvestigationReport extends Record<string, unknown> {
  status?: InvestigationStatus;
  conclusion?: string;
  risk_score?: number;
  risk_label?: RiskLabel;
  confidence_score?: number;
  why?: string[];
  evidence?: EvidenceItem[];
  expert_consensus?: ExpertConsensusReport;
  behavioral_red_flags?: BehavioralRedFlag[];
  actions?: string[];
  limitations?: string[];
  markdown?: string;
}

export interface VerificationResult {
  risk_score: number;
  risk_label: RiskLabel;
  confidence_score: number;
  [key: string]: unknown;
}

export interface InvestigationResponse {
  investigation_id: string;
  status: InvestigationStatus;
  evidence?: EvidenceItem[];
  experts?: ExpertAssessment[];
  evidence_status?: EvidenceStatus;
  behavioral_analysis?: BehavioralAnalysis;
  verification: VerificationResult;
  report: InvestigationReport;
  warnings: string[];
  timings_ms: Record<string, number>;
  [key: string]: unknown;
}
