import { useOllamaStatus } from '@/hooks/useApi';
import { cn } from '@/utils/helpers';
import { Bot, Database, Server, Wifi, WifiOff } from 'lucide-react';

export function StatusBar() {
  const { status } = useOllamaStatus();
  const connected = !!status?.connected;
  const modelCount = status?.models?.length ?? 0;

  return (
    <footer className="flex items-center justify-between gap-4 px-4 sm:px-6 h-9 bg-brown-900 text-cream-100 text-xs border-t border-brown-800 shrink-0">
      <div className="flex items-center gap-4 min-w-0">
        <span
          className={cn(
            'inline-flex items-center gap-1.5 font-medium',
            connected ? 'text-green-400' : 'text-red-400'
          )}
          title={connected ? 'Ollama local LLM server is connected' : 'Ollama is not running - start it with "ollama serve"'}
        >
          {connected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
          Ollama {connected ? 'Connected' : 'Disconnected'}
        </span>

        {connected && (
          <>
            <span className="hidden sm:inline-flex items-center gap-1.5 text-brown-200">
              <Bot className="w-3.5 h-3.5" />
              Model: <span className="font-mono text-cream-100">{status?.model || 'N/A'}</span>
            </span>
            <span
              className={cn(
                'inline-flex items-center gap-1.5',
                modelCount > 0 ? 'text-green-400' : 'text-brown-300'
              )}
            >
              <Database className="w-3.5 h-3.5" />
              {modelCount} model{modelCount === 1 ? '' : 's'} live
            </span>
          </>
        )}
      </div>

      <div className="flex items-center gap-4">
        <span className="hidden md:inline-flex items-center gap-1.5 text-brown-200">
          <Server className="w-3.5 h-3.5" />
          {connected ? 'Local inference - no API key required' : 'Rule-based analyst fallback active'}
        </span>
        <span className="text-brown-300">Safety NLP v2.1.0</span>
      </div>
    </footer>
  );
}