import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 300000, // 5 minutes for pipeline runs
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<{ detail?: string }>) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred';
        return Promise.reject(new Error(message));
      }
    );
  }

  // Health
  async health() {
    return this.client.get('/health');
  }

  // Overview
  async getOverview() {
    return this.client.get('/overview');
  }

  // Model Performance
  async getModelPerformance() {
    return this.client.get('/model-performance');
  }

  // RAG Classification
  async classify(narrative: string, topK = 3) {
    return this.client.post('/classify', { narrative, top_k: topK });
  }

  // Data Assistant
  async analyze(query: string) {
    return this.client.post('/analyze', { query });
  }

  // Alerts
  async getAlerts(limit = 50) {
    return this.client.get('/alerts', { params: { limit } });
  }

  // System Control
  async getSystemStatus() {
    return this.client.get('/system/status');
  }

  async controlService(service: string, action: 'start' | 'stop' | 'restart') {
    return this.client.post(`/system/control/${service}/${action}`);
  }

  async controlAllServices(action: 'start' | 'stop' | 'restart') {
    return this.client.post(`/system/control/all/${action}`);
  }

  // Pipeline
  async runPipeline(options: {
    force_refresh?: boolean;
    no_fetch?: boolean;
    no_rag?: boolean;
    samples?: number;
    stages?: string[];
  }) {
    return this.client.post('/pipeline/run', options);
  }

  async getPipelineProgress() {
    return this.client.get('/pipeline/progress');
  }

  async fetchData(options: {
    force_refresh?: boolean;
    nrows_aviation?: number;
  }) {
    return this.client.post('/pipeline/fetch', options);
  }

  async trainModel(options: {
    max_features?: number;
    ngram_range?: number[];
    test_size?: number;
    cv_folds?: number;
    alphas?: number[];
    class_weights?: (string | null)[];
    max_iter?: number;
  }) {
    return this.client.post('/pipeline/train', options);
  }

  // Monitor
  async controlMonitor(action: 'start' | 'stop' | 'restart', pollSeconds = 60, enableApi = true) {
    return this.client.post('/monitor/control', { action, poll_seconds: pollSeconds, enable_api: enableApi });
  }
}

export const api = new ApiClient();
export default api;