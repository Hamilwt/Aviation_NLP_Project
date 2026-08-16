import { useModelPerformance } from '@/hooks/useApi';
import { Section, Card, CardHeader, Badge, MetricCard, Table, ProgressBar } from '@/components/ui/DataDisplay';
import { BarChartComponent, PieChartComponent, LineChartComponent } from '@/components/charts/ChartComponents';
import { Loader2, CheckCircle, AlertCircle, FileText, TrendingUp, Target, Award } from 'lucide-react';
import { formatPercent, cn } from '@/utils/helpers';

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
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-brown-800 text-lg font-medium mb-2">Unable to load model performance</h3>
        <p className="text-brown-500 mb-4">{error || 'No performance data available. Run the pipeline first.'}</p>
        <button onClick={refetch} className="px-4 py-2 bg-brown-700 text-white rounded-lg hover:bg-brown-800">
          Try Again
        </button>
      </Card>
    );
  }

  const { metrics, classification_report, confusion_matrix_url, class_distribution_url } = data;

  // Prepare class distribution data for charts
  const classDistData = classification_report.map(row => ({
    name: row.class_name.length > 20 ? row.class_name.slice(0, 20) + '...' : row.class_name,
    precision: row.precision,
    recall: row.recall,
    f1: row.f1_score,
    support: row.support,
    fullName: row.class_name,
  }));

  const topClasses = classDistData.slice(0, 10);
  const supportData = classification_report
    .sort((a, b) => b.support - a.support)
    .slice(0, 10)
    .map(row => ({
      name: row.class_name.length > 20 ? row.class_name.slice(0, 20) + '...' : row.class_name,
      support: row.support,
    }));

  return (
    <div className="space-y-6">
      <Section
        title="Model Performance"
        subtitle="Classification metrics and evaluation results"
        action={
          <button onClick={refetch} className="px-3 py-1.5 text-sm bg-brown-100 text-brown-700 rounded-lg hover:bg-brown-200 transition-colors">
            Refresh
          </button>
        }
      />

      <StatGrid columns={4}>
        <MetricCard
          label="Test Accuracy"
          value={formatPercent(metrics.accuracy)}
          icon={<CheckCircle className="w-6 h-6 text-green-600" />}
          color="#22C55E"
        />
        <MetricCard
          label="Classes"
          value={metrics.n_classes}
          icon={<Target className="w-6 h-6" />}
          color="#3B82F6"
        />
        <MetricCard
          label="Test Samples"
          value={metrics.test_size}
          icon={<FileText className="w-6 h-6" />}
          color="#F59E0B"
        />
        <MetricCard
          label="CV F1 (Weighted)"
          value={metrics.best_cv_f1 ? formatPercent(metrics.best_cv_f1) : 'N/A'}
          icon={<Award className="w-6 h-6" />}
          color="#8B5CF6"
        />
      </StatGrid>

      {metrics.best_cv_f1 && (
        <Card className="bg-purple-50 border-purple-200 mb-6">
          <CardHeader title="Cross-Validation Score" subtitle="Best weighted F1 from GridSearchCV" />
          <div className="flex items-center justify-between">
            <div className="text-4xl font-bold text-purple-700">{formatPercent(metrics.best_cv_f1)}</div>
            <div className="text-sm text-purple-600">
              {metrics.training_config && (
                <>
                  <div>Alpha: {metrics.training_config.best_params?.sgd__alpha || 'N/A'}</div>
                  <div>Class Weight: {metrics.training_config.best_params?.sgd__class_weight || 'N/A'}</div>
                </>
              )}
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Per-Class Metrics" subtitle="Precision, Recall, F1-Score by class" />
          <div className="h-80">
            <BarChartComponent
              data={topClasses}
              xKey="name"
              yKeys={['precision', 'recall', 'f1']}
              labels={{ precision: 'Precision', recall: 'Recall', f1: 'F1-Score' }}
              colors={['#5C4033', '#8B6B4D', '#0F766E']}
              horizontal={true}
              height={350}
            />
          </div>
        </Card>

        <Card>
          <CardHeader title="Class Support (Sample Count)" subtitle="Number of test samples per class" />
          <div className="h-80">
            <BarChartComponent
              data={supportData}
              xKey="name"
              yKeys="support"
              horizontal={true}
              colors={['#0F766E']}
              height={350}
            />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {confusion_matrix_url && (
          <Card>
            <CardHeader title="Confusion Matrix (Normalized)" subtitle="True vs Predicted labels" />
            <div className="aspect-square flex items-center justify-center p-4">
              <img 
                src={confusion_matrix_url} 
                alt="Confusion matrix" 
                className="max-w-full max-h-96 rounded-lg shadow-sm border border-cream-300"
              />
            </div>
          </Card>
        )}

        {class_distribution_url && (
          <Card>
            <CardHeader title="Class Distribution" subtitle="Training data class balance" />
            <div className="aspect-square flex items-center justify-center p-4">
              <img 
                src={class_distribution_url} 
                alt="Class distribution" 
                className="max-w-full max-h-96 rounded-lg shadow-sm border border-cream-300"
              />
            </div>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader title="Detailed Classification Report" subtitle="Per-class precision, recall, F1-score, and support" />
        <Table
          columns={[
            { key: 'class_name', header: 'Class', className: 'font-medium max-w-xs truncate' },
            { key: 'precision', header: 'Precision', className: 'text-right', render: (r: any) => formatPercent(r.precision) },
            { key: 'recall', header: 'Recall', className: 'text-right', render: (r: any) => formatPercent(r.recall) },
            { key: 'f1_score', header: 'F1-Score', className: 'text-right font-medium', render: (r: any) => formatPercent(r.f1_score) },
            { key: 'support', header: 'Support', className: 'text-right text-brown-500' },
            { 
              key: 'f1_bar', 
              header: 'F1 Visual', 
              className: 'w-40',
              render: (row: any) => (
                <ProgressBar value={row.f1_score * 100} color={row.f1_score > 0.7 ? '#22C55E' : row.f1_score > 0.4 ? '#F59E0B' : '#EF4444'} height={6} showLabel />
              )
            },
          ]}
          data={classification_report}
          keyExtractor={(row) => row.class_name}
        />
      </Card>

      {metrics.training_config && (
        <Card>
          <CardHeader title="Training Configuration" subtitle="Hyperparameters and settings used" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            {Object.entries(metrics.training_config).map(([key, value]) => (
              <div key={key} className="p-3 bg-cream-100 rounded-lg">
                <p className="text-brown-500 capitalize">{key.replace(/_/g, ' ')}</p>
                <p className="font-mono text-brown-800">{JSON.stringify(value)}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {metrics.per_class_metrics && (
        <Card>
          <CardHeader title="Per-Class Metrics Summary" subtitle="Detailed breakdown" />
          <Table
            columns={[
              { key: 'class', header: 'Class', className: 'font-medium' },
              { key: 'precision', header: 'Precision', className: 'text-right', render: (r: any) => formatPercent(r.precision) },
              { key: 'recall', header: 'Recall', className: 'text-right', render: (r: any) => formatPercent(r.recall) },
              { key: 'f1', header: 'F1', className: 'text-right', render: (r: any) => formatPercent(r.f1) },
              { key: 'support', header: 'Support', className: 'text-right' },
            ]}
            data={Object.entries(metrics.per_class_metrics).map(([className, vals]) => ({
              class: className,
              ...vals,
            }))}
            keyExtractor={(row) => row.class}
          />
        </Card>
      )}
    </div>
  );
}