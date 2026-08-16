import { useState } from 'react';
import { useClassify } from '@/hooks/useApi';
import { Card, CardHeader, Button, Textarea, Badge } from '@/components/ui';
import { Loader2, Search, FileText, ArrowRight, Copy, Check } from 'lucide-react';
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

  const handleClassify = async () => {
    if (!narrative.trim()) return;
    try {
      const res = await classify(narrative, topK);
      setResult(res);
    } catch (err) {
      // Error handled by hook
    }
  };

  const handleSampleClick = (sample: string) => {
    setNarrative(sample);
    setResult(null);
  };

  const handleCopy = async () => {
    if (!result) return;
    const text = `Predicted: ${result.predicted_label}\n\nEvidence:\n${result.evidence.map(e => `#${e.rank} (${(e.similarity * 100).toFixed(1)}%) - ${e.label} [${e.domain}]: ${e.snippet}`).join('\n\n')}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brown-800">RAG Explorer</h1>
          <p className="text-brown-500 mt-1">Classify an incident narrative and retrieve similar historical reports as evidence</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader title="Incident Narrative" subtitle="Enter or paste an incident description" />
          
          <div className="space-y-4">
            <Textarea
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
              placeholder="Paste an incident narrative here..."
              rows={8}
              label="Narrative"
            />
            
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-brown-700">
                <span>Top-K Evidence:</span>
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
                className="flex-1"
                disabled={!narrative.trim()}
              >
                <Search className="w-4 h-4" />
                Classify & Retrieve Evidence
              </Button>
            </div>

            <div className="pt-4 border-t border-cream-300">
              <p className="text-sm font-medium text-brown-700 mb-2">Try a sample:</p>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_NARRATIVES.map((sample, idx) => (
                  <Button
                    key={idx}
                    variant="outline"
                    size="sm"
                    onClick={() => handleSampleClick(sample)}
                    className="truncate max-w-[200px]"
                  >
                    Sample {idx + 1}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader 
            title="Results" 
            subtitle={result ? `Processed in ${result.processing_time_ms.toFixed(1)}ms` : 'Submit a narrative to see results'}
            action={
              result && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={handleCopy}
                  loading={copied}
                >
                  {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                </Button>
              )
            }
          />
          
          {result ? (
            <div className="space-y-4">
              <div className={cn(
                'p-4 rounded-lg border',
                'bg-risk-critical/10 border-risk-critical/20 text-risk-critical'
              )}>
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  <span className="font-semibold text-lg">Predicted Risk Category:</span>
                </div>
                <p className="text-xl font-bold mt-1">{result.predicted_label}</p>
              </div>

              <div>
                <h4 className="font-medium text-brown-700 mb-3">Top {result.evidence.length} Most Similar Historical Reports</h4>
                <div className="space-y-3">
                  {result.evidence.map((ev) => (
                    <div 
                      key={ev.rank}
                      className={cn(
                        'p-4 rounded-lg border',
                        'bg-cream-50 border-cream-300'
                      )}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="info" size="sm">#{ev.rank}</Badge>
                            <Badge variant="default" size="sm">
                              {(ev.similarity * 100).toFixed(1)}% similar
                            </Badge>
                            <Badge variant="default" size="sm">{ev.domain}</Badge>
                          </div>
                          <p className="font-medium text-brown-800">{ev.label}</p>
                        </div>
                        <div className="w-24 text-right text-sm text-brown-500">
                          {(ev.similarity * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="mt-2 h-2 bg-cream-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-brown-700 rounded-full transition-all duration-500"
                          style={{ width: `${ev.similarity * 100}%` }}
                        />
                      </div>
                      <p className="mt-2 text-sm text-brown-600 italic">"{ev.snippet}"</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-brown-500">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Enter a narrative and click "Classify & Retrieve Evidence" to see results</p>
            </div>
          )}
        </Card>
      </div>

      {error && (
        <Card className="border-risk-critical/50 bg-risk-critical/5">
          <div className="flex items-center gap-3 p-4 text-risk-critical">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </Card>
      )}
    </div>
  );
}

// Need to import AlertCircle
import { AlertCircle } from 'lucide-react';