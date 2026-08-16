export interface EvidenceItem {
  rank: number;
  similarity: number;
  label: string;
  domain: string;
  snippet: string;
}

export interface ClassifyResponse {
  predicted_label: string;
  evidence: EvidenceItem[];
  processing_time_ms: number;
}

export interface DatasetStats {
  total_reports: number;
  domains: Record<string, number>;
  anomaly_classes: number;
  class_distribution: Record<string, number>;
}

export interface ClassificationReportRow {
  class_name: string;
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface ModelMetrics {
  accuracy: number;
  n_classes: number;
  test_size: number;
  best_cv_f1?: number;
  training_config?: Record<string, any>;
}

export interface ModelPerformanceResponse {
  metrics: ModelMetrics;
  classification_report: ClassificationReportRow[];
  confusion_matrix_url?: string;
  class_distribution_url?: string;
}

export interface DataAssistantResponse {
  lines: string[];
}

export interface AlertItem {
  timestamp: string;
  incident_id: string;
  source: string;
  risk_level: 'critical' | 'high' | 'medium';
  predicted_label: string;
  narrative: string;
  evidence: EvidenceItem[];
}

export interface AlertsResponse {
  counts: Record<string, number>;
  alerts: AlertItem[];
  total: number;
}

export interface ServiceStatus {
  name: string;
  label: string;
  description: string;
  running: boolean;
  pid?: number;
}

export interface SystemControlResponse {
  services: ServiceStatus[];
  logs: Record<string, string[]>;
}

export interface PipelineRunResponse {
  success: boolean;
  message: string;
  duration_seconds?: number;
  artifacts?: Record<string, string>;
}

export interface HealthResponse {
  status: string;
  version: string;
  model_loaded: boolean;
  data_loaded: boolean;
}