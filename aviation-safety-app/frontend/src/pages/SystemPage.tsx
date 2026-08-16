import { useSystemStatus, useServiceControl, usePipeline } from '@/hooks/useApi';
import { Card, CardHeader, Button, Badge } from '@/components/ui';
import { Loader2, Play, Stop, Terminal, Database, Zap, AlertTriangle, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/utils/helpers';
import { useState } from 'react';

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
  const [pipelineResult, setPipelineResult] = useState<{ success: boolean; message: string } | null>(null);
  const [activeLogTab, setActiveLogTab] = useState<string>('pipeline');

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
        <AlertTriangle className="w-12 h-12 mx-auto text-risk-critical mb-4" />
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
    try {
      const result = await runPipeline(pipelineOptions);
      setPipelineResult({ success: result.success, message: result.message });
    } catch (err) {
      // Handled by hook
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brown-800">System Control</h1>
          <p className="text-brown-500 mt-1">Manage pipeline and monitor processes</p>
        </div>
        <Button variant="outline" onClick={refetch} loading={loading}>
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Service Controls" subtitle="Start/stop pipeline and monitor services" />
          
          <div className="space-y-4">
            {services.map((service) => (
              <div key={service.name} className="p-4 rounded-lg border border-cream-300 bg-cream-50">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-brown-800">{service.label}</h4>
                      <Badge 
                        variant={service.running ? 'success' : 'default'} 
                        size="sm"
                        className={service.running ? 'bg-risk-medium/10 text-risk-medium' : 'bg-cream-200 text-brown-600'}
                      >
                        {service.running ? 'RUNNING' : 'STOPPED'}
                      </Badge>
                      {service.pid && (
                        <span className="text-xs text-brown-400 font-mono">PID: {service.pid}</span>
                      )}
                    </div>
                    <p className="text-sm text-brown-600">{service.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {!service.running ? (
                      <Button
                        size="sm"
                        onClick={() => controlService(service.name, 'start')}
                        loading={controlLoading[service.name]}
                        disabled={controlLoading[service.name]}
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
                      >
                        <Stop className="w-4 h-4" />
                        Stop
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}

            <div className="pt-4 border-t border-cream-300 flex gap-2">
              <Button
                variant="primary"
                onClick={() => controlAll('start')}
                loading={controlLoading.all}
                disabled={controlLoading.all}
              >
                <Play className="w-4 h-4" />
                Start ALL
              </Button>
              <Button
                variant="danger"
                onClick={() => controlAll('stop')}
                loading={controlLoading.all}
                disabled={controlLoading.all}
              >
                <Stop className="w-4 h-4" />
                Stop ALL
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="Run Pipeline" subtitle="Execute the full NLP pipeline end-to-end" />
          
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
              loading={pipelineLoading}
              className="w-full"
              size="lg"
            >
              <Zap className="w-5 h-5" />
              Run Pipeline
            </Button>

            {pipelineResult && (
              <div className={cn(
                'p-4 rounded-lg',
                pipelineResult.success 
                  ? 'bg-risk-medium/10 border-risk-medium/20 text-risk-medium' 
                  : 'bg-risk-critical/10 border-risk-critical/20 text-risk-critical'
              )}>
                <div className="flex items-center gap-2">
                  {pipelineResult.success ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                  <span className="font-medium">{pipelineResult.message}</span>
                </div>
              </div>
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
                  'py-3 px-4 text-sm font-medium rounded-t-lg transition-colors',
                  'border-b-2 -mb-px',
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
          <pre className="bg-brown-900 text-cream-100 p-4 rounded-lg overflow-x-auto text-sm font-mono max-h-96">
            <code>{logs[activeLogTab]?.slice(-100).join('\n') || 'No logs yet. Start the service to see output.'}</code>
          </pre>
        </div>
      </Card>
    </div>
  );
}