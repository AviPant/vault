import React from 'react';
import { Activity, Server, Cpu, HardDrive, Wifi, Shield, Box } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

export default function Monitor({ systemStatus }) {
  if (!systemStatus) {
    return (
      <div className="flex-1 flex items-center justify-center h-full">
        <p className="text-text-dim flex items-center"><Activity className="animate-spin mr-2" size={16}/> Fetching telemetry...</p>
      </div>
    );
  }

  const isOnline = systemStatus.ollama_status === 'online';

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-surface h-full">
      <div className="h-14 border-b border-muted flex items-center justify-between px-6 flex-shrink-0">
        <div className="flex items-center space-x-2">
          <Activity size={16} className="text-accent-teal" />
          <h1 className="font-semibold text-on-surface">System Monitor</h1>
        </div>
        <Badge variant="outline" className={`font-jetbrains-mono ${isOnline ? 'text-status-success border-status-success/30 bg-status-success/10' : 'text-destructive border-destructive/30 bg-destructive/10'}`}>
          {isOnline ? 'SYSTEM ONLINE' : 'OLLAMA OFFLINE'}
        </Badge>
      </div>

      <ScrollArea className="flex-1 w-full min-h-0 p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <Card className="bg-surface-main border-muted">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center">
                  <Cpu size={16} className="text-accent-teal mr-2" /> Inference Engine
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <span className="text-[10px] font-jetbrains-mono text-text-dim block mb-1">Active Model</span>
                  <Badge className="bg-surface-raised text-on-surface hover:bg-surface-raised">{systemStatus.active_model}</Badge>
                </div>
                <div>
                  <span className="text-[10px] font-jetbrains-mono text-text-dim block mb-1">Vision Precision</span>
                  <Badge variant="outline" className="border-muted text-on-surface-variant capitalize">{systemStatus.vision_mode}</Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-surface-main border-muted">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center">
                  <HardDrive size={16} className="text-accent-teal mr-2" /> VRAM Allocation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-[10px] font-jetbrains-mono text-text-dim mb-1">
                    <span>Usage</span>
                    <span>Max: {systemStatus.vram_limit_gb} GB</span>
                  </div>
                  <div className="h-2 bg-surface-raised rounded-full overflow-hidden">
                    <div className={`h-full ${systemStatus.active_model !== "None (VRAM Free)" ? 'bg-accent-teal w-[85%]' : 'bg-text-dim w-0'}`} />
                  </div>
                  <p className="text-[10px] text-text-dim mt-2 leading-tight">
                    Strict VRAM caps enforced to prevent swapping. Model unloading required before switching contexts.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-surface-main border-muted border-dashed border-status-success/40">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center text-status-success">
                  <Shield size={16} className="mr-2" /> Network Security
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-3 mb-3">
                  <Wifi size={24} className="text-status-success opacity-50" />
                  <div>
                    <p className="text-xs font-semibold text-status-success">Air-Gapped Operation</p>
                    <p className="text-[10px] text-text-dim mt-0.5">Isolated from public internet</p>
                  </div>
                </div>
                <ul className="space-y-1 mt-4">
                  <li className="text-[10px] font-jetbrains-mono text-text-dim flex items-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-status-success mr-2"></div> Local Embedding (Nomic)
                  </li>
                  <li className="text-[10px] font-jetbrains-mono text-text-dim flex items-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-status-success mr-2"></div> Local Generation (Llama 3)
                  </li>
                  <li className="text-[10px] font-jetbrains-mono text-text-dim flex items-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-status-success mr-2"></div> No Telemetry Export
                  </li>
                </ul>
              </CardContent>
            </Card>

          </div>

          <Card className="bg-surface-main border-muted">
            <CardHeader>
              <CardTitle className="text-sm flex items-center">
                <Box size={16} className="text-text-dim mr-2" /> Local Model Registry
              </CardTitle>
              <CardDescription className="text-xs">Models available in the isolated Ollama instance.</CardDescription>
            </CardHeader>
            <CardContent>
              {systemStatus.available_models && systemStatus.available_models.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {systemStatus.available_models.map((m, i) => (
                    <div key={i} className="p-3 border border-muted bg-surface rounded-md flex items-center justify-center">
                      <span className="text-xs font-jetbrains-mono text-on-surface-variant truncate">{m}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-text-dim italic">No models found or engine offline.</p>
              )}
            </CardContent>
          </Card>

        </div>
      </ScrollArea>
    </div>
  );
}
