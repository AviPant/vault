import React from 'react';
import { ChevronRight, Palette, Terminal, Zap, HardDrive } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export default function TopBar({
  theme,
  setTheme,
  selectedModel,
  setSelectedModel,
  isHighPrecision,
  setIsHighPrecision,
  systemStatus,
  setSystemStatus,
  API
}) {
  return (
    <div className="h-14 flex items-center justify-between px-6 border-b border-muted bg-surface flex-shrink-0">
      <div className="flex items-center space-x-2 text-xs font-jetbrains-mono text-text-dim">
        <span className="text-on-surface">Sovereign AI Workbench</span>
        <ChevronRight size={12} />
        <span className="text-accent-teal">Confidential task execution</span>
      </div>
      <div className="flex items-center space-x-3">
        
        {/* Theme Selector */}
        <div className="flex items-center bg-surface-main rounded border border-muted px-2 py-1">
          <Palette size={12} className="text-text-dim mr-1.5" />
          <select
            value={theme}
            onChange={(e) => {
              document.documentElement.setAttribute('data-theme-transitioning', 'true');
              setTheme(e.target.value);
              setTimeout(() => document.documentElement.removeAttribute('data-theme-transitioning'), 300);
            }}
            className="bg-transparent border-none text-[11px] font-jetbrains-mono text-accent-teal focus:ring-0 py-0 pl-0 pr-4 cursor-pointer outline-none"
          >
            <option value="shadcn-black">Shadcn Black</option>
            <option value="obsidian">Obsidian</option>
            <option value="sapphire">Sapphire</option>
            <option value="emerald">Emerald</option>
            <option value="crimson">Crimson</option>
            <option value="amber">Amber</option>
            <option value="violet">Violet</option>
          </select>
        </div>

        {/* Model Selector */}
        <div className="flex items-center bg-surface-main rounded border border-muted px-2 py-1">
          <Terminal size={12} className="text-text-dim mr-1.5" />
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="bg-transparent border-none text-[11px] font-jetbrains-mono text-accent-teal focus:ring-0 py-0 pl-0 pr-4 cursor-pointer outline-none"
          >
            <option value="agent">Auto (Orchestrator)</option>
            <option value="llama3.1:8b">llama3.1:8b</option>
            <option value="qwen2.5-coder:7b">qwen2.5-coder:7b</option>
            <option value="qwen2.5vl:3b">qwen2.5vl:3b</option>
          </select>
        </div>

        {/* Vision Toggle */}
        <div className="flex items-center bg-surface-main rounded border border-muted p-0.5 space-x-0.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setIsHighPrecision(false); fetch(`${API}/api/system/vision-mode?precision=false`, { method: 'POST' }); }}
            className={`h-6 px-2 py-0 text-[10px] font-jetbrains-mono rounded-sm ${!isHighPrecision ? 'bg-surface text-accent-teal border border-muted shadow-sm hover:bg-surface hover:text-accent-teal' : 'text-text-dim hover:text-on-surface hover:bg-transparent'}`}
          >
            Fast 3B
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setIsHighPrecision(true); fetch(`${API}/api/system/vision-mode?precision=true`, { method: 'POST' }); }}
            className={`h-6 px-2 py-0 text-[10px] font-jetbrains-mono rounded-sm ${isHighPrecision ? 'bg-surface text-accent-teal border border-muted shadow-sm hover:bg-surface hover:text-accent-teal' : 'text-text-dim hover:text-on-surface hover:bg-transparent'}`}
          >
            Precision 7B
          </Button>
        </div>

        {/* VRAM Purge */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => fetch(`${API}/api/system/unload`, { method: 'POST' }).then(() => fetch(`${API}/api/system/status`).then(r=>r.json()).then(d=>setSystemStatus(d)))}
          className="h-7 px-2 text-[10px] font-jetbrains-mono border-status-warning/50 text-status-warning hover:bg-status-warning/10 hover:text-status-warning bg-transparent"
        >
          <Zap size={11} className="mr-1" /> VRAM Purge
        </Button>
      </div>
    </div>
  );
}
