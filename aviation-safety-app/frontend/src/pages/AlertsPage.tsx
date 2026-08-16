import { useAlerts } from '@/hooks/useApi';
import { Card, CardHeader, Badge, MetricCard } from '@/components/ui';
import { Loader2, AlertTriangle, Shield, RefreshCw, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { formatNumber, formatDate, getRiskColor, getRiskBadgeColor } from '@/utils/helpers';
import { cn } from '@/utils/helpers';
import { useState } from 'react';

export function AlertsPage() {
  const { data, loading, error, refetch } = useAlerts(100);
  const [expandedAlerts, setExpandedAlerts] = useState<Set<string>>(new Set());

  const toggleExpand = (incidentId: string) => {
    setExpandedAlerts(prev => {
      const next = new Set(prev);
      if (next.has(incidentId)) {
        next.delete(incidentId);
      } else {
        next.add(incidentId);
      }
      return next;
    });
  };

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
        <h3 className="text-brown-800 text-lg font-medium mb-2">Unable to load alerts</h3>
        <p className="text-brown-500 mb-4">{error}</p>
        <button onClick={refetch} className="px-4 py-2 bg-brown-700 text-white rounded-lg hover:bg-brown-800">
          Try Again
        </button>
      </Card>
    );
  }

  const counts = data?.counts || {};
  const alerts = data?.alerts || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brown-800">Live Alerts</h1>
          <p className="text-brown-500 mt-1">Real-time incident monitoring and alerting</p>
        </div>
        <Button variant="outline" onClick={refetch} loading={loading}>
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Critical"
          value={counts.critical || 0}
          icon={<AlertTriangle className="w-6 h-6 text-risk-critical" />}
        />
        <MetricCard
          label="High"
          value={counts.high || 0}
          icon={<Shield className="w-6 h-6 text-risk-high" />}
        />
        <MetricCard
          label="Medium"
          value={counts.medium || 0}
          icon={<FileText className="w-6 h-6 text-risk-medium" />}
        />
        <MetricCard
          label="Total Alerts"
          value={data?.total || 0}
          icon={<AlertTriangle className="w-6 h-6" />}
        />
      </div>

      <Card>
        <CardHeader title="Recent Alerts" subtitle={data ? `Showing ${alerts.length} of ${data.total} total` : 'No alerts'} />
        
        {alerts.length === 0 ? (
          <div className="text-center py-12 text-brown-500">
            <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No alerts found. Start the monitor to begin receiving alerts.</p>
          </div>
        ) : (
          <div className="space-y-0">
            {alerts.map((alert) => {
              const isExpanded = expandedAlerts.has(alert.incident_id);
              return (
                <div key={alert.incident_id} className="border-b border-cream-200 last:border-0">
                  <div 
                    className={cn(
                      'p-4 hover:bg-cream-50 transition-colors cursor-pointer',
                      'flex items-start gap-4'
                    )}
                    onClick={() => toggleExpand(alert.incident_id)}
                  >
                    <div className={cn(
                      'w-3 h-3 rounded-full mt-1.5 flex-shrink-0',
                      getRiskBadgeColor(alert.risk_level)
                    )} />
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <Badge variant={alert.risk_level === 'critical' ? 'error' : alert.risk_level === 'high' ? 'warning' : 'success'} size="sm">
                          {alert.risk_level.toUpperCase()}
                        </Badge>
                        <span className="font-medium text-brown-800">{alert.predicted_label}</span>
                        <span className="text-sm text-brown-500">{alert.source}</span>
                        <span className="text-sm text-brown-400">{alert.incident_id}</span>
                      </div>
                      <p className="mt-1 text-sm text-brown-600 truncate">{alert.narrative}</p>
                      <p className="mt-1 text-xs text-brown-400">{formatDate(alert.timestamp)}</p>
                    </div>

                    <div className="flex items-center gap-2 text-brown-400">
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="bg-cream-50 border-t border-cream-200 p-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-sm font-medium text-brown-700">Full Narrative</p>
                          <p className="mt-1 text-sm text-brown-800 bg-white p-3 rounded border border-cream-300">
                            {alert.narrative}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-brown-700">Risk Assessment</p>
                          <div className="mt-1 space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-brown-600">Risk Level:</span>
                              <Badge variant={alert.risk_level === 'critical' ? 'error' : alert.risk_level === 'high' ? 'warning' : 'success'}>
                                {alert.risk_level.toUpperCase()}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-brown-600">Predicted:</span>
                              <Badge variant="info" size="sm">{alert.predicted_label}</Badge>
                            </div>
                          </div>
                        </div>
                      </div>

                      {alert.evidence.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-brown-700 mb-3">RAG Evidence (Similar Historical Reports)</p>
                          <div className="space-y-3">
                            {alert.evidence.map((ev) => (
                              <div 
                                key={ev.rank}
                                className={cn('p-3 rounded-lg border', 'bg-white border-cream-300')}
                              >
                                <div className="flex items-center gap-2 mb-1">
                                  <Badge variant="info" size="sm">#{ev.rank}</Badge>
                                  <Badge variant="default" size="sm">
                                    {(ev.similarity * 100).toFixed(1)}% similar
                                  </Badge>
                                  <Badge variant="default" size="sm">{ev.domain}</Badge>
                                </div>
                                <p className="font-medium text-brown-800 text-sm">{ev.label}</p>
                                <p className="mt-1 text-sm text-brown-600 italic">"{ev.snippet}"</p>
                                <div className="mt-2 h-1.5 bg-cream-200 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-brown-700 rounded-full"
                                    style={{ width: `${ev.similarity * 100}%` }}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}