import { useState, useMemo } from 'react';
import { useAlerts } from '@/hooks/useApi';
import { Section, Card, CardHeader, Badge, MetricCard, ProgressBar, StatGrid, Button } from '@/components/ui';
import { PieChartComponent, BarChartComponent } from '@/components/charts/ChartComponents';
import { Loader2, AlertTriangle, Shield, RefreshCw, ChevronDown, ChevronUp, FileText, Bell, Lightbulb, Filter } from 'lucide-react';
import { formatDate, cn } from '@/utils/helpers';

type RiskLevel = 'critical' | 'high' | 'medium' | 'low';
type CategoryFilter = 'all' | RiskLevel;

const RISK_ORDER: RiskLevel[] = ['critical', 'high', 'medium', 'low'];

const RISK_COLORS: Record<RiskLevel, string> = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#22C55E',
};

const RISK_LABELS: Record<RiskLevel, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

const CATEGORY_META: Record<CategoryFilter, { label: string; color: string; ring: string }> = {
  all: { label: 'All', color: '#5C4033', ring: 'ring-brown-700 text-brown-800 bg-brown-50' },
  critical: { label: 'Critical', color: RISK_COLORS.critical, ring: 'ring-red-600 text-red-700 bg-red-50' },
  high: { label: 'High', color: RISK_COLORS.high, ring: 'ring-orange-500 text-orange-700 bg-orange-50' },
  medium: { label: 'Medium', color: RISK_COLORS.medium, ring: 'ring-yellow-500 text-yellow-700 bg-yellow-50' },
  low: { label: 'Low', color: RISK_COLORS.low, ring: 'ring-green-600 text-green-700 bg-green-50' },
};

interface Alert {
  incident_id: string;
  risk_level: string;
  predicted_label: string;
  source: string;
  narrative: string;
  timestamp: string;
  suggestion?: string;
  evidence: Array<{ rank: number; similarity: number; label: string; domain: string; snippet: string }>;
}

export function AlertsPage() {
  const { data, loading, error, refetch } = useAlerts(200);
  const [expandedAlerts, setExpandedAlerts] = useState<Set<string>>(new Set());
  const [category, setCategory] = useState<CategoryFilter>('all');
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

  const filteredAlerts = useMemo(() => {
    return data?.alerts.filter((alert: Alert) => {
      if (category !== 'all' && alert.risk_level !== category) return false;
      if (sourceFilter !== 'all' && alert.source !== sourceFilter) return false;
      return true;
    }) || [];
  }, [data?.alerts, category, sourceFilter]);

  const sources = useMemo((): string[] => [...new Set((data?.alerts as Alert[] | undefined)?.map(a => a.source) || [])], [data?.alerts]);

  const categoryCounts = useMemo(() => {
    const counts: Record<CategoryFilter, number> = { all: data?.alerts?.length || 0, critical: 0, high: 0, medium: 0, low: 0 };
    (data?.alerts || []).forEach((a: Alert) => {
      const key = a.risk_level as RiskLevel;
      if (key in counts) counts[key] += 1;
      else counts.all += 1;
    });
    return counts;
  }, [data?.alerts]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <Loader2 className="w-8 h-8 text-brown-500 animate-spin" />
        <p className="text-brown-800 font-medium">Loading live alerts...</p>
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

  const riskDistData = RISK_ORDER
    .map(risk => ({ name: RISK_LABELS[risk], value: counts[risk] || 0, color: RISK_COLORS[risk] }))
    .filter(d => d.value > 0);

  const sourceDistData = alerts.reduce((acc: Record<string, number>, alert: Alert) => {
    const source = alert.source || 'unknown';
    acc[source] = (acc[source] || 0) + 1;
    return acc;
  }, {});

  const sourceData = Object.entries(sourceDistData).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <Section
        title="Live Alerts"
        subtitle="Real-time incident monitoring with auto-generated safety suggestions"
        action={
          <Button variant="outline" onClick={refetch} loading={loading}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        }
      >
        <StatGrid columns={5}>
          {RISK_ORDER.map(risk => (
            <MetricCard
              key={risk}
              label={RISK_LABELS[risk]}
              value={counts[risk] || 0}
              icon={risk === 'critical' ? <AlertTriangle className="w-6 h-6" /> : risk === 'high' ? <Shield className="w-6 h-6" /> : risk === 'medium' ? <FileText className="w-6 h-6" /> : <Bell className="w-6 h-6" />}
              color={RISK_COLORS[risk]}
            />
          ))}
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
                  barColors={['#5C4033']}
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
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="px-3 py-1.5 border border-cream-300 rounded-lg text-sm focus:ring-2 focus:ring-brown-500 focus:border-transparent bg-white"
              >
                <option value="all">All Sources</option>
                {sources.map((s: string) => <option key={s} value={s}>{s}</option>)}
              </select>
            }
          />

          <div className="flex flex-wrap items-center gap-2 px-4 pb-4 border-b border-cream-300">
            <Filter className="w-4 h-4 text-brown-400" />
            {(Object.keys(CATEGORY_META) as CategoryFilter[]).map(cat => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={cn(
                  'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                  'ring-1 ring-inset focus:outline-none focus:ring-2',
                  category === cat
                    ? CATEGORY_META[cat].ring
                    : 'text-brown-500 hover:bg-cream-100 ring-transparent'
                )}
              >
                {CATEGORY_META[cat].label}
                <span className="ml-1.5 opacity-70">({categoryCounts[cat]})</span>
              </button>
            ))}
          </div>
          
          {alerts.length === 0 ? (
            <div className="text-center py-16 text-brown-500">
              <Shield className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No {category === 'all' ? '' : `${RISK_LABELS[category as RiskLevel]} `}alerts found</p>
              <p className="text-sm mt-1">Start the monitor to begin receiving alerts</p>
            </div>
          ) : (
            <div className="space-y-0">
              {alerts.map((alert: Alert) => {
                const isExpanded = expandedAlerts.has(alert.incident_id);
                const risk = (alert.risk_level as RiskLevel) in RISK_COLORS ? alert.risk_level as RiskLevel : 'medium';
                const riskColor = RISK_COLORS[risk];
                
                return (
                  <div key={alert.incident_id} className="border-b border-cream-200 last:border-0">
                    <div 
                      className="p-4 hover:bg-cream-50 transition-colors cursor-pointer flex items-start gap-4"
                      onClick={() => toggleExpand(alert.incident_id)}
                    >
                      <div className="w-3 h-3 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: riskColor }} />
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 flex-wrap">
                          <Badge variant={risk === 'critical' ? 'error' : risk === 'high' ? 'warning' : risk === 'medium' ? 'default' : 'success'} size="sm">
                            {RISK_LABELS[risk]}
                          </Badge>
                          <span className="font-medium text-brown-800">{alert.predicted_label}</span>
                          <Badge variant="info" size="sm">{alert.source}</Badge>
                          <span className="text-sm text-brown-400 font-mono">{alert.incident_id}</span>
                        </div>
                        <p className="mt-1 text-sm text-brown-600 truncate">{alert.narrative}</p>
                        <p className="mt-1 text-xs text-brown-400">{formatDate(alert.timestamp)}</p>
                        {(alert.suggestion || `Priority ${RISK_LABELS[risk as RiskLevel]} response: review the incident evidence, confirm the safety controls that failed, and document the corrective action plan before normal operations continue.`) && (
                          <div className="mt-2 flex items-start gap-2 p-2.5 bg-teal-50 border border-teal-200 rounded-lg">
                            <Lightbulb className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
                            <p className="text-xs text-teal-800 leading-relaxed">{alert.suggestion || `Priority ${RISK_LABELS[risk as RiskLevel]} response: review the incident evidence, confirm the safety controls that failed, and document the corrective action plan before normal operations continue.`}</p>
                          </div>
                        )}
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
                                <Badge variant={risk === 'critical' ? 'error' : risk === 'high' ? 'warning' : risk === 'medium' ? 'default' : 'success'}>
                                  {RISK_LABELS[risk]}
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

                        {alert.suggestion && (
                          <div className="mb-4">
                            <p className="text-sm font-medium text-teal-700 mb-2 flex items-center gap-1.5">
                              <Lightbulb className="w-4 h-4" />
                              Safety Suggestion (auto-generated)
                            </p>
                            <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg">
                              <p className="text-sm text-teal-900 leading-relaxed">{alert.suggestion}</p>
                            </div>
                          </div>
                        )}

                        {alert.evidence.length > 0 && (
                          <div>
                            <p className="text-sm font-medium text-brown-700 mb-3">RAG Evidence (Similar Historical Reports)</p>
                            <div className="space-y-3">
                              {alert.evidence.map((ev: { rank: number; similarity: number; label: string; domain: string; snippet: string }) => (
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
      </Section>
    </div>
  );
}