import { useState } from 'react';
import { useAnalyze } from '@/hooks/useApi';
import { Card, CardHeader, Button, Input } from '@/components/ui';
import { Loader2, Search, ClipboardList, AlertTriangle, BarChart2, FileText, Sparkles } from 'lucide-react';

const QUICK_QUERIES = [
  { label: 'Summary', query: 'summary', icon: FileText, description: 'Dataset overview and key stats' },
  { label: 'Quality / Issues', query: 'quality', icon: AlertTriangle, description: 'Data quality audit' },
  { label: 'Safety / Critical', query: 'safety', icon: AlertTriangle, description: 'Safety-criticality breakdown' },
  { label: 'Classes / Balance', query: 'classes', icon: BarChart2, description: 'Class distribution analysis' },
];

export function AssistantPage() {
  const [query, setQuery] = useState('');
  const [history, setHistory] = useState<Array<{ query: string; response: string[] }>>([]);
  const { analyze, loading, error } = useAnalyze();

  const handleSubmit = async (q: string) => {
    if (!q.trim()) return;
    setQuery(q);
    try {
      const response = await analyze(q);
      setHistory(prev => [{ query: q, response: response.lines }, ...prev].slice(0, 10));
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brown-800">Data Assistant</h1>
          <p className="text-brown-500 mt-1">Keyless analysis computed with pandas - no LLM, no API key</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader title="Quick Analysis" subtitle="Click a button or type a question" />
          
          <div className="space-y-2">
            {QUICK_QUERIES.map(({ label, query: q, icon: Icon, description }) => (
              <Button
                key={q}
                variant="outline"
                className="w-full justify-start gap-3"
                onClick={() => handleQuickQuery(q)}
                loading={loading}
              >
                <Icon className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-medium">{label}</div>
                  <div className="text-xs text-brown-500">{description}</div>
                </div>
              </Button>
            ))}
          </div>

          <div className="pt-4 border-t border-cream-300">
            <p className="text-sm font-medium text-brown-700 mb-2">Example queries:</p>
            <ul className="space-y-1 text-sm text-brown-600">
              <li>• "analyze engine failure during takeoff"</li>
              <li>• "what are the data quality issues"</li>
              <li>• "show me critical safety categories"</li>
              <li>• "class distribution and balance"</li>
            </ul>
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
            
            <Button 
              onClick={() => handleSubmit(query)} 
              loading={loading}
              disabled={!query.trim()}
            >
              <Search className="w-4 h-4" />
              Analyze
            </Button>

            {error && (
              <div className="p-3 bg-risk-critical/5 border border-risk-critical/20 rounded-lg text-risk-critical text-sm">
                {error}
              </div>
            )}
          </div>

          <CardHeader title="Analysis Results" className="mt-6" />
          
          {history.length > 0 ? (
            <div className="space-y-4">
              {history.map((item, idx) => (
                <Card key={idx} className="bg-cream-50 border-cream-300">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2 text-brown-700">
                      <Sparkles className="w-4 h-4" />
                      <span className="font-medium">Query: {item.query}</span>
                    </div>
                  </div>
                  <pre className="bg-white p-4 rounded-lg border border-cream-200 overflow-x-auto text-sm">
                    <code className="font-mono text-brown-800 whitespace-pre-wrap">
                      {item.response.join('\n')}
                    </code>
                  </pre>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-brown-500">
              <ClipboardList className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Click a quick analysis button or type a question to get insights</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}