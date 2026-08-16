import { useState } from 'react';
import { useAlerts } from '@/hooks/useApi';
import { Section, Card, CardHeader, Badge, MetricCard, ProgressBar, Table } from '@/components/ui/DataDisplay';
import { PieChartComponent, BarChartComponent } from '@/components/charts/ChartComponents';
import { Loader2, AlertTriangle, Shield, RefreshCw, ChevronDown, ChevronUp, FileText, Bell, Eye, Filter } from 'lucide-react';
import { formatNumber, formatDate, cn } from '@/utils/helpers';

export function AlertsPage() {
  const { data, loading, error, refetch } = useAlerts(200);
  const [expandedAlerts, setExpandedAlerts] = useState<Set<string>>(new Set());
  const [riskFilter, setRiskFilter] = useState<'all' | 'critical' | 'high' | 'medium'>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');

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

  const filteredAlerts = data?.alerts.filter(alert => {
    if (riskFilter !== 'all' && alert.risk_level !== riskFilter) return false;
    if (sourceFilter !== 'all' && alert.source !== sourceFilter) return false;
    return true;
  }) || [];

  const sources = [...new Set(data?.alerts.map(a => a.source) || [])];

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
        <h3 className="text-brown-800 text-lg font-medium mb-2">Unable to load alerts</h3>
        <p className="text-brown-500 mb-4">{error}</p>
        <button onClick={refetch} className="px-4 py-2 bg-brown-700 text-white rounded-lg hover:bg-brown-800">
          Try Again
        </button>
      </Card>
    );
  }

  const counts = data?.counts || {};
  const alerts = filteredAlerts;
  const total = data?.total || 0;

  const riskColors = { critical: '#EF4444', high: '#F97316', medium: '#22C55E' };
  const riskLabels = { critical: 'Critical', high: 'High', medium: 'Medium' };

  const riskDistData = Object.entries(counts).map(([risk, count]) => ({
    name: riskLabels[risk as keyof typeof riskLabels] || risk,
    value: count,
    color: riskColors[risk as keyof typeof riskColors] || '#888',
  })).filter(d => d.value > 0);

  const sourceDistData = alerts.reduce((acc, alert) => {
    acc[alert.source] = (acc[alert.source] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sourceData = Object.entries(sourceDistData).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <Section
        title="Live Alerts"
        subtitle="Real-time incident monitoring and alerting"
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={refetch} loading={loading}>
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
        }
      />

      <StatGrid columns={4}>
        <MetricCard
          label="Critical"
          value={counts.critical || 0}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="#EF4444"
        />
        <MetricCard
          label="High"
          value={counts.high || 0}
          icon={<Shield className="w-6 h-6" />}
          color="#F97316"
        />
        <MetricCard
          label="Medium"
          value={counts.medium || 0}
          icon={<FileText className="w-6 h-6" />}
          color="#22C55E"
        />
        <MetricCard
          label="Total Alerts"
          value={total}
          icon={<Bell className="w-6 h-6" />}
          color="#5C4033"
        />
      </StatGrid>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader title="Alert Timeline" subtitle="Recent alerts by risk level" />
          <div className="h-64">
            {riskDistData.length > 0 ? (
              <PieChartComponent
                data={riskDistData}
                dataKey="value"
                nameKey="name"
                height={250}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-brown-500">No alert data</div>
            )}
          </div>
        </Card>

        <Card>
          <CardHeader title="Alerts by Source" subtitle="Source distribution" />
          <div className="h-64">
            {sourceData.length > 0 ? (
              <BarChartComponent
                data={sourceData}
                xKey="name"
                yKeys="value"
                horizontal={true}
                colors={['#5C4033']}
                height={250}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-brown-500">No source data</div>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader 
          title="Recent Alerts" 
          subtitle={data ? `Showing ${alerts.length} of ${total} total` : 'No alerts'}
          action={
            <div className="flex items-center gap-2">
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value as any)}
                className="px-3 py-1.5 border-cream-300 rounded-lg text-sm focus:ring-2 focus:ring-brown-500 focus:border-transparent"
              >
                <option value="all">All Risk Levels</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
              </select>
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="px-3 py-1.5 border-cream-300 rounded-lg text-sm focus:ring-2 focus:ring-brown-500 focus:border-transparent"
              >
                <option value="all">All Sources</option>
                {sources.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          }
        />
        
        {alerts.length === 0 ? (
          <div className="text-center py-16 text-brown-500">
            <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg">No alerts found</p>
            <p className="text-sm mt-1">Start the monitor to begin receiving alerts</p>
          </div>
        ) : (
          <div className="space-y-0">
            {alerts.map((alert) => {
              const isExpanded = expandedAlerts.has(alert.incident_id);
              const riskColor = riskColors[alert.risk_level as keyof typeof riskColors] || '#888';
              
              return (
                <div key={alert.incident_id} className="border-b border-cream-200 last:border-0">
                  <div 
                    className={cn(
                      'p-4 hover:bg-cream-50 transition-colors cursor-pointer',
                      'flex items-start gap-4'
                    )}
                    onClick={() => toggleExpand(alert.incident_id)}
                  >
                    <div className="w-3 h-3 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: riskColor }} />
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <Badge variant={alert.risk_level as any} size="sm">
                          {riskLabels[alert.risk_level as keyof typeof riskLabels]}
                        </Badge>
                        <span className="font-medium text-brown-800">{alert.predicted_label}</span>
                        <Badge variant="info" size="sm">{alert.source}</Badge>
                        <span className="text-sm text-brown-400 font-mono">{alert.incident_id}</span>
                      </div>
                      <p className="mt-1 text-sm text-brown-600 truncate">{alert.narrative}</p>
                      <p className="mt-1 text-xs text-brown-400">{formatDate(alert.timestamp)}</p>
                    </div>

                    <div className="flex items-center gap-2 text-brown-400">
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="bg-cream-50 border-t border-cream-200 p-4 animate-slide-up">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-sm font-medium text-brown-700">Full Narrative</p>
                          <p className="mt-1 text-sm text-brown-800 bg-white p-3 rounded border border-cream-300">
                            {alert.narrative}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-brown-700">Risk Assessment</p>
                          <div className="mt-1 space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-brown-600">Risk Level:</span>
                              <Badge variant={alert.risk_level as any}>
                                {riskLabels[alert.risk_level as keyof typeof riskLabels]}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-brown-600">Predicted:</span>
                              <Badge variant="info" size="sm">{alert.predicted_label}</Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-brown-600">Source:</span>
                              <Badge variant="default" size="sm">{alert.source}</Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-brown-600">Time:</span>
                              <Badge variant="default" size="sm">{formatDate(alert.timestamp)}</Badge>
                            </div>
                          </div>
                        </div>
                      </div>

                      {alert.evidence.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-brown-700 mb-3">RAG Evidence (Similar Historical Reports)</p>
                          <div className="space-y-3">
                            {alert.evidence.map((ev) => (
                              <Card key={ev.rank} className="p-3">
                                <div className="flex items-center gap-2 mb-1">
                                  <Badge variant="info" size="sm">#{ev.rank}</Badge>
                                  <Badge variant={ev.similarity > 0.7 ? 'success' : ev.similarity > 0.4 ? 'warning' : 'default'} size="sm">
                                    {(ev.similarity * 100).toFixed(1)}% similar
                                  </Badge>
                                  <Badge variant="default" size="sm">{ev.domain}</Badge>
                                </div>
                                <p className="font-medium text-brown-800 text-sm">{ev.label}</p>
                                <p className="mt-1 text-sm text-brown-600 italic">"{ev.snippet}"</p>
                                <ProgressBar value={ev.similarity * 100} color={ev.similarity > 0.7 ? '#22C55E' : ev.similarity > 0.4 ? '#F59E0B' : '#EF4444'} height={4} className="mt-2" />
                              </Card>
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