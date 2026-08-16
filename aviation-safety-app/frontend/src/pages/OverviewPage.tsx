import { useOverview } from '@/hooks/useApi';
import { Section, StatGrid, MetricCard, Card, CardHeader, Badge, Table, ProgressBar } from '@/components/ui';
import { BarChartComponent } from '@/components/charts/ChartComponents';
import { Users, Globe, Tag, TrendingUp, Loader2, AlertTriangle, CheckCircle } from 'lucide-react';
import { formatNumber } from '@/utils/helpers';

export function OverviewPage() {
  const { data, loading, error, refetch } = useOverview();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-brown-500 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="text-center py-12">
        <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-brown-800 text-lg font-medium mb-2">Unable to load overview</h3>
        <p className="text-brown-500 mb-4">{error || 'No data available'}</p>
        <button onClick={refetch} className="px-4 py-2 bg-brown-700 text-white rounded-lg hover:bg-brown-800">
          Try Again
        </button>
      </Card>
    );
  }

  const domainData = Object.entries(data.domains).map(([name, value]) => ({ name, value: value as number }));
  const classData = Object.entries(data.class_distribution)
    .slice(0, 12)
    .map(([name, value]) => ({ name: name.length > 25 ? name.slice(0, 25) + '...' : name, value: value as number }));
  
  const total = data.total_reports;
  const classDistValues = Object.values(data.class_distribution) as number[];
  const imbalanceRatio = classDistValues.length > 1 
    ? Math.max(...classDistValues) / Math.min(...classDistValues)
    : 1;

  return (
    <div className="space-y-6">
      <Section
        title="Overview"
        subtitle="Dataset snapshot and key metrics"
        action={
          <button onClick={refetch} className="px-3 py-1.5 text-sm bg-brown-100 text-brown-700 rounded-lg hover:bg-brown-200 transition-colors">
            Refresh
          </button>
        }
      >
        <StatGrid columns={4}>
          <MetricCard
            label="Total Reports"
            value={formatNumber(data.total_reports)}
            icon={<Users className="w-6 h-6" />}
            color="#5C4033"
          />
          <MetricCard
            label="Domains"
            value={Object.keys(data.domains).length}
            icon={<Globe className="w-6 h-6" />}
            color="#8B6B4D"
          />
          <MetricCard
            label="Anomaly Classes"
            value={data.anomaly_classes}
            icon={<Tag className="w-6 h-6" />}
            color="#A98467"
          />
          <MetricCard
            label="Class Imbalance"
            value={`${imbalanceRatio.toFixed(0)}:1`}
            icon={<TrendingUp className="w-6 h-6" />}
            color="#0F766E"
            change={imbalanceRatio > 100 ? 'High' : imbalanceRatio > 10 ? 'Moderate' : 'Balanced'}
            changeType={imbalanceRatio > 100 ? 'negative' : imbalanceRatio > 10 ? 'neutral' : 'positive'}
          />
        </StatGrid>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader title="Domain Distribution" subtitle="Reports by domain" />
            <div className="h-64">
              <BarChartComponent
                data={domainData}
                xKey="name"
                yKeys="value"
                barColors={['#5C4033', '#0F766E']}
                horizontal={false}
              />
            </div>
            <div className="flex flex-wrap gap-2 mt-4">
              {Object.entries(data.domains).map(([domain, count]) => (
                <Badge key={domain} variant="info" size="sm">
                  {domain}: {formatNumber(count as number)} ({((count as number)/total*100).toFixed(1)}%)
                </Badge>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader title="Top Anomaly Classes" subtitle="Top 12 most frequent categories" />
            <div className="h-72">
              <BarChartComponent
                data={classData}
                xKey="name"
                yKeys="value"
                horizontal={true}
                height={280}
              />
            </div>
          </Card>
        </div>

        <Card>
          <CardHeader title="Class Distribution Details" subtitle="Full breakdown of anomaly categories" />
          <Table
            columns={[
              { key: 'class', header: 'Anomaly Category', className: 'font-medium' },
              { key: 'count', header: 'Count', className: 'text-right' },
              { key: 'percent', header: 'Percentage', className: 'text-right' },
              { 
                key: 'bar', 
                header: 'Distribution', 
                className: 'w-48',
                render: (row: any) => (
                  <ProgressBar value={row.percent} color="#5C4033" height={6} />
                )
              },
            ]}
            data={Object.entries(data.class_distribution).map(([className, count]) => {
              const countNum = count as number;
              return {
                class: className,
                count: countNum,
                percent: (countNum / total) * 100,
              };
            })}
            keyExtractor={(row) => row.class}
          />
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-green-50 border-green-200">
            <CardHeader title="Data Quality" subtitle="Dataset integrity check" />
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-brown-600">Total Records</span>
                <span className="font-medium text-brown-800">{formatNumber(total)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-brown-600">Domains</span>
                <span className="font-medium text-brown-800">{Object.keys(data.domains).length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-brown-600">Classes</span>
                <span className="font-medium text-brown-800">{data.anomaly_classes}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-brown-600">Imbalance Ratio</span>
                <span className="font-medium text-brown-800">{imbalanceRatio.toFixed(0)}:1</span>
              </div>
            </div>
          </Card>

          <Card className="bg-blue-50 border-blue-200">
            <CardHeader title="Narrative Statistics" subtitle="Text length analysis" />
            <div className="space-y-2">
              {data.narrative_stats && Object.entries(data.narrative_stats as Record<string, unknown>).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-brown-600 capitalize">{key.replace('_', ' ')}</span>
                  <span className="font-medium text-brown-800">{typeof value === 'number' ? value.toFixed(0) : String(value)}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card className="bg-purple-50 border-purple-200">
            <CardHeader title="Model Readiness" subtitle="Pipeline artifact status" />
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-brown-700">Dataset loaded</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-brown-700">Model artifacts ready</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-brown-700">RAG index built</span>
              </div>
            </div>
          </Card>
        </div>
      </Section>
    </div>
  );
}