import React from 'react';
import { Upload, Zap, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function ChatInput({ 
  prompt, setPrompt, handleSend, isStreaming, ollamaOnline, 
  dragOver, setDragOver, handleDrop, attachedImage, setAttachedImage, handleImageUpload 
}) {
  return (
    <div
      className="p-4 bg-surface border-t border-muted flex-shrink-0"
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      {/* Staged file preview */}
      {attachedImage && (
        <div className="mb-2.5 flex items-center space-x-2 bg-accent-teal/5 border border-accent-teal/20 rounded-lg px-3 py-2">
          <img src={attachedImage} alt="Preview" className="h-10 w-10 object-cover rounded border border-accent-teal/40" />
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-jetbrains-mono text-accent-teal truncate">File staged for analysis</p>
            <p className="text-[9px] text-text-dim/60">Will be sent with your next task</p>
          </div>
          <button onClick={() => setAttachedImage(null)} className="p-1 text-text-dim hover:text-destructive rounded transition-colors">
            <X size={14} />
          </button>
        </div>
      )}
      
      <div className={`flex items-center space-x-2 bg-surface-main border rounded-lg p-1.5 transition-all duration-200 ${
        dragOver ? 'border-accent-teal ring-2 ring-accent-teal/20 bg-accent-teal/5' : 'border-muted focus-within:border-accent-teal focus-within:ring-1 focus-within:ring-accent-teal'
      }`}>
        <label className="p-2 text-text-dim hover:text-accent-teal cursor-pointer rounded transition-colors" title="Attach file">
          <Upload size={18} />
          <input type="file" className="hidden" accept="image/*,.pdf" onChange={handleImageUpload} disabled={isStreaming} />
        </label>
        
        <Input
          className="flex-1 bg-transparent border-none focus-visible:ring-0 focus-visible:ring-offset-0 text-sm p-2 text-on-surface placeholder:text-text-dim"
          placeholder={dragOver ? 'Drop file here...' : 'Describe the next task...'}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
          disabled={isStreaming}
        />
        
        <Button
          onClick={handleSend}
          disabled={isStreaming || (!prompt.trim() && !attachedImage) || !ollamaOnline}
          className="px-4 py-2 bg-accent-teal text-surface-main font-semibold text-xs rounded hover:bg-[#38debb] disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center"
        >
          <Zap size={12} className="mr-1" />Run Task
        </Button>
      </div>
      
      <p className="text-center mt-1.5 text-[9px] font-jetbrains-mono text-text-dim/40 uppercase tracking-widest">
        Air-Gapped • All processing on-premises • Drop files anywhere
      </p>
    </div>
  );
}
