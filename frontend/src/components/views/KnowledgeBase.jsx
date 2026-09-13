import React, { useState, useEffect, useRef } from 'react';
import { Database, FileText, Download, Trash2, HardDrive, RefreshCw, UploadCloud, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';

export default function KnowledgeBase({ API }) {
  const [uploads, setUploads] = useState([]);
  const [outputs, setOutputs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState('uploads'); // 'uploads' or 'outputs'

  const fileInputRef = useRef(null);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const [uplRes, outRes] = await Promise.all([
        fetch(`${API}/api/files/uploads`),
        fetch(`${API}/api/files/outputs`)
      ]);
      if (uplRes.ok) setUploads(await uplRes.json());
      if (outRes.ok) setOutputs(await outRes.json());
    } catch (e) {
      console.error('Failed to fetch files', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [API]);

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${API}/api/files/upload`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        await fetchFiles(); // Refresh lists immediately on success
      }
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (filename, type) => {
    try {
      const endpoint = type === 'upload' ? 'uploads' : 'outputs';
      await fetch(`${API}/api/files/${endpoint}/${filename}`, { method: 'DELETE' });
      fetchFiles();
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  const handleDownload = async (filename) => {
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
      console.error('Download failed', e);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const renderFileList = (files, type) => {
    if (files.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-48 text-text-dim">
          <HardDrive size={32} className="mb-3 opacity-20" />
          <p className="text-sm font-jetbrains-mono uppercase tracking-widest">No files found</p>
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {files.map((file, idx) => (
          <div key={idx} className="flex items-center justify-between p-3 bg-surface-main border border-muted rounded-lg hover:border-accent-teal/50 transition-colors group">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="p-2 bg-surface-raised rounded text-accent-teal">
                <FileText size={16} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-on-surface truncate">{file.filename}</p>
                <div className="flex items-center space-x-2 mt-0.5">
                  <Badge variant="outline" className="text-[9px] font-jetbrains-mono px-1 py-0 border-muted text-text-dim h-4">
                    {(file.type || 'FILE').toUpperCase().replace('.', '')}
                  </Badge>
                  <span className="text-[10px] text-text-dim">{formatBytes(file.size_bytes)}</span>
                  <span className="text-[10px] text-text-dim/50">•</span>
                  <span className="text-[10px] text-text-dim">{new Date(file.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
              {type === 'output' && (
                <Button variant="ghost" size="icon" className="h-8 w-8 text-accent-teal hover:text-accent-teal hover:bg-accent-teal/10" onClick={() => handleDownload(file.filename)}>
                  <Download size={14} />
                </Button>
              )}
              <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10" onClick={() => handleDelete(file.filename, type)}>
                <Trash2 size={14} />
              </Button>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-surface h-full">
      <div className="h-14 border-b border-muted flex items-center justify-between px-6 flex-shrink-0">
        <div className="flex items-center space-x-2">
          <Database size={16} className="text-accent-teal" />
          <h1 className="font-semibold text-on-surface">Knowledge Base</h1>
        </div>
        <Button variant="outline" size="sm" className="h-7 text-xs border-muted text-text-dim hover:text-on-surface" onClick={fetchFiles}>
          <RefreshCw size={12} className={`mr-1.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      <div className="p-6 flex flex-col flex-1 min-h-0">
        <div className="grid grid-cols-2 gap-4 mb-6 flex-shrink-0">
          <Card
            className={`cursor-pointer transition-all duration-200 ${activeTab === 'uploads' ? 'bg-surface-raised border-accent-teal ring-1 ring-accent-teal/20' : 'bg-surface-main border-muted hover:border-accent-teal/50'}`}
            onClick={() => setActiveTab('uploads')}
          >
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-xs font-jetbrains-mono text-text-dim uppercase flex items-center">
                Uploaded Sources
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 flex justify-between items-end">
              <span className="text-2xl font-bold text-on-surface">{uploads.length}</span>
              <span className="text-[10px] font-jetbrains-mono text-text-dim">Vector Indexed</span>
            </CardContent>
          </Card>

          <Card
            className={`cursor-pointer transition-all duration-200 ${activeTab === 'outputs' ? 'bg-surface-raised border-accent-teal ring-1 ring-accent-teal/20' : 'bg-surface-main border-muted hover:border-accent-teal/50'}`}
            onClick={() => setActiveTab('outputs')}
          >
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-xs font-jetbrains-mono text-text-dim uppercase flex items-center">
                Generated Outputs
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 flex justify-between items-end">
              <span className="text-2xl font-bold text-on-surface">{outputs.length}</span>
              <span className="text-[10px] font-jetbrains-mono text-text-dim">Ready for Download</span>
            </CardContent>
          </Card>
        </div>

        {/* Upload Dropzone (Only visible when the 'Uploaded Sources' tab is active) */}
        {activeTab === 'uploads' && (
          <div
            className="mb-4 border-2 border-dashed border-muted rounded-xl bg-surface-main/30 hover:bg-surface-main p-6 flex flex-col items-center justify-center cursor-pointer hover:border-accent-teal transition-all group shrink-0"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".pdf,.txt,.md"
              onChange={handleFileUpload}
            />
            {isUploading ? (
              <Loader2 className="w-8 h-8 text-accent-teal animate-spin mb-3" />
            ) : (
              <UploadCloud className="w-8 h-8 text-text-dim group-hover:text-accent-teal transition-colors mb-3" />
            )}
            <span className="text-sm font-medium text-on-surface">
              {isUploading ? "Uploading Document..." : "Click to upload SOPs or Manuals"}
            </span>
            <span className="text-xs text-text-dim mt-1 font-jetbrains-mono">Accepts .PDF, .TXT, .MD</span>
          </div>
        )}

        <ScrollArea className="flex-1 w-full min-h-0 rounded-md border border-muted bg-surface-main/30">
          <div className="p-4">
            <h3 className="text-xs font-jetbrains-mono uppercase text-text-dim mb-4 tracking-wider">
              {activeTab === 'uploads' ? 'Document Contexts' : 'Agent Work Products'}
            </h3>
            {renderFileList(activeTab === 'uploads' ? uploads : outputs, activeTab === 'uploads' ? 'upload' : 'output')}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}