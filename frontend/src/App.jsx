import { useState, useEffect, useRef, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import ReactMarkdown from 'react-markdown';
import {
  Upload, MessageSquare, FileText, Trash2, Plus,
  Send, ChevronRight, Loader2, CheckCircle, AlertCircle,
  BookOpen, Cpu, Database
} from 'lucide-react';
import { documentsAPI, sessionsAPI, chatAPI } from './api/client';

// ─── STATUS BADGE ────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const styles = {
    ready: 'bg-green-100 text-green-700',
    processing: 'bg-yellow-100 text-yellow-700',
    error: 'bg-red-100 text-red-700',
  };
  const icons = {
    ready: <CheckCircle size={12} />,
    processing: <Loader2 size={12} className="animate-spin" />,
    error: <AlertCircle size={12} />,
  };
  return (
    <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${styles[status] || 'bg-gray-100 text-gray-600'}`}>
      {icons[status]} {status}
    </span>
  );
}

// ─── DOCUMENT PANEL ──────────────────────────────────────────────────────────
function DocumentPanel({ documents, selectedDocs, onToggleDoc, onUpload, onDelete, uploading }) {
  const onDrop = useCallback((acceptedFiles) => {
    acceptedFiles.forEach(file => onUpload(file));
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  });

  const fmt = (bytes) => bytes > 1024 * 1024
    ? `${(bytes / 1024 / 1024).toFixed(1)} MB`
    : `${(bytes / 1024).toFixed(0)} KB`;

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <h2 className="font-semibold text-gray-800 flex items-center gap-2">
          <BookOpen size={16} /> Documents
        </h2>
        <p className="text-xs text-gray-500 mt-1">Select which PDFs to query</p>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`m-3 border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="flex items-center justify-center gap-2 text-blue-600">
            <Loader2 size={16} className="animate-spin" />
            <span className="text-sm">Uploading...</span>
          </div>
        ) : (
          <>
            <Upload size={20} className="mx-auto mb-1 text-gray-400" />
            <p className="text-xs text-gray-500">Drop PDFs here or click to upload</p>
          </>
        )}
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-2">
        {documents.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            <FileText size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">No documents yet</p>
          </div>
        )}
        {documents.map(doc => (
          <div
            key={doc.id}
            className={`border rounded-lg p-3 cursor-pointer transition-all
              ${selectedDocs.includes(doc.id)
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'}`}
            onClick={() => doc.status === 'ready' && onToggleDoc(doc.id)}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-800 truncate">{doc.filename}</p>
                <p className="text-xs text-gray-400">{fmt(doc.file_size)} • {doc.page_count || '?'} pages</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(doc.id); }}
                className="text-gray-300 hover:text-red-400 transition-colors flex-shrink-0"
              >
                <Trash2 size={13} />
              </button>
            </div>
            <div className="mt-1.5">
              <StatusBadge status={doc.status} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── MESSAGE BUBBLE ───────────────────────────────────────────────────────────
function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center mr-2 flex-shrink-0 mt-1">
          <Cpu size={14} className="text-white" />
        </div>
      )}
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        isUser
          ? 'bg-blue-600 text-white rounded-br-sm'
          : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm'
      }`}>
        {isUser ? (
          <p className="text-sm">{message.content}</p>
        ) : (
          <div className="text-sm prose prose-sm max-w-none prose-p:my-1 prose-headings:my-2">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-400 mb-1">Sources:</p>
            {message.sources.map((s, i) => (
              <span key={i} className="inline-block text-xs bg-blue-50 text-blue-600 rounded px-2 py-0.5 mr-1 mb-1">
                {s.source}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [documents, setDocuments] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const messagesEndRef = useRef(null);

  // Load data on mount
  useEffect(() => {
    loadDocuments();
    loadSessions();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Poll processing docs
  useEffect(() => {
    const processing = documents.filter(d => d.status === 'processing');
    if (processing.length === 0) return;
    const interval = setInterval(loadDocuments, 3000);
    return () => clearInterval(interval);
  }, [documents]);

  const loadDocuments = async () => {
    try {
      const { data } = await documentsAPI.list();
      setDocuments(data);
    } catch (e) { console.error(e); }
  };

  const loadSessions = async () => {
    try {
      const { data } = await sessionsAPI.list();
      setSessions(data);
    } catch (e) { console.error(e); }
  };

  const loadMessages = async (sessionId) => {
    try {
      const { data } = await chatAPI.history(sessionId);
      setMessages(data);
    } catch (e) { console.error(e); }
  };

  const handleUpload = async (file) => {
    setUploading(true);
    try {
      await documentsAPI.upload(file);
      await loadDocuments();
    } catch (e) {
      alert('Upload failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (id) => {
    if (!confirm('Delete this document?')) return;
    await documentsAPI.delete(id);
    setSelectedDocs(prev => prev.filter(d => d !== id));
    await loadDocuments();
  };

  const handleNewSession = async () => {
    const { data } = await sessionsAPI.create('New Chat');
    setSessions(prev => [data, ...prev]);
    setCurrentSession(data);
    setMessages([]);
  };

  const handleSelectSession = async (session) => {
    setCurrentSession(session);
    await loadMessages(session.id);
  };

  const handleToggleDoc = (docId) => {
    setSelectedDocs(prev =>
      prev.includes(docId) ? prev.filter(d => d !== docId) : [...prev, docId]
    );
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    if (!currentSession) {
      const { data } = await sessionsAPI.create(input.slice(0, 40));
      setSessions(prev => [data, ...prev]);
      setCurrentSession(data);
      await sendMessage(data.id, input.trim());
    } else {
      await sendMessage(currentSession.id, input.trim());
    }
  };

  const sendMessage = async (sessionId, text) => {
    const userMsg = { id: Date.now(), role: 'user', content: text, sources: [] };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const docIds = selectedDocs.length > 0 ? selectedDocs : null;
      const { data } = await chatAPI.send(sessionId, text, docIds);

      const assistantMsg = {
        id: data.message_id,
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e) {
      const errMsg = {
        id: Date.now(),
        role: 'assistant',
        content: `⚠️ Error: ${e.response?.data?.detail || 'Failed to get response. Check your API keys.'}`,
        sources: [],
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 font-sans">

      {/* Left Sidebar: Sessions */}
      <div className="w-56 bg-gray-900 text-white flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center gap-2 mb-1">
            <Database size={16} className="text-blue-400" />
            <span className="font-bold text-sm">PDF RAG Chat</span>
          </div>
          <p className="text-xs text-gray-400">Chat with your documents</p>
        </div>

        <button
          onClick={handleNewSession}
          className="m-3 flex items-center gap-2 bg-blue-600 hover:bg-blue-700 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
        >
          <Plus size={14} /> New Chat
        </button>

        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => handleSelectSession(s)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm mb-1 transition-colors flex items-center gap-2
                ${currentSession?.id === s.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700'}`}
            >
              <MessageSquare size={13} className="flex-shrink-0" />
              <span className="truncate">{s.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Middle: Documents */}
      <div className="w-64 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col">
        <DocumentPanel
          documents={documents}
          selectedDocs={selectedDocs}
          onToggleDoc={handleToggleDoc}
          onUpload={handleUpload}
          onDelete={handleDeleteDoc}
          uploading={uploading}
        />
      </div>

      {/* Right: Chat */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="font-semibold text-gray-800">
              {currentSession?.title || 'Start a conversation'}
            </h1>
            <p className="text-xs text-gray-400">
              {selectedDocs.length > 0
                ? `Querying ${selectedDocs.length} selected document(s)`
                : `Querying all ${documents.filter(d => d.status === 'ready').length} ready documents`}
            </p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <MessageSquare size={28} className="text-blue-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-700 mb-2">Ask anything about your PDFs</h2>
              <p className="text-sm text-gray-400 max-w-sm">
                Upload PDFs in the panel on the left, then ask questions. The AI will find relevant sections and cite its sources.
              </p>
            </div>
          )}

          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {loading && (
            <div className="flex justify-start mb-4">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center mr-2">
                <Cpu size={14} className="text-white" />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question about your documents... (Enter to send)"
              rows={1}
              className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl p-3 transition-colors"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
