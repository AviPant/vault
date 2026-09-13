import React from 'react';
import { Lock } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import ReasoningTrace from './ReasoningTrace';

export default function ChatFeed({ chatHistory, isStreaming, downloadFile, chatEndRef, extractInfo }) {
  return (
    <ScrollArea className="flex-1 min-h-0 w-full">
      <div className="p-6 space-y-6">
        {chatHistory.map((msg, index) => (
          <div key={index} className="max-w-3xl mx-auto w-full">
            {msg.role === 'user' ? (
              <div className="bg-surface border border-muted rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-jetbrains-mono uppercase text-text-dim tracking-wider">Task Input</span>
                  <span className="text-[10px] font-jetbrains-mono text-status-success flex items-center">
                    <Lock size={10} className="mr-1" /> LOCAL ONLY
                  </span>
                </div>
                {msg.image && (
                  <div className="mb-3">
                    <img src={msg.image} alt="Upload" className="max-h-40 rounded border border-muted" />
                  </div>
                )}
                <p className="text-sm text-on-surface whitespace-pre-wrap">{msg.content}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Extracted Info */}
                {msg.content && extractInfo && extractInfo(msg.content) && (
                  <div className="bg-surface border border-muted rounded-lg p-4">
                    <span className="text-[10px] font-jetbrains-mono uppercase text-text-dim tracking-wider mb-3 block">Extracted Information</span>
                    <div className="grid grid-cols-2 gap-3">
                      {extractInfo(msg.content).map((info, i) => (
                        <div key={i} className="bg-surface-main rounded p-3 border border-muted">
                          <span className="text-[10px] font-jetbrains-mono text-text-dim uppercase">{info.label}</span>
                          <p className={`text-sm font-medium mt-0.5 ${info.color || 'text-on-surface'}`}>{info.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reasoning Trace */}
                <ReasoningTrace 
                  steps={msg.steps} 
                  downloadFile={downloadFile} 
                  isStreaming={isStreaming} 
                  isLast={index === chatHistory.length - 1} 
                />

                {/* Response Content */}
                {(msg.content || (isStreaming && index === chatHistory.length - 1)) && (
                  <div className="bg-surface border border-muted rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[10px] font-jetbrains-mono uppercase text-accent-teal tracking-wider">V.A.U.L.T. Agent</span>
                    </div>
                    <div className="prose prose-sm prose-invert max-w-none font-inter text-on-surface leading-relaxed">
                      {msg.content.split('\n').map((line, i) => (
                        <p key={i} className="mb-2 last:mb-0 min-h-[1em]">{line.replace(/\*/g, '')}</p>
                      ))}
                      {isStreaming && index === chatHistory.length - 1 && (
                        <span className="inline-block w-1.5 h-3 bg-accent-teal ml-1 animate-pulse" />
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
    </ScrollArea>
  );
}
