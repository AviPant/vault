import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronRight, Download, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

export default function ReasoningTrace({ steps, downloadFile, isStreaming, isLast }) {
  const [traceExpanded, setTraceExpanded] = useState(true);

  if (!steps || steps.length === 0) return null;

  const renderTraceStep = (step, idx) => {
    const isError = step.type === 'error';
    const isFile = step.type === 'file';

    let lineText = step.text;
    let prefix = '>';
    let prefixColor = 'text-status-success';
    let bgTint = 'bg-transparent';

    if (isError) {
      prefix = '✗';
      prefixColor = 'text-destructive';
      bgTint = 'bg-destructive/10';
    } else if (isFile) {
      prefix = '⬡';
      prefixColor = 'text-accent-teal';
      bgTint = 'bg-accent-teal/5';
      lineText = `Document generated: ${step.filepath.split('\\').pop().split('/').pop()}`;
    } else if (step.text?.toLowerCase().includes('phase 1')) {
      prefix = '◆';
      prefixColor = 'text-status-info';
      bgTint = 'bg-status-info/5';
    } else if (step.text?.toLowerCase().includes('phase 2')) {
      prefix = '▶';
      prefixColor = 'text-status-warning';
      bgTint = 'bg-status-warning/5';
    } else if (step.text?.toLowerCase().includes('phase 3')) {
      prefix = '◈';
      prefixColor = 'text-accent-teal';
      bgTint = 'bg-accent-teal/5';
    }

    return (
      <div key={idx} className={`flex items-start space-x-2 px-3 py-1.5 rounded ${bgTint} group transition-colors hover:bg-surface-main/40`}>
        <span className={`font-jetbrains-mono text-xs ${prefixColor} flex-shrink-0 mt-px select-none`}>{prefix}</span>
        <div className="flex-1 min-w-0">
          <p className="font-jetbrains-mono text-[11px] text-on-surface-variant/90 leading-relaxed break-words">{lineText}</p>
          {step.time && <span className="font-jetbrains-mono text-[9px] text-text-dim/40">{step.time}</span>}
          {isFile && (
            <button
              onClick={() => downloadFile(step.filepath.split('\\').pop().split('/').pop())}
              className="mt-1.5 px-2.5 py-1 text-[10px] font-jetbrains-mono border border-accent-teal/30 text-accent-teal rounded hover:bg-accent-teal/10 transition-colors inline-flex items-center"
            >
              <Download size={10} className="mr-1" /> Download
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <Card className="bg-[#0a0a14] border-muted/50 rounded-lg overflow-hidden shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] border">
      <button
        onClick={() => setTraceExpanded(!traceExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 hover:bg-surface-main/30 transition-colors border-b border-muted/50"
      >
        <div className="flex items-center space-x-2">
          {isStreaming && isLast ? (
            <Loader2 size={12} className="text-accent-teal animate-spin" />
          ) : (
            <Terminal size={12} className="text-accent-teal" />
          )}
          <span className="text-[10px] font-jetbrains-mono uppercase text-text-dim tracking-wider">
            {isStreaming && isLast ? 'Agent is thinking...' : 'Agent Reasoning Trace'}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[9px] font-jetbrains-mono px-1.5 py-0.5 rounded bg-accent-teal/10 text-accent-teal border border-accent-teal/20">{steps.length} STEPS</span>
          {traceExpanded ? <ChevronDown size={14} className="text-text-dim" /> : <ChevronRight size={14} className="text-text-dim" />}
        </div>
      </button>
      {traceExpanded && (
        <CardContent className="p-2 space-y-0.5">
          {steps.map((step, i) => renderTraceStep(step, i))}
        </CardContent>
      )}
    </Card>
  );
}
