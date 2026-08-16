import { useModelPerformance } from '@/hooks/useApi';
import { Card, CardHeader, Badge, MetricCard } from '@/components/ui';
import { Loader2, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import { formatPercent } from '@/utils/helpers';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, AreaChart, Area
} from 'recharts';

export function PerformancePage() {
  const { data, loading, error, refetch } = useModelPerformance();

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
        <AlertCircle className="w-12 h-12 mx-auto text-risk-critical mb-4" />
        <h3 className="text-brown-800 text-lg font-medium mb-2">Unable to load model performance</h3>
        <p className="text-brown-500 mb-4">{error || 'No performance data available. Run the pipeline first.'}</p>
        <button onClick={refetch} className="px-4 py-2 bg-brown-700 text-white rounded-lg hover:bg-brown-800">
          Try Again
        </button>
      </Card>
    );
  }

  const { metrics, classification_report, confusion_matrix_url, class_distribution_url } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brown-800">Model Performance</h1>
          <p className="text-brown-500 mt-1">Classification metrics and evaluation results</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          label="Test Accuracy"
          value={formatPercent(metrics.accuracy)}
          icon={<CheckCircle className="w-6 h-6 text-risk-medium" />}
        />
        <MetricCard
          label="Classes"
          value={metrics.n_classes}
          icon={<FileText className="w-6 h-6" />}
        />
        <MetricCard
          label="Test Samples"
          value={metrics.test_size}
          icon={<AlertCircle className="w-6 h-6" />}
        />
      </div>

      {metrics.best_cv_f1 && (
        <Card className="bg-teal-50 border-teal-200">
          <CardHeader title="Cross-Validation Score" subtitle="Best weighted F1 from GridSearchCV" />
          <div className="text-3xl font-bold text-teal-700">{formatPercent(metrics.best_cv_f1)}</div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {confusion_matrix_url && (
          <Card>
            <CardHeader title="Confusion Matrix (Normalized)" />
            <div className="aspect-square flex items-center justify-center">
              <img 
                src={confusion_matrix_url} 
                alt="Confusion matrix" 
                className="max-w-full max-h-96 rounded-lg shadow-sm"
              />
            </div>
          </Card>
        )}

        {class_distribution_url && (
          <Card>
            <CardHeader title="Class Distribution" />
            <div className="aspect-square flex items-center justify-center">
              <img 
                src={class_distribution_url} 
                alt="Class distribution" 
                className="max-w-full max-h-96 rounded-lg shadow-sm"
              />
            </div>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader title="Classification Report (Per Class)" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-cream-300 bg-cream-50">
                <th className="text-left py-3 px-4 font-medium text-brown-600">Class</th>
                <th className="text-right py-3 px-4 font-medium text-brown-600">Precision</th>
                <th className="text-right py-3 px-4 font-medium text-brown-600">Recall</th>
                <th className="text-right py-3 px-4 font-medium text-brown-600">F1-Score</th>
                <th className="text-right py-3 px-4 font-medium text-brown-600">Support</th>
              </tr>
            </thead>
            <tbody>
              {classification_report.map((row, idx) => (
                <tr key={row.class_name} className={cn(idx % 2 === 0 ? 'bg-cream-50' : '', 'border-b border-cream-200')}>
                  <td className="py-3 px-4 font-medium text-brown-800">{row.class_name}</td>
                  <td className="py-3 px-4 text-right">{formatPercent(row.precision)}</td>
                  <td className="py-3 px-4 text-right">{formatPercent(row.recall)}</td>
                  <td className="py-3 px-4 text-right font-medium text-brown-700">{formatPercent(row.f1_score)}</td>
                  <td className="py-3 px-4 text-right text-brown-500">{row.support}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {metrics.training_config && (
        <Card>
          <CardHeader title="Training Configuration" />
          <pre className="bg-cream-100 p-4 rounded-lg text-sm overflow-x-auto text-brown-700">
            {JSON.stringify(metrics.training_config, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}

function cn(...classes: (string | boolean | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}