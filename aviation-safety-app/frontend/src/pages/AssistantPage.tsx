import { useState, useEffect, useRef } from 'react';
import { useAnalyze, useOllamaStatus } from '@/hooks/useApi';
import { Section, Card, CardHeader, Button, Input, Badge } from '@/components/ui';
import { AlertTriangle, BarChart2, FileText, Trash2, Copy, Bot, Wifi, WifiOff, Lightbulb, Send } from 'lucide-react';
import { cn } from '@/utils/helpers';

const QUICK_QUERIES = [
  { label: 'Summary', query: 'Give me a summary of the aviation and power grid safety dataset.', icon: FileText, description: 'Dataset overview and key stats', color: '#3B82F6' },
  { label: 'Quality / Issues', query: 'What are the data quality issues in this dataset?', icon: AlertTriangle, description: 'Data quality audit', color: '#EF4444' },
  { label: 'Safety / Critical', query: 'What are the most critical safety categories and risks?', icon: AlertTriangle, description: 'Safety-criticality breakdown', color: '#F97316' },
  { label: 'Classes / Balance', query: 'Show me the class distribution and balance of anomaly categories.', icon: BarChart2, description: 'Class distribution analysis', color: '#22C55E' },
];

const EXAMPLE_QUERIES = [
  "analyze engine failure during takeoff",
  "what are the data quality issues",
  "show me critical safety categories",
  "class distribution and balance",
  "analyze bird strike during approach",
  "what causes power grid blackouts",
];

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  usedLlm?: boolean;
  model?: string | null;
  timestamp: Date;
}

export function AssistantPage() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const { analyze, loading, error } = useAnalyze();
  const { status } = useOllamaStatus();
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (status?.models?.length && !selectedModel) {
      setSelectedModel(status.model);
    }
  }, [status, selectedModel]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  const connected = !!status?.connected;

  const sendMessage = async (q: string) => {
    const text = q.trim();
    if (!text) return;
    setQuery('');
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    try {
      const response = await analyze(text, selectedModel || undefined, true);
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: response.reply || response.lines.join('\n'),
        usedLlm: response.used_llm,
        model: response.model,
        timestamp: new Date(),
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: `Error: ${err instanceof Error ? err.message : 'Analysis failed'}`,
        usedLlm: false,
        timestamp: new Date(),
      }]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(query);
    }
  };

  const copyMessage = async (text: string) => {
    await navigator.clipboard.writeText(text);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="space-y-6">
      <Section
        title="Data Assistant"
        subtitle="Local Ollama LLM answers only within the aviation & power-grid safety domain"
        action={
          messages.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearChat}>
              <Trash2 className="w-4 h-4" />
              Clear Chat
            </Button>
          )
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader 
                title="Ollama Status" 
                subtitle="Local LLM server connection"
                action={
                  <Badge variant={connected ? 'success' : 'error'} size="sm">
                    {connected ? 'Live' : 'Offline'}
                  </Badge>
                }
              />
              <div className="space-y-3">
                <div className={cn(
                  'flex items-center gap-3 p-3 rounded-lg border',
                  connected ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                )}>
                  {connected ? <Wifi className="w-5 h-5 text-green-600 flex-shrink-0" /> : <WifiOff className="w-5 h-5 text-red-500 flex-shrink-0" />}
                  <div className="min-w-0">
                    <p className={cn('text-sm font-medium', connected ? 'text-green-800' : 'text-red-700')}>
                      {connected ? 'Ollama Connected' : 'Ollama Disconnected'}
                    </p>
                    <p className="text-xs text-brown-500 truncate">{status?.base_url || 'http://localhost:11434'}</p>
                  </div>
                </div>

                {connected && (
                  <div>
                    <label className="block text-sm font-medium text-brown-700 mb-1.5">
                      Active Model ({status?.models?.length || 0} live)
                    </label>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-cream-300 rounded-lg text-sm focus:ring-2 focus:ring-brown-500 focus:border-transparent"
                    >
                      {(status?.models || []).map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <p className="mt-2 text-xs text-brown-500 flex items-center gap-1">
                      <Bot className="w-3.5 h-3.5" />
                      Replies are constrained to aviation & power-grid safety topics.
                    </p>
                  </div>
                )}

                {!connected && (
                  <div className="text-xs text-brown-500 space-y-1.5">
                    <p>Start Ollama and pull a model to enable LLM answers:</p>
                    <code className="block bg-cream-100 p-2 rounded font-mono">ollama serve</code>
                    <code className="block bg-cream-100 p-2 rounded font-mono">ollama pull llama3</code>
                    <p className="pt-1">Until then the rule-based pandas analyst answers.</p>
                  </div>
                )}
              </div>
            </Card>

            <Card>
              <CardHeader title="Quick Analysis" subtitle="One-click insights" />
              <div className="space-y-2">
                {QUICK_QUERIES.map(({ label, query: q, icon: Icon, description, color }) => (
                  <Button
                    key={label}
                    variant="outline"
                    className="w-full justify-start gap-3"
                    onClick={() => sendMessage(q)}
                    loading={loading}
                    style={{ borderLeft: `4px solid ${color}` }}
                  >
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${color}20` }}>
                      <Icon className="w-5 h-5" style={{ color }} />
                    </div>
                    <div className="text-left flex-1 min-w-0">
                      <div className="font-medium text-brown-800">{label}</div>
                      <div className="text-xs text-brown-500 truncate">{description}</div>
                    </div>
                  </Button>
                ))}
              </div>
            </Card>

            <div className="p-4 bg-cream-100 rounded-lg">
              <p className="text-sm font-medium text-brown-700 mb-3">Example Queries</p>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {EXAMPLE_QUERIES.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(example)}
                    className="w-full text-left p-2 text-sm text-brown-600 hover:text-brown-800 hover:bg-cream-200 rounded transition-colors truncate"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <Card className="lg:col-span-2 flex flex-col">
            <CardHeader
              title="Chat"
              subtitle={connected
                ? `Model ${selectedModel || status?.model || 'default'} will answer domain questions only`
                : 'Ollama offline - rule-based analyst is answering'}
              action={
                connected && (
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 px-2.5 py-1 rounded-full">
                    <Wifi className="w-3.5 h-3.5" />
                    Ollama live
                  </span>
                )
              }
            />

            <div className="flex-1 space-y-4 min-h-[400px] max-h-[560px] overflow-y-auto pr-1">
              {messages.length === 0 ? (
                <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-brown-500">
                  <Bot className="w-16 h-16 mb-4 opacity-40" />
                  <p className="text-lg font-medium text-brown-700">Ask about the safety data</p>
                  <p className="text-sm mt-1 text-center max-w-sm">
                    {connected
                      ? `Ask anything about aviation incidents or power-grid events - ${selectedModel || status?.model} will answer within this domain.`
                      : 'Connect Ollama for LLM answers. The rule-based analyst works without it.'}
                  </p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0 mt-1">
                        <Bot className="w-4 h-4 text-purple-600" />
                      </div>
                    )}
                    <div className={cn(
                      'max-w-[85%] rounded-xl px-4 py-3 border',
                      msg.role === 'user'
                        ? 'bg-brown-700 text-cream-50 border-brown-700'
                        : 'bg-white border-cream-300'
                    )}>
                      <pre className={cn(
                        'whitespace-pre-wrap font-sans text-sm leading-relaxed',
                        msg.role === 'user' ? 'text-cream-50' : 'text-brown-800'
                      )}>
                        {msg.text}
                      </pre>
                      <div className={cn(
                        'mt-2 flex items-center gap-2 text-xs',
                        msg.role === 'user' ? 'text-cream-200' : 'text-brown-400'
                      )}>
                        <span>{msg.timestamp.toLocaleTimeString()}</span>
                        {msg.role === 'assistant' && msg.usedLlm !== undefined && (
                          <Badge variant={msg.usedLlm ? 'success' : 'default'} size="sm">
                            {msg.usedLlm ? `Ollama LLM${msg.model ? ` · ${msg.model}` : ''}` : 'Rule-based analyst'}
                          </Badge>
                        )}
                        {msg.role === 'assistant' && (
                          <button
                            onClick={() => copyMessage(msg.text)}
                            className="hover:text-brown-700 transition-colors"
                            aria-label="Copy response"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="pt-4 border-t border-cream-200 mt-4">
              {error && (
                <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}
              <div className="flex gap-2">
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about flight safety, power outages, grid events..."
                />
                <Button
                  onClick={() => sendMessage(query)}
                  loading={loading}
                  disabled={!query.trim()}
                  size="lg"
                  className="flex-shrink-0"
                >
                  <Send className="w-4 h-4" />
                  Ask
                </Button>
              </div>
              <p className="mt-2 text-xs text-brown-500 flex items-center gap-1.5">
                <Lightbulb className="w-3.5 h-3.5" />
                {connected
                  ? `The LLM answers ONLY aviation & power-grid safety questions - unrelated questions are refused.`
                  : 'Start Ollama to enable the local LLM (no API key, fully private).'}
              </p>
            </div>
          </Card>
        </div>
      </Section>
    </div>
  );
}