import { useState } from 'react';
import { useAnalyze } from '@/hooks/useApi';
import { Section, Card, CardHeader, Button, Input, Badge, ProgressBar } from '@/components/ui/DataDisplay';
import { Loader2, Search, ClipboardList, AlertTriangle, BarChart2, FileText, Sparkles, Trash2, Copy } from 'lucide-react';
import { cn } from '@/utils/helpers';

const QUICK_QUERIES = [
  { label: 'Summary', query: 'summary', icon: FileText, description: 'Dataset overview and key stats', color: '#3B82F6' },
  { label: 'Quality / Issues', query: 'quality', icon: AlertTriangle, description: 'Data quality audit', color: '#EF4444' },
  { label: 'Safety / Critical', query: 'safety', icon: AlertTriangle, description: 'Safety-criticality breakdown', color: '#F97316' },
  { label: 'Classes / Balance', query: 'classes', icon: BarChart2, description: 'Class distribution analysis', color: '#22C55E' },
];

const EXAMPLE_QUERIES = [
  "analyze engine failure during takeoff",
  "what are the data quality issues",
  "show me critical safety categories",
  "class distribution and balance",
  "analyze bird strike during approach",
  "quality issues in power grid data",
];

export function AssistantPage() {
  const [query, setQuery] = useState('');
  const [history, setHistory] = useState<Array<{ query: string; response: string[]; timestamp: Date }>>([]);
  const { analyze, loading, error } = useAnalyze();

  const handleSubmit = async (q: string) => {
    if (!q.trim()) return;
    setQuery(q);
    try {
      const response = await analyze(q);
      setHistory(prev => [{ query: q, response: response.lines, timestamp: new Date() }, ...prev].slice(0, 20));
    } catch (err) {
      // Error handled by hook
    }
  };

  const handleQuickQuery = (q: string) => {
    handleSubmit(q);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(query);
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    handleSubmit(example);
  };

  const copyResponse = async (lines: string[]) => {
    await navigator.clipboard.writeText(lines.join('\n'));
  };

  const clearHistory = () => {
    setHistory([]);
  };

  return (
    <div className="space-y-6">
      <Section
        title="Data Assistant"
        subtitle="Keyless analysis computed with pandas - no LLM, no API key"
        action={
          history.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearHistory}>
              <Trash2 className="w-4 h-4" />
              Clear History
            </Button>
          )
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader title="Quick Analysis" subtitle="One-click insights" />
          
          <div className="space-y-2">
            {QUICK_QUERIES.map(({ label, query: q, icon: Icon, description, color }) => (
              <Button
                key={q}
                variant="outline"
                className="w-full justify-start gap-3"
                onClick={() => handleQuickQuery(q)}
                loading={loading}
                style={{ borderLeft: `4px solid ${color}` }}
              >
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
                  <Icon className="w-5 h-5" style={{ color }} />
                </div>
                <div className="text-left flex-1">
                  <div className="font-medium text-brown-800">{label}</div>
                  <div className="text-xs text-brown-500">{description}</div>
                </div>
              </Button>
            ))}
          </div>

          <div className="mt-6 p-4 bg-cream-100 rounded-lg">
            <p className="text-sm font-medium text-brown-700 mb-3">Example Queries</p>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {EXAMPLE_QUERIES.map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => handleExampleClick(example)}
                  className="w-full text-left p-2 text-sm text-brown-600 hover:text-brown-800 hover:bg-cream-200 rounded transition-colors truncate"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Query Input" />
          
          <div className="space-y-4">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about the data: quality, safety, classes, or 'analyze <narrative>'"
              label="Your Question"
            />
            
            <div className="flex gap-2">
              <Button 
                onClick={() => handleSubmit(query)} 
                loading={loading}
                disabled={!query.trim()}
                size="lg"
              >
                <Search className="w-4 h-4" />
                Analyze
              </Button>
              {history.length > 0 && (
                <Button variant="secondary" size="lg" onClick={clearHistory}>
                  <Trash2 className="w-4 h-4" />
                  Clear
                </Button>
              )}
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}
          </div>

          <CardHeader title="Analysis History" className="mt-6" />
          
          {history.length > 0 ? (
            <div className="space-y-4">
              {history.map((item, idx) => (
                <Card key={idx} className="bg-cream-50 border-cream-300">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2 text-brown-700 flex-1 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
                        <Sparkles className="w-4 h-4 text-purple-600" />
                      </div>
                      <div>
                        <div className="font-medium text-brown-800 truncate">Query: {item.query}</div>
                        <div className="text-xs text-brown-500">{item.timestamp.toLocaleTimeString()}</div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => copyResponse(item.response)}>
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-cream-200 overflow-x-auto max-h-96">
                    <pre className="text-sm font-mono text-brown-800 whitespace-pre-wrap text-left">
                      {item.response.join('\n')}
                    </pre>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 text-brown-500">
              <ClipboardList className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Click a quick analysis button or type a question to get insights</p>
              <p className="text-sm mt-1">The assistant uses pandas to analyze the loaded dataset - no API keys required</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}