import { useEffect, useCallback, useState } from 'react';
import { api } from '@/api/client';
import { useDataStore, useUIStore } from '@/store';

export function useOverview() {
  const { overview, loading, error, setOverview, setLoading, setError } = useDataStore();
  const { addNotification } = useUIStore();

  const fetchOverview = useCallback(async () => {
    setLoading('overview', true);
    try {
      const response = await api.getOverview();
      setOverview(response.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load overview';
      setError('overview', message);
      addNotification({ type: 'error', message });
    }
  }, [setOverview, setLoading, setError, addNotification]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  return { data: overview, loading: loading.overview, error: error.overview, refetch: fetchOverview };
}

export function useModelPerformance() {
  const { modelPerformance, loading, error, setModelPerformance, setLoading, setError } = useDataStore();
  const { addNotification } = useUIStore();

  const fetchModelPerformance = useCallback(async () => {
    setLoading('modelPerformance', true);
    try {
      const response = await api.getModelPerformance();
      setModelPerformance(response.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load model performance';
      setError('modelPerformance', message);
      addNotification({ type: 'error', message });
    }
  }, [setModelPerformance, setLoading, setError, addNotification]);

  useEffect(() => {
    fetchModelPerformance();
  }, [fetchModelPerformance]);

  return { data: modelPerformance, loading: loading.modelPerformance, error: error.modelPerformance, refetch: fetchModelPerformance };
}

export function useAlerts(limit = 50) {
  const { alerts, loading, error, setAlerts, setLoading, setError } = useDataStore();
  const { addNotification } = useUIStore();

  const fetchAlerts = useCallback(async () => {
    setLoading('alerts', true);
    try {
      const response = await api.getAlerts(limit);
      setAlerts(response.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load alerts';
      setError('alerts', message);
      addNotification({ type: 'error', message });
    }
  }, [limit, setAlerts, setLoading, setError, addNotification]);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  return { data: alerts, loading: loading.alerts, error: error.alerts, refetch: fetchAlerts };
}

export function useSystemStatus() {
  const { systemStatus, loading, error, setSystemStatus, setLoading, setError } = useDataStore();
  const { addNotification } = useUIStore();

  const fetchSystemStatus = useCallback(async () => {
    setLoading('systemStatus', true);
    try {
      const response = await api.getSystemStatus();
      setSystemStatus(response.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load system status';
      setError('systemStatus', message);
      addNotification({ type: 'error', message });
    }
  }, [setSystemStatus, setLoading, setError, addNotification]);

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [fetchSystemStatus]);

  return { data: systemStatus, loading: loading.systemStatus, error: error.systemStatus, refetch: fetchSystemStatus };
}

export function useClassify() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addNotification } = useUIStore();

  const classify = useCallback(async (narrative: string, topK = 3) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.classify(narrative, topK);
      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Classification failed';
      setError(message);
      addNotification({ type: 'error', message });
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  return { classify, loading, error };
}

export function useAnalyze() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addNotification } = useUIStore();

  const analyze = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.analyze(query);
      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
      addNotification({ type: 'error', message });
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  return { analyze, loading, error };
}

export function usePipeline() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<Array<{ stage: string; status: string; progress: number; message: string }>>([]);
  const { addNotification } = useUIStore();

  const runPipeline = useCallback(async (options: {
    force_refresh?: boolean;
    no_fetch?: boolean;
    no_rag?: boolean;
    samples?: number;
    stages?: string[];
  }) => {
    setLoading(true);
    setError(null);
    setProgress([
      { stage: 'fetch', status: 'pending', progress: 0, message: 'Queued' },
      { stage: 'preprocess', status: 'pending', progress: 0, message: 'Queued' },
      { stage: 'train', status: 'pending', progress: 0, message: 'Queued' },
      { stage: 'evaluate', status: 'pending', progress: 0, message: 'Queued' },
      { stage: 'rag', status: 'pending', progress: 0, message: 'Queued' },
      { stage: 'report', status: 'pending', progress: 0, message: 'Queued' },
    ]);
    try {
      const response = await api.runPipeline(options);
      // Start polling for progress
      const pollProgress = async () => {
        try {
          const progRes = await api.getPipelineProgress();
          setProgress(progRes.data);
          if (progRes.data.some((s: any) => s.status === 'running' || s.status === 'pending')) {
            setTimeout(pollProgress, 2000);
          } else {
            // Final result
            addNotification({ type: response.data.success ? 'success' : 'error', message: response.data.message });
          }
        } catch (e) {
          console.error('Progress poll failed:', e);
        }
      };
      setTimeout(pollProgress, 1000);
      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Pipeline failed';
      setError(message);
      addNotification({ type: 'error', message });
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  const fetchData = useCallback(async (options: { force_refresh?: boolean; nrows_aviation?: number }) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.fetchData(options);
      if (response.data.success) {
        addNotification({ type: 'success', message: 'Data fetch completed' });
      } else {
        addNotification({ type: 'error', message: response.data.message });
      }
      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Fetch failed';
      setError(message);
      addNotification({ type: 'error', message });
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  const trainModel = useCallback(async (options: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.trainModel(options);
      if (response.data.success) {
        addNotification({ type: 'success', message: 'Model training completed' });
      } else {
        addNotification({ type: 'error', message: response.data.message });
      }
      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Training failed';
      setError(message);
      addNotification({ type: 'error', message });
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  return { runPipeline, fetchData, trainModel, loading, error, progress };
}

export function useServiceControl() {
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const { addNotification } = useUIStore();

  const controlService = useCallback(async (service: string, action: 'start' | 'stop' | 'restart') => {
    setLoading((prev) => ({ ...prev, [service]: true }));
    try {
      const response = await api.controlService(service, action);
      addNotification({ 
        type: response.data.success ? 'success' : 'error', 
        message: response.data.message 
      });
      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : `Failed to ${action} ${service}`;
      addNotification({ type: 'error', message });
      throw err;
    } finally {
      setLoading((prev) => ({ ...prev, [service]: false }));
    }
  }, [addNotification]);

  const controlAll = useCallback(async (action: 'start' | 'stop' | 'restart') => {
    setLoading((prev) => ({ ...prev, all: true }));
    try {
      const response = await api.controlAllServices(action);
      addNotification({ 
        type: response.data.success ? 'success' : 'error', 
        message: response.data.message 
      });
      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : `Failed to ${action} all services`;
      addNotification({ type: 'error', message });
      throw err;
    } finally {
      setLoading((prev) => ({ ...prev, all: false }));
    }
  }, [addNotification]);

  return { controlService, controlAll, loading };
}

export function useMonitorControl() {
  const [loading, setLoading] = useState(false);
  const { addNotification } = useUIStore();

  const controlMonitor = useCallback(async (action: 'start' | 'stop' | 'restart', pollSeconds = 60, enableApi = true) => {
    setLoading(true);
    try {
      const response = await api.controlMonitor(action, pollSeconds, enableApi);
      addNotification({ 
        type: response.data.success ? 'success' : 'error', 
        message: response.data.message 
      });
      return response.data;
    } catch (err) {
      const message = err instanceof Error ? err.message : `Failed to ${action} monitor`;
      addNotification({ type: 'error', message });
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  return { controlMonitor, loading };
}