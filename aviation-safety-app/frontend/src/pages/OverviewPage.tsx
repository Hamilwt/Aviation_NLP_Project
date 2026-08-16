import { useOverview } from '@/hooks/useApi';
import { MetricCard, Card, CardHeader, Badge } from '@/components/ui';
import { Users, Globe, Tag, TrendingUp, Loader2 } from 'lucide-react';
import { formatNumber, formatPercent } from '@/utils/helpers';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

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
        <div className="text-risk-critical mb-4">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-brown-800 text-lg font-medium mb-2">Unable to load overview</h3>
        <p className="text-brown-500 mb-4">{error || 'No data available'}</p>
        <button onClick={refetch} className="px-4 py-2 bg-brown-700 text-white rounded-lg hover:bg-brown-800">
          Try Again
        </button>
      </Card>
    );
  }

  const domainData = Object.entries(data.domains).map(([name, value]) => ({ name, value }));
  const classData = Object.entries(data.class_distribution)
    .slice(0, 10)
    .map(([name, value]) => ({ name: name.length > 20 ? name.slice(0, 20) + '...' : name, value }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brown-800">Overview</h1>
          <p className="text-brown-500 mt-1">Dataset snapshot and key metrics</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Reports"
          value={formatNumber(data.total_reports)}
          icon={<Users className="w-6 h-6" />}
        />
        <MetricCard
          label="Domains"
          value={Object.keys(data.domains).length}
          icon={<Globe className="w-6 h-6" />}
        />
        <MetricCard
          label="Anomaly Classes"
          value={data.anomaly_classes}
          icon={<Tag className="w-6 h-6" />}
        />
        <MetricCard
          label="Imbalance Ratio"
          value={
            (() => {
              const vals = Object.values(data.class_distribution);
              return vals.length > 1 ? (Math.max(...vals) / Math.min(...vals)).toFixed(0) + 'x' : '1x';
            })()
          }
          icon={<TrendingUp className="w-6 h-6" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Domain Distribution" subtitle="Reports by domain" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={domainData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#D9C5B2" />
                <XAxis dataKey="name" stroke="#8B7355" fontSize={12} tickMargin={8} />
                <YAxis stroke="#8B7355" fontSize={12} tickMargin={8} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFDF9',
                    border: '1px solid #D9C5B2',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  <Cell fill="#5C4033" />
                  <Cell fill="#8B6B4D" />
                  <Cell fill="#A98467" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 mt-4">
            {Object.entries(data.domains).map(([domain, count]) => (
              <Badge key={domain} variant="info">
                {domain}: {formatNumber(count)}
              </Badge>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Top Anomaly Classes" subtitle="Top 10 most frequent categories" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={classData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#D9C5B2" />
                <XAxis type="number" stroke="#8B7355" fontSize={12} />
                <YAxis type="category" dataKey="name" stroke="#8B7355" fontSize={11} width={140} tickMargin={8} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFDF9',
                    border: '1px solid #D9C5B2',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {classData.map((_, i) => (
                    <Cell key={`cell-${i}`} fill={i % 3 === 0 ? '#5C4033' : i % 3 === 1 ? '#8B6B4D' : '#A98467'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Sample Reports" subtitle="First 10 reports from the dataset" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-cream-300">
                <th className="text-left py-3 px-4 font-medium text-brown-600">Narrative</th>
                <th className="text-left py-3 px-4 font-medium text-brown-600">Label</th>
                <th className="text-left py-3 px-4 font-medium text-brown-600">Domain</th>
              </tr>
            </thead>
            <tbody>
              {/* This would need actual sample data from the API */}
              <tr>
                <td colSpan={3} className="py-8 text-center text-brown-500">
                  Sample data not available in overview endpoint. Use Data Assistant for detailed inspection.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}