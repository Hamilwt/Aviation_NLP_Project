import { useState, useEffect } from 'react';
import { useSystemStatus, useServiceControl, usePipeline } from '@/hooks/useApi';
import { Section, Card, CardHeader, Button, Badge, ProgressBar } from '@/components/ui';
import { Loader2, Play, Square, Zap, AlertTriangle, CheckCircle, XCircle, RefreshCw, RotateCcw, Download, Database, Bell } from 'lucide-react';
import { cn } from '@/utils/helpers';

export function SystemPage() {
  const { data, loading, error, refetch } = useSystemStatus();
  const { controlService, controlAll, loading: controlLoading } = useServiceControl();
  const { runPipeline, loading: pipelineLoading } = usePipeline();
  const [pipelineOptions, setPipelineOptions] = useState({
    force_refresh: false,
    no_fetch: false,
    no_rag: false,
    samples: 100,
  });
  const [pipelineResult, setPipelineResult] = useState<{
    success: boolean;
    message: string;
    duration_seconds?: number;
    stages: Array<{ stage: string; status: string; progress: number; message: string }>;
    artifacts?: Record<string, string>;
  } | null>(null);
  const [activeLogTab, setActiveLogTab] = useState<string>('pipeline');
  const [pipelineProgress, setPipelineProgress] = useState<Array<{ stage: string; status: string; progress: number; message: string }>>([]);
  const [pollProgress, setPollProgress] = useState(false);

  // Poll for pipeline progress
  useEffect(() => {
    if (!pollProgress) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/pipeline/progress');
        if (res.ok) {
          const data = await res.json();
          setPipelineProgress(data);
          if (data.every((s: any) => s.status === 'completed' || s.status === 'failed')) {
            setPollProgress(false);
          }
        }
      } catch (e) {
        console.error('Progress poll failed:', e);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [pollProgress]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-brown-500 animate-spin" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <Card className="text-center py-12">
        <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-brown-800 text-lg font-medium mb-2">Unable to load system status</h3>
        <p className="text-brown-500 mb-4">{error}</p>
        <button onClick={refetch} className="px-4 py-2 bg-brown-700 text-white rounded-lg hover:bg-brown-800">
          Try Again
        </button>
      </Card>
    );
  }

  const services = data?.services || [];
  const logs = data?.logs || {};

  const handleStartPipeline = async () => {
    setPollProgress(true);
    setPipelineProgress([
      { stage: 'fetch', status: 'running', progress: 0, message: 'Starting...' },
      { stage: 'preprocess', status: 'pending', progress: 0, message: 'Waiting...' },
      { stage: 'train', status: 'pending', progress: 0, message: 'Waiting...' },
      { stage: 'evaluate', status: 'pending', progress: 0, message: 'Waiting...' },
      { stage: 'rag', status: 'pending', progress: 0, message: 'Waiting...' },
      { stage: 'report', status: 'pending', progress: 0, message: 'Waiting...' },
    ]);
    
    try {
      const result = await runPipeline(pipelineOptions);
      setPipelineResult({
        success: result.success,
        message: result.message,
        duration_seconds: result.duration_seconds,
        stages: pipelineProgress,
        artifacts: result.artifacts,
      });
      setPollProgress(false);
      refetch();
    } catch (err) {
      setPollProgress(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'running': return <RotateCcw className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-600" />;
      default: return <span className="w-4 h-4 text-brown-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#22C55E';
      case 'running': return '#3B82F6';
      case 'failed': return '#EF4444';
      default: return '#D9C5B2';
    }
  };

  return (
    <div className="space-y-6">
      <Section
        title="System Control"
        subtitle="Manage pipeline and monitor processes"
        action={
          <Button variant="outline" onClick={refetch} loading={loading}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader title="Service Controls" subtitle="Start/stop pipeline and monitor services" />
            
            <div className="space-y-4">
              {services.map((service: { name: string; label: string; description: string; running: boolean; pid?: number }) => (
                <div key={service.name} className="p-4 rounded-lg border border-cream-300 bg-cream-50">
                  <div className="flex items-center justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-brown-100 flex items-center justify-center">
                        {service.name === 'pipeline' ? <Database className="w-5 h-5 text-brown-600" /> : <Bell className="w-5 h-5 text-brown-600" />}
                      </div>
                      <div>
                        <h4 className="font-semibold text-brown-800">{service.label}</h4>
                        <p className="text-sm text-brown-600">{service.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={service.running ? 'success' : 'default'} size="md" className="px-3 py-1">
                        {service.running ? 'RUNNING' : 'STOPPED'}
                      </Badge>
                      {service.pid && (
                        <span className="text-xs text-brown-400 font-mono px-2 py-1 bg-cream-100 rounded">PID: {service.pid}</span>
                      )}
                    </div>
                  </div>
<div className="flex gap-2">
                      {!service.running ? (
                        <Button
                          size="sm"
                          onClick={() => controlService(service.name, 'start')}
                          loading={controlLoading[service.name]}
                          disabled={controlLoading[service.name]}
                          className="flex-1"
                        >
                          <Play className="w-4 h-4" />
                          Start
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => controlService(service.name, 'stop')}
                          loading={controlLoading[service.name]}
                          disabled={controlLoading[service.name]}
                          className="flex-1"
                        >
                          <Square className="w-4 h-4" />
                          Stop
                        </Button>
                      )}
                    </div>
                </div>
              ))}

              <div className="pt-4 border-t border-cream-300 flex gap-2">
                <Button
                  variant="primary"
                  onClick={() => controlAll('start')}
                  loading={controlLoading.all}
                  disabled={controlLoading.all}
                  className="flex-1"
                >
                  <Play className="w-4 h-4" />
                  Start ALL
                </Button>
                <Button
                  variant="danger"
                  onClick={() => controlAll('stop')}
                  loading={controlLoading.all}
                  disabled={controlLoading.all}
                  className="flex-1"
                >
                  <Square className="w-4 h-4" />
                  Stop ALL
                </Button>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader title="Pipeline Execution" subtitle="Run the full NLP pipeline with progress tracking" />
            
            <div className="space-y-4">
              <div className="space-y-3">
                <label className="flex items-center gap-3 p-3 rounded-lg border border-cream-300 bg-white cursor-pointer hover:bg-cream-50">
                  <input
                    type="checkbox"
                    checked={pipelineOptions.force_refresh}
                    onChange={(e) => setPipelineOptions(prev => ({ ...prev, force_refresh: e.target.checked }))}
                    className="w-4 h-4 text-brown-700 border-cream-300 rounded focus:ring-brown-500"
                  />
                  <div>
                    <p className="font-medium text-brown-800">Force Refresh</p>
                    <p className="text-sm text-brown-500">Re-download data even if cached CSV exists</p>
                  </div>
                </label>
                
                <label className="flex items-center gap-3 p-3 rounded-lg border border-cream-300 bg-white cursor-pointer hover:bg-cream-50">
                  <input
                    type="checkbox"
                    checked={pipelineOptions.no_fetch}
                    onChange={(e) => setPipelineOptions(prev => ({ ...prev, no_fetch: e.target.checked }))}
                    className="w-4 h-4 text-brown-700 border-cream-300 rounded focus:ring-brown-500"
                  />
                  <div>
                    <p className="font-medium text-brown-800">Skip Fetch</p>
                    <p className="text-sm text-brown-500">Skip fetching; requires cached CSV</p>
                  </div>
                </label>
                
                <label className="flex items-center gap-3 p-3 rounded-lg border border-cream-300 bg-white cursor-pointer hover:bg-cream-50">
                  <input
                    type="checkbox"
                    checked={pipelineOptions.no_rag}
                    onChange={(e) => setPipelineOptions(prev => ({ ...prev, no_rag: e.target.checked }))}
                    className="w-4 h-4 text-brown-700 border-cream-300 rounded focus:ring-brown-500"
                  />
                  <div>
                    <p className="font-medium text-brown-800">Skip RAG</p>
                    <p className="text-sm text-brown-500">Skip batch RAG explainability step</p>
                  </div>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-brown-700 mb-1">RAG Samples</label>
                <input
                  type="number"
                  value={pipelineOptions.samples}
                  onChange={(e) => setPipelineOptions(prev => ({ ...prev, samples: Math.max(10, Math.min(1000, Number(e.target.value))) }))}
                  min={10}
                  max={1000}
                  className="w-full px-3 py-2 border-cream-300 rounded-lg focus:ring-2 focus:ring-brown-500 focus:border-transparent"
                />
              </div>

              <Button 
                onClick={handleStartPipeline} 
                loading={pipelineLoading || pollProgress}
                className="w-full"
                size="lg"
                disabled={pipelineLoading || pollProgress}
              >
                <Zap className="w-5 h-5" />
                {pollProgress ? 'Running Pipeline...' : 'Run Pipeline'}
              </Button>

              {pollProgress && (
                <Card className="bg-blue-50 border-blue-200">
                  <CardHeader title="Pipeline Progress" subtitle="Real-time stage tracking" />
                  <div className="space-y-3">
                    {pipelineProgress.map((stage) => (
                      <div key={stage.stage} className="flex items-center gap-3">
                        <div className="w-24 text-sm font-medium text-brown-700 capitalize">{stage.stage}</div>
                        <div className="flex-1">
                          <ProgressBar 
                            value={stage.progress} 
                            color={getStatusColor(stage.status)} 
                            height={8} 
                            showLabel 
                          />
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(stage.status)}
                          <span className="text-sm text-brown-600">{stage.message}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {pipelineResult && (
                <Card className="animate-slide-up">
                  <div className="flex items-start gap-3">
                    {pipelineResult.success ? <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" /> : <XCircle className="w-5 h-5 text-red-600 mt-0.5" />}
                    <div className="flex-1">
                      <p className="font-medium text-brown-800">{pipelineResult.message}</p>
                      {pipelineResult.duration_seconds && (
                        <p className="text-sm text-brown-500 mt-1">Duration: {pipelineResult.duration_seconds.toFixed(1)}s</p>
                      )}
                      {pipelineResult.artifacts && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {Object.entries(pipelineResult.artifacts).map(([key, path]) => (
                            <span key={key} className="text-xs bg-cream-100 text-brown-600 px-2 py-1 rounded font-mono">
                              {key}: {path.split('/').pop()}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              )}
            </div>
          </Card>
        </div>

        <Card>
          <CardHeader title="Process Logs" subtitle="Real-time output from running services" />
          
          <div className="border-b border-cream-300">
            <nav className="flex gap-1 px-4" aria-label="Log tabs">
              {Object.keys(logs).map((service) => (
                <button
                  key={service}
                  onClick={() => setActiveLogTab(service)}
                  className={cn(
                    'py-3 px-4 text-sm font-medium rounded-t-lg transition-colors border-b-2 -mb-px',
                    activeLogTab === service
                      ? 'border-brown-700 text-brown-800 bg-cream-50'
                      : 'border-transparent text-brown-500 hover:text-brown-700 hover:bg-cream-50'
                  )}
                >
                  {service.charAt(0).toUpperCase() + service.slice(1)}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-brown-500">{logs[activeLogTab]?.length || 0} log entries</span>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => navigator.clipboard.writeText(logs[activeLogTab]?.join('\n') || '')}>
                  <Download className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <pre className="bg-brown-900 text-cream-100 p-4 rounded-lg overflow-x-auto text-sm font-mono max-h-96">
              <code>{logs[activeLogTab]?.slice(-200).join('\n') || 'No logs yet. Start the service to see output.'}</code>
            </pre>
          </div>
        </Card>
      </Section>
    </div>
  );
}