import React from 'react';
import { Terminal, BookOpen, Eye, Loader2, MessageSquare, Trash2, Wifi, WifiOff, Lock, PanelLeft, PanelLeftClose, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import VaultLogo from '../../VaultLogo';

export default function Sidebar({
  sidebarCollapsed,
  setSidebarCollapsed,
  activePage,
  setActivePage,
  startNewChat,
  conversationsLoading,
  conversations,
  loadConversation,
  activeConversationId,
  deleteConversation,
  ollamaOnline,
  PAGES
}) {
  const SidebarItem = ({ icon, label, sublabel, active, collapsed, onClick }) => (
    <Button
      variant="ghost"
      className={`w-full justify-start h-auto py-2.5 px-3 mb-1 ${active ? 'bg-accent-teal/10 hover:bg-accent-teal/20 text-accent-teal' : 'text-text-dim hover:text-on-surface hover:bg-surface-main/50'}`}
      onClick={onClick}
    >
      <div className={`flex items-center w-full ${collapsed ? 'justify-center' : ''}`}>
        <div className={active ? 'text-accent-teal' : 'text-text-dim'}>{icon}</div>
        {!collapsed && (
          <div className="ml-3 text-left">
            <p className={`text-xs font-medium leading-none ${active ? 'text-accent-teal' : 'text-on-surface'}`}>{label}</p>
            <p className="text-[10px] text-text-dim mt-1 font-jetbrains-mono tracking-tight">{sublabel}</p>
          </div>
        )}
      </div>
    </Button>
  );

  return (
    <aside className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-surface flex-shrink-0 border-r border-muted flex flex-col transition-all duration-300`}>
      {/* Logo + Collapse Toggle */}
      <div className="h-16 flex items-center justify-between px-3 border-b border-muted">
        <div className="flex items-center">
          <VaultLogo className="text-accent-teal flex-shrink-0" size={24} />
          {!sidebarCollapsed && (
            <div className="ml-2.5">
              <h1 className="font-bold text-sm leading-tight tracking-tight text-on-surface">V.A.U.L.T.</h1>
              <p className="text-[7px] uppercase font-jetbrains-mono text-accent-teal tracking-[0.2em]">SOVEREIGN AI</p>
            </div>
          )}
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8 text-text-dim hover:text-on-surface" onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
          {sidebarCollapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
        </Button>
      </div>

      {/* Nav Items */}
      <nav className="p-2 space-y-1">
        <SidebarItem icon={<Terminal size={18} />} label="Workspace" sublabel="Execute tasks"
          active={activePage === PAGES.WORKSPACE} collapsed={sidebarCollapsed}
          onClick={() => setActivePage(PAGES.WORKSPACE)} />
        <SidebarItem icon={<BookOpen size={18} />} label="Knowledge Base" sublabel="Documents & RAG"
          active={activePage === PAGES.KNOWLEDGE} collapsed={sidebarCollapsed}
          onClick={() => setActivePage(PAGES.KNOWLEDGE)} />
        <SidebarItem icon={<Eye size={18} />} label="Monitor" sublabel="System health"
          active={activePage === PAGES.MONITOR} collapsed={sidebarCollapsed}
          onClick={() => setActivePage(PAGES.MONITOR)} />
      </nav>

      {/* Conversation History */}
      {!sidebarCollapsed && activePage === PAGES.WORKSPACE && (
        <div className="flex-1 flex flex-col overflow-hidden border-t border-muted">
          <div className="px-3 py-2 flex items-center justify-between">
            <span className="text-[10px] font-jetbrains-mono text-text-dim uppercase tracking-wider">History</span>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-text-dim hover:text-accent-teal" onClick={startNewChat} title="New Chat">
              <Plus size={14} />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
            {conversationsLoading ? (
              <div className="text-center py-4">
                <Loader2 size={16} className="text-text-dim animate-spin mx-auto" />
              </div>
            ) : conversations.length === 0 ? (
              <p className="text-[10px] text-text-dim/50 text-center py-4 px-2">No conversations yet</p>
            ) : (
              conversations.map(conv => (
                <button
                  key={conv.id}
                  onClick={() => loadConversation(conv.id)}
                  className={`w-full flex items-center justify-between px-2.5 py-2 rounded text-left group transition-colors ${
                    activeConversationId === conv.id
                      ? 'bg-accent-teal/10 text-accent-teal'
                      : 'text-text-dim hover:text-on-surface hover:bg-surface-main/50'
                  }`}
                >
                  <div className="flex items-center space-x-2 min-w-0 flex-1">
                    <MessageSquare size={12} className="flex-shrink-0" />
                    <span className="text-xs truncate">{conv.title}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => deleteConversation(conv.id, e)}
                    className="h-5 w-5 opacity-0 group-hover:opacity-100 p-0 text-text-dim hover:text-destructive hover:bg-destructive/10 transition-all flex-shrink-0"
                  >
                    <Trash2 size={11} />
                  </Button>
                </button>
              ))
            )}
          </div>
        </div>
      )}

      {/* Status Badges */}
      <div className="p-3 border-t border-muted space-y-2 flex flex-col items-center">
        {!sidebarCollapsed ? (
          <>
            <Badge variant="outline" className={`w-full justify-center text-[10px] font-jetbrains-mono tracking-wider ${ollamaOnline ? 'border-status-success/30 text-status-success bg-status-success/5' : 'border-red-400/30 text-red-400 bg-red-400/5'}`}>
              {ollamaOnline ? <Wifi size={10} className="mr-1.5" /> : <WifiOff size={10} className="mr-1.5" />}
              {ollamaOnline ? 'Ollama Online' : 'Ollama Offline'}
            </Badge>
            <Badge variant="outline" className="w-full justify-center text-[10px] font-jetbrains-mono text-status-info border-status-info/30 bg-status-info/5 uppercase tracking-wider">
              <Lock size={10} className="mr-1.5" /> Air-Gapped
            </Badge>
          </>
        ) : (
          <>
            <div className={`p-1.5 rounded-full ${ollamaOnline ? 'bg-status-success/10 text-status-success' : 'bg-red-400/10 text-red-400'}`}>
              {ollamaOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
            </div>
            <div className="p-1.5 rounded-full bg-status-info/10 text-status-info">
              <Lock size={14} />
            </div>
          </>
        )}
      </div>
    </aside>
  );
}
