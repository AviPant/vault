import React, { useState, useRef, useEffect } from 'react';
import { Shield, FileText, Cpu, Eye, Lock, Upload, X, Zap, RefreshCw, WifiOff } from 'lucide-react';

import VaultLogo from './VaultLogo';
import Login from '@/components/auth/Login';
import Sidebar from '@/components/layout/Sidebar';
import TopBar from '@/components/layout/TopBar';
import RightSidebar from '@/components/layout/RightSidebar';
import ChatFeed from '@/components/chat/ChatFeed';
import ChatInput from '@/components/chat/ChatInput';
import KnowledgeBase from '@/components/views/KnowledgeBase';
import Monitor from '@/components/views/Monitor';

const API = 'http://localhost:8000';
const PAGES = { WORKSPACE: 'workspace', KNOWLEDGE: 'knowledge', MONITOR: 'monitor' };

export default function App() {
  // ─── Authentication State ───
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // ─── Core State ───
  const [activePage, setActivePage] = useState(PAGES.WORKSPACE);
  const [isHighPrecision, setIsHighPrecision] = useState(false);
  const [selectedModel, setSelectedModel] = useState('agent');
  const [prompt, setPrompt] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [attachedImage, setAttachedImage] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentActivity, setAgentActivity] = useState([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('vault-theme') || 'shadcn-black');

  // ─── Chat History State ───
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [conversationsLoading, setConversationsLoading] = useState(false);

  // ─── Knowledge Base / Files State ───
  const [outputFiles, setOutputFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const kbFileInputRef = useRef(null);

  const ollamaOnline = systemStatus?.ollama_status === 'online';

  // ─── Theme Management ───
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('vault-theme', theme);
  }, [theme]);

  // ─── Auto-scroll chat ───
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // ─── Fetch system status periodically ───
  useEffect(() => {
    if (!isAuthenticated) return;
    const fetchStatus = () => {
      fetch(`${API}/api/system/status`)
        .then(r => r.json())
        .then(data => setSystemStatus(data))
        .catch(() => setSystemStatus(prev => prev ? { ...prev, ollama_status: 'offline' } : { ollama_status: 'offline', active_model: 'None (VRAM Free)' }));
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  // ─── Load conversations on mount ───
  useEffect(() => {
    if (isAuthenticated) loadConversations();
  }, [isAuthenticated]);

  const loadConversations = async () => {
    try {
      setConversationsLoading(true);
      const res = await fetch(`${API}/api/history/conversations`);
      const data = await res.json();
      setConversations(data);
    } catch (e) {
      console.error('Failed to load conversations:', e);
    } finally {
      setConversationsLoading(false);
    }
  };

  const loadConversation = async (id) => {
    try {
      const res = await fetch(`${API}/api/history/conversations/${id}`);
      const data = await res.json();
      setActiveConversationId(id);
      setChatHistory(data.messages || []);
      setAgentActivity([]);
      setActivePage(PAGES.WORKSPACE);
    } catch (e) {
      console.error('Failed to load conversation:', e);
    }
  };

  const startNewChat = async () => {
    try {
      const res = await fetch(`${API}/api/history/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      setActiveConversationId(data.id);
      setChatHistory([]);
      setAgentActivity([]);
      setPrompt('');
      setAttachedImage(null);
      setActivePage(PAGES.WORKSPACE);
      loadConversations();
    } catch (e) {
      console.error('Failed to create conversation:', e);
    }
  };

  const deleteConversation = async (id, e) => {
    e.stopPropagation();
    try {
      await fetch(`${API}/api/history/conversations/${id}`, { method: 'DELETE' });
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setChatHistory([]);
        setAgentActivity([]);
      }
      loadConversations();
    } catch (e) {
      console.error('Failed to delete conversation:', e);
    }
  };

  const saveMessage = async (convId, msg) => {
    try {
      await fetch(`${API}/api/history/conversations/${convId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: msg.role,
          content: msg.content || '',
          image: msg.image || null,
          steps: msg.steps || null,
        })
      });
    } catch (e) {
      console.error('Failed to save message:', e);
    }
  };

  // ─── Image Upload ───
  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setAttachedImage(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && (file.type.startsWith('image/') || file.type === 'application/pdf')) {
      const reader = new FileReader();
      reader.onloadend = () => setAttachedImage(reader.result);
      reader.readAsDataURL(file);
    }
  };

  // ─── Download a file ───
  const downloadFile = async (filename) => {
    try {
      const res = await fetch(`${API}/api/files/download/${filename}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Download failed:', e);
    }
  };

  // ─── Send Message (SSE Streaming) ───
  const handleSend = async () => {
    if (!prompt.trim() && !attachedImage) return;
    if (!ollamaOnline) return;

    let convId = activeConversationId;
    if (!convId) {
      try {
        const res = await fetch(`${API}/api/history/conversations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        });
        const data = await res.json();
        convId = data.id;
        setActiveConversationId(convId);
      } catch (e) {
        console.error('Failed to create conversation:', e);
        return;
      }
    }

    const userMessage = { role: 'user', content: prompt, image: attachedImage };
    setChatHistory(prev => [...prev, userMessage]);
    await saveMessage(convId, userMessage);

    const currentPrompt = prompt;
    setPrompt('');
    setAttachedImage(null);
    setIsStreaming(true);
    setAgentActivity([]);
    setChatHistory(prev => [...prev, { role: 'agent', content: '', steps: [] }]);

    const startTime = new Date().toLocaleTimeString('en-US', { hour12: false });
    setAgentActivity([{ time: startTime, text: 'Task received — processing request', status: 'success' }]);

    let imagesPayload = [];
    if (attachedImage) {
      imagesPayload = [attachedImage.split(',')[1]];
    }

    let finalAgentMsg = { role: 'agent', content: '', steps: [] };

    try {
      const response = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: currentPrompt,
          use_agent: selectedModel === 'agent',
          model: selectedModel !== 'agent' ? selectedModel : undefined,
          high_precision: isHighPrecision,
          stream: true,
          images: imagesPayload.length > 0 ? imagesPayload : undefined
        })
      });

      if (!response.body) throw new Error('ReadableStream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.replace('data: ', '').trim();
              if (!dataStr) continue;

              try {
                const data = JSON.parse(dataStr);
                const now = new Date().toLocaleTimeString('en-US', { hour12: false });

                setChatHistory(prev => {
                  const newHistory = [...prev];
                  const lastMsg = { ...newHistory[newHistory.length - 1] };
                  lastMsg.steps = lastMsg.steps ? [...lastMsg.steps] : [];

                  if (data.token) {
                    lastMsg.content += data.token;
                    finalAgentMsg.content += data.token;
                  } else if (data.status) {
                    const step = { type: 'status', text: data.status, time: now };
                    lastMsg.steps.push(step);
                    finalAgentMsg.steps.push(step);
                  } else if (data.file_generated) {
                    const step = { type: 'file', filepath: data.file_generated, time: now };
                    lastMsg.steps.push(step);
                    finalAgentMsg.steps.push(step);
                  } else if (data.error) {
                    const step = { type: 'error', text: data.error, time: now };
                    lastMsg.steps.push(step);
                    finalAgentMsg.steps.push(step);
                  }

                  newHistory[newHistory.length - 1] = lastMsg;
                  return newHistory;
                });
              } catch (e) {
                console.warn('SSE parse error:', e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      finalAgentMsg.content += '\n\n**Error:** Could not connect to the engine.';
      setChatHistory(prev => {
        const newHistory = [...prev];
        const lastMsg = { ...newHistory[newHistory.length - 1] };
        lastMsg.content += '\n\n**Error:** Could not connect to the engine.';
        newHistory[newHistory.length - 1] = lastMsg;
        return newHistory;
      });
    } finally {
      setIsStreaming(false);
      await saveMessage(convId, finalAgentMsg);
      loadConversations();
    }
  };

  // Helper for parsing JSON chunks from response (if any)
  const extractInfo = (text) => {
    const match = text.match(/```json\n([\s\S]*?)\n```/);
    if (!match) return null;
    try {
      const data = JSON.parse(match[1]);
      return Object.entries(data).map(([key, value]) => ({
        label: key.replace(/_/g, ' '),
        value: value,
        color: value === 'Critical' || value === 'Fail' ? 'text-status-warning' : (value === 'Pass' || value === 'Normal' ? 'text-status-success' : 'text-on-surface')
      }));
    } catch (e) {
      return null;
    }
  };

  const renderOllamaBanner = () => {
    if (systemStatus && !ollamaOnline) {
      return (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 flex items-center space-x-3 mb-4 mx-auto max-w-3xl w-full">
          <WifiOff size={18} className="text-red-400 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-300">Ollama is offline</p>
            <p className="text-xs text-red-400/70">Run <code className="bg-red-500/20 px-1 rounded text-red-300">ollama serve</code> in a terminal to start AI inference.</p>
          </div>
          <button
            onClick={() => fetch(`${API}/api/system/status`).then(r => r.json()).then(d => setSystemStatus(d)).catch(() => {})}
            className="px-2 py-1 text-xs border border-red-500/30 text-red-400 rounded hover:bg-red-500/10 transition-colors"
          >
            <RefreshCw size={12} className="inline mr-1" />Retry
          </button>
        </div>
      );
    }
    return null;
  };

  if (!isAuthenticated) {
    return <Login onLogin={setIsAuthenticated} />;
  }

  return (
    <div className="flex h-screen bg-surface-main text-on-surface overflow-hidden">
      <Sidebar 
        sidebarCollapsed={sidebarCollapsed}
        setSidebarCollapsed={setSidebarCollapsed}
        activePage={activePage}
        setActivePage={setActivePage}
        startNewChat={startNewChat}
        conversationsLoading={conversationsLoading}
        conversations={conversations}
        loadConversation={loadConversation}
        activeConversationId={activeConversationId}
        deleteConversation={deleteConversation}
        ollamaOnline={ollamaOnline}
        PAGES={PAGES}
      />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Main Content Area */}
        {activePage === PAGES.WORKSPACE && (
          <div className="flex-1 flex flex-col min-w-0">
            <TopBar 
              theme={theme}
              setTheme={setTheme}
              selectedModel={selectedModel}
              setSelectedModel={setSelectedModel}
              isHighPrecision={isHighPrecision}
              setIsHighPrecision={setIsHighPrecision}
              systemStatus={systemStatus}
              setSystemStatus={setSystemStatus}
              API={API}
            />
            
            {chatHistory.length === 0 ? (
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {renderOllamaBanner()}
                <div className="max-w-3xl mx-auto space-y-6 mt-8">
                  <div>
                    <h2 className="text-xl font-semibold text-on-surface mb-1">Sovereign AI Workbench</h2>
                    <p className="text-sm text-text-dim">Document analysis and code execution, fully local and auditable.</p>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { icon: <FileText size={18} />, label: 'Draft Approval Note', prompt: 'Draft an approval note for pipe replacement in Unit 42' },
                      { icon: <Cpu size={18} />, label: 'Calculate Burst Pressure', prompt: 'Calculate burst pressure using Barlows Formula for S=35000 PSI, D=12.75 in, t=0.25 in' },
                      { icon: <Eye size={18} />, label: 'Analyze P&ID Diagram', prompt: 'Analyze the attached P&ID diagram for anomalies' },
                    ].map((action, i) => (
                      <button key={i} onClick={() => setPrompt(action.prompt)}
                        className="bg-surface border border-muted rounded-lg p-4 text-left hover:border-accent-teal/50 transition-colors group">
                        <div className="text-text-dim group-hover:text-accent-teal transition-colors mb-2">{action.icon}</div>
                        <p className="text-xs font-medium text-on-surface">{action.label}</p>
                      </button>
                    ))}
                  </div>

                  <div className="bg-surface border border-muted rounded-lg p-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-jetbrains-mono uppercase text-text-dim tracking-wider">Task Input</span>
                      <span className="text-[10px] font-jetbrains-mono text-status-success flex items-center">
                        <Lock size={10} className="mr-1" /> FULLY LOCAL
                      </span>
                    </div>

                    <div>
                      <h3 className="text-base font-medium text-on-surface mb-1">What should V.A.U.L.T. work on?</h3>
                      <p className="text-xs text-text-dim">Your prompt and files stay inside the MRPL network.</p>
                    </div>

                    <div>
                      <label className="text-xs text-text-dim mb-1.5 block font-jetbrains-mono">DESCRIBE THE TASK</label>
                      <textarea
                        className="w-full bg-surface-main border border-muted rounded-md p-3 text-sm text-on-surface placeholder-text-dim focus:border-accent-teal focus:ring-1 focus:ring-accent-teal resize-none min-h-[100px]"
                        placeholder="E.g., Inspect the attached P&ID schematic for Line 14-P-201..."
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                      />
                    </div>

                    <div
                      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-md p-4 flex items-center justify-center cursor-pointer transition-colors ${
                        dragOver ? 'border-accent-teal bg-accent-teal/5' : 'border-muted hover:border-accent-teal/50'
                      }`}
                    >
                      <input ref={fileInputRef} type="file" className="hidden" accept="image/*,.pdf" onChange={handleImageUpload} />
                      {attachedImage ? (
                        <div className="flex items-center space-x-3">
                          <img src={attachedImage} alt="Preview" className="h-12 w-12 object-cover rounded border border-muted" />
                          <span className="text-xs text-on-surface-variant">Image attached</span>
                          <button onClick={(e) => { e.stopPropagation(); setAttachedImage(null); }} className="text-text-dim hover:text-status-warning">
                            <X size={14} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2 text-text-dim">
                          <Upload size={16} />
                          <span className="text-xs">Attach a PDF or Image</span>
                          <span className="text-[10px] text-text-dim/50">Drop file here or browse</span>
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end">
                      <button
                        onClick={handleSend}
                        disabled={isStreaming || (!prompt.trim() && !attachedImage) || !ollamaOnline}
                        className="px-6 py-2 bg-accent-teal text-surface-main font-semibold text-sm rounded-md hover:bg-[#38debb] disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center"
                        title={!ollamaOnline ? 'Ollama is offline — cannot run tasks' : ''}
                      >
                        <Zap size={14} className="mr-2" />Run Task
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <>
                <div className="w-full flex justify-center mt-6 z-10 px-6">
                  {renderOllamaBanner()}
                </div>
                <ChatFeed 
                  chatHistory={chatHistory} 
                  isStreaming={isStreaming} 
                  downloadFile={downloadFile} 
                  chatEndRef={chatEndRef}
                  extractInfo={extractInfo}
                />
                <ChatInput 
                  prompt={prompt}
                  setPrompt={setPrompt}
                  handleSend={handleSend}
                  isStreaming={isStreaming}
                  ollamaOnline={ollamaOnline}
                  dragOver={dragOver}
                  setDragOver={setDragOver}
                  handleDrop={handleDrop}
                  attachedImage={attachedImage}
                  setAttachedImage={setAttachedImage}
                  handleImageUpload={handleImageUpload}
                />
              </>
            )}
          </div>
        )}
        
        {/* Right Sidebar for Telemetry (Rendered only on Workspace) */}
        {activePage === PAGES.WORKSPACE && (
          <RightSidebar 
            systemStatus={systemStatus} 
            collapsed={rightSidebarCollapsed} 
            setCollapsed={setRightSidebarCollapsed} 
          />
        )}

        {/* Knowledge Base Page */}
        {activePage === PAGES.KNOWLEDGE && (
          <KnowledgeBase API={API} />
        )}

        {/* Monitor Page */}
        {activePage === PAGES.MONITOR && (
          <Monitor systemStatus={systemStatus} />
        )}
      </div>
    </div>
  );
}
