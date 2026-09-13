import React from 'react';
import { HardDrive, Server, Database, Cpu, Activity, ShieldCheck, PanelRight, PanelRightClose } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export default function RightSidebar({ systemStatus, collapsed, setCollapsed }) {
  if (!systemStatus) return null;

  return (
    <aside className={`${collapsed ? 'w-16' : 'w-64'} bg-surface border-l border-muted flex-shrink-0 flex flex-col transition-all duration-300`}>
      <div className={`h-14 flex items-center ${collapsed ? 'justify-center' : 'justify-between px-4'} border-b border-muted`}>
        {!collapsed && (
          <div className="flex items-center">
            <Activity size={14} className="text-accent-teal mr-2" />
            <h2 className="text-xs font-semibold text-on-surface uppercase tracking-wider font-jetbrains-mono">Telemetry</h2>
          </div>
        )}
        <Button variant="ghost" size="icon" className="h-8 w-8 text-text-dim hover:text-on-surface" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? <PanelRight size={16} /> : <PanelRightClose size={16} />}
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Hardware Status */}
        {collapsed ? (
          <div className="flex flex-col items-center space-y-4">
            <div className="p-2 bg-surface-main rounded-md border border-muted" title="Hardware Node">
              <Server size={16} className="text-text-dim" />
            </div>
            <div className={`p-2 rounded-md ${systemStatus.active_model !== "None (VRAM Free)" ? 'bg-accent-teal/10 text-accent-teal' : 'bg-surface-main border border-muted text-text-dim'}`} title={`Active Model: ${systemStatus.active_model}`}>
              <Cpu size={16} />
            </div>
            <div className="p-2 bg-surface-main rounded-md border border-muted" title={`Vector Store: ${systemStatus.knowledge_base_docs} Docs`}>
              <Database size={16} className="text-text-dim" />
            </div>
            <div className="p-2 bg-status-success/10 rounded-md" title="Local Network Only">
              <ShieldCheck size={16} className="text-status-success" />
            </div>
          </div>
        ) :
          <>
            <Card className="bg-surface-main border-muted">
              <CardHeader className="p-3 pb-1">
                <CardTitle className="text-[10px] font-jetbrains-mono text-text-dim uppercase flex items-center">
                  <Server size={12} className="mr-1.5" /> Hardware Node
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 pt-2 space-y-3">
                <div>
                  <div className="flex justify-between text-[10px] font-jetbrains-mono text-on-surface-variant mb-1">
                    <span>GPU</span>
                    <span className="text-accent-teal">{systemStatus.active_model !== "None (VRAM Free)" ? 'Active' : 'Idle'}</span>
                  </div>
                  <div className="h-1.5 bg-surface-raised rounded-full overflow-hidden">
                    <div
                      className={`h-full ${systemStatus.active_model !== "None (VRAM Free)" ? 'bg-accent-teal w-[85%]' : 'bg-text-dim w-[5%]'}`}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-jetbrains-mono text-text-dim flex items-center">
                    <HardDrive size={10} className="mr-1.5" /> VRAM Limit
                  </span>
                  <span className="text-[10px] font-jetbrains-mono text-on-surface">{systemStatus.vram_limit_gb} GB</span>
                </div>
              </CardContent>
            </Card>

            {/* Model Status */}
            <Card className="bg-surface-main border-muted">
              <CardHeader className="p-3 pb-1">
                <CardTitle className="text-[10px] font-jetbrains-mono text-text-dim uppercase flex items-center">
                  <Cpu size={12} className="mr-1.5" /> Active Model
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 pt-2">
                <Badge variant="outline" className={`w-full justify-center text-[10px] font-jetbrains-mono font-normal ${systemStatus.active_model !== "None (VRAM Free)" ? 'border-accent-teal/50 text-accent-teal bg-accent-teal/5' : 'border-muted text-text-dim'}`}>
                  {systemStatus.active_model}
                </Badge>
              </CardContent>
            </Card>

            {/* Knowledge Base */}
            <Card className="bg-surface-main border-muted">
              <CardHeader className="p-3 pb-1">
                <CardTitle className="text-[10px] font-jetbrains-mono text-text-dim uppercase flex items-center">
                  <Database size={12} className="mr-1.5" /> Vector Store
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 pt-2 flex justify-between items-center">
                <span className="text-[10px] font-jetbrains-mono text-text-dim">Indexed Docs</span>
                <span className="text-[11px] font-jetbrains-mono font-bold text-on-surface bg-surface-raised px-2 py-0.5 rounded">
                  {systemStatus.knowledge_base_docs}
                </span>
              </CardContent>
            </Card>

            {/* Security / Network */}
            <Card className="bg-surface-main border-muted border-dashed border-status-success/30">
              <CardContent className="p-3 flex items-center space-x-3">
                <div className="p-1.5 bg-status-success/10 rounded-md">
                  <ShieldCheck size={16} className="text-status-success" />
                </div>
                <div>
                  <p className="text-[10px] font-jetbrains-mono text-status-success uppercase font-semibold">Local Network</p>
                  <p className="text-[9px] text-text-dim leading-tight mt-0.5">Zero external API calls</p>
                </div>
              </CardContent>
            </Card>
          </>
        }
      </div>
    </aside>
  );
}
