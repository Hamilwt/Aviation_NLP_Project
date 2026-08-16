import { useState } from 'react';
import { useClassify } from '@/hooks/useApi';
import { Section, Card, CardHeader, Button, Textarea, Badge, ProgressBar, MetricCard } from '@/components/ui/DataDisplay';
import { Loader2, Search, FileText, ArrowRight, Copy, Check, X, Sparkles } from 'lucide-react';
import { cn } from '@/utils/helpers';

const SAMPLE_NARRATIVES = [
  "I was cleared for the ILS approach but misheard the altitude restriction due to heavy static on the radio frequency. We descended below the minimum safe altitude and received a terrain warning.",
  "During cruise at FL350, the left engine experienced an uncommanded shutdown. The crew declared an emergency and diverted to the nearest suitable airport. Single engine landing completed without incident.",
  "A large flock of birds was encountered during takeoff roll. Multiple bird strikes were observed on the windshield and leading edges. The takeoff was continued and the aircraft returned for inspection.",
  "Power grid experienced a cascading failure following a transmission line fault during severe weather. Over 500,000 customers lost power across multiple states. Restoration took 72 hours.",
  "Unplanned power cut affecting the London operating zone. Postcodes SW1, SW2, SW3 affected. Approximately 15,000 customers without power. Cause: underground cable fault.",
];

export function RAGPage() {
  const [narrative, setNarrative] = useState(SAMPLE_NARRATIVES[0]);
  const [topK, setTopK] = useState(3);
  const { classify, loading, error } = useClassify();
  const [result, setResult] = useState<{
    predicted_label: string;
    evidence: Array<{ rank: number; similarity: number; label: string; domain: string; snippet: string }>;
    processing_time_ms: number;
  } | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeSample, setActiveSample] = useState(0);

  const handleClassify = async () => {
    if (!narrative.trim()) return;
    try {
      const res = await classify(narrative, topK);
      setResult(res);
      setActiveSample(-1);
    } catch (err) {
      // Error handled by hook
    }
  };

  const handleSampleClick = (sample: string, index: number) => {
    setNarrative(sample);
    setActiveSample(index);
    setResult(null);
  };

  const handleCopy = async () => {
    if (!result) return;
    const text = `Predicted: ${result.predicted_label}\n\nEvidence:\n${result.evidence.map(e => `#${e.rank} (${(e.similarity * 100).toFixed(1)}%) - ${e.label} [${e.domain}]: ${e.snippet}`).join('\n\n')}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClear = () => {
    setNarrative('');
    setResult(null);
    setActiveSample(-1);
  };

  return (
    <div className="space-y-6">
      <Section
        title="RAG Explorer"
        subtitle="Classify an incident narrative and retrieve similar historical reports as evidence"
        action={
          <Button variant="ghost" size="sm" onClick={handleClear} disabled={!narrative.trim() && !result}>
            <X className="w-4 h-4" />
            Clear
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader title="Sample Narratives" subtitle="Click to test classification" />
          <div className="space-y-2">
            {SAMPLE_NARRATIVES.map((sample, idx) => (
              <Button
                key={idx}
                variant={activeSample === idx ? 'primary' : 'outline'}
                className="w-full justify-start text-left p-3 h-auto gap-2"
                onClick={() => handleSampleClick(sample, idx)}
                loading={loading}
              >
                <Sparkles className="w-4 h-4 flex-shrink-0" />
                <div className="text-sm leading-relaxed">
                  {sample.slice(0, 80)}...
                </div>
              </Button>
            ))}
          </div>
          
          <div className="mt-6 p-4 bg-cream-100 rounded-lg">
            <p className="text-sm font-medium text-brown-700 mb-2">Quick Actions</p>
            <div className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start" onClick={handleClear} disabled={!narrative.trim() && !result}>
                <X className="w-4 h-4" />
                Clear Input
              </Button>
              <Button variant="ghost" size="sm" className="w-full justify-start" onClick={() => setNarrative(SAMPLE_NARRATIVES[0])}>
                <ArrowRight className="w-4 h-4" />
                Load First Sample
              </Button>
            </div>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader 
            title="Incident Narrative" 
            subtitle="Enter or paste an incident description for classification"
            action={
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-sm text-brown-700">
                  <span>Top-K:</span>
                  <select
                    value={topK}
                    onChange={(e) => setTopK(Number(e.target.value))}
                    className="px-3 py-1.5 border-cream-300 rounded-lg text-sm focus:ring-2 focus:ring-brown-500 focus:border-transparent"
                  >
                    <option value={1}>1</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                  </select>
                </label>
                <Button 
                  onClick={handleClassify} 
                  loading={loading}
                  disabled={!narrative.trim()}
                  size="lg"
                >
                  <Search className="w-4 h-4" />
                  Classify & Retrieve Evidence
                </Button>
              </div>
            }
          />
          
          <Textarea
            value={narrative}
            onChange={(e) => { setNarrative(e.target.value); setActiveSample(-1); }}
            placeholder="Paste an incident narrative here..."
            rows={6}
            label="Narrative"
          />

          {result && (
            <div className="mt-6 space-y-6 animate-fade-in">
              <Card className="bg-brown-50 border-brown-200">
                <CardHeader 
                  title="Prediction Result" 
                  subtitle={`Processed in ${result.processing_time_ms.toFixed(1)}ms`}
                  action={
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={handleCopy}
                      loading={copied}
                    >
                      {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  }
                />
                <div className="flex items-center gap-4 p-4 bg-brown-100 rounded-lg">
                  <div className="w-12 h-12 bg-brown-700 rounded-full flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-brown-500 text-sm">Predicted Risk Category</p>
                    <p className="text-2xl font-bold text-brown-800">{result.predicted_label}</p>
                  </div>
                </div>
              </Card>

              <Card>
                <CardHeader title={`Top ${result.evidence.length} Similar Historical Reports`} subtitle="Evidence retrieved via cosine similarity on TF-IDF vectors" />
                <div className="space-y-4">
                  {result.evidence.map((ev) => (
                    <Card key={ev.rank} className={cn('relative overflow-hidden', ev.similarity > 0.7 && 'border-green-300')}>
                      <div className="absolute top-0 left-0 h-full w-1" style={{ backgroundColor: ev.similarity > 0.7 ? '#22C55E' : ev.similarity > 0.4 ? '#F59E0B' : '#EF4444' }} />
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <Badge variant="info" size="sm">#{ev.rank}</Badge>
                            <Badge variant={ev.similarity > 0.7 ? 'success' : ev.similarity > 0.4 ? 'warning' : 'default'} size="sm">
                              {(ev.similarity * 100).toFixed(1)}% Similar
                            </Badge>
                            <Badge variant="default" size="sm">{ev.domain}</Badge>
                          </div>
                          <p className="font-medium text-brown-800">{ev.label}</p>
                        </div>
                        <div className="flex items-center gap-4 text-right">
                          <div className="w-32">
                            <ProgressBar value={ev.similarity * 100} color={ev.similarity > 0.7 ? '#22C55E' : ev.similarity > 0.4 ? '#F59E0B' : '#EF4444'} height={8} showLabel />
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 p-3 bg-cream-100 rounded-lg border border-cream-200">
                        <p className="text-sm text-brown-600 italic">"{ev.snippet}"</p>
                      </div>
                    </Card>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </Card>
      </div>

      {error && (
        <Card className="border-red-300 bg-red-50">
          <div className="flex items-center gap-3 p-4 text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </Card>
      )}
    </div>
  );
}

import { AlertCircle } from 'lucide-react';