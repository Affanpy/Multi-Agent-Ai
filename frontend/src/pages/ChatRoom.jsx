import React, { useEffect, useState, useRef } from 'react';
import { useStore } from '../store';
import { useWebSocket } from '../hooks/useWebSocket';
import Sidebar from '../components/Sidebar';
import MessageBubble from '../components/MessageBubble';
import TypingIndicator from '../components/TypingIndicator';
import PrivateDrawer from '../components/PrivateDrawer';
import { AnimatePresence } from 'framer-motion';
import { Send, PlusCircle, X, Reply, FileText, Loader2, Paperclip, Image as ImageIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ChatRoom() {
  const { 
    currentSession, messages, isTyping, typingAgent, 
    createSession, clearSession, activePrivateAgent, 
    setActivePrivateAgent, agents, isModerating,
    replyTo, setReplyTo, generateSummary, isSummarizing,
    pendingFile, isUploading, uploadFile, clearPendingFile
  } = useStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!currentSession) {
      createSession();
    }
  }, [currentSession, createSession]);
  
  const { status, sendMessage, toastEvent } = useWebSocket(currentSession?.id);

  const publicMessages = messages.filter(m => !m.is_private);
  const activeAgentsCount = agents.filter(a => a.is_active).length;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [publicMessages, isTyping]);

  const fileInputRef = useRef(null);

  const handleSend = (e) => {
    e.preventDefault();
    if ((!input.trim() && !pendingFile) || status !== 'connected') return;
    sendMessage(input, false, null, replyTo?.agentId || null, pendingFile?.file_id || null);
    setInput('');
    setReplyTo(null);
    clearPendingFile();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    uploadFile(file);
    e.target.value = ''; // Reset input
  };

  const handleNewSession = async () => {
     clearSession();
     await createSession();
  };

  return (
    <div className="h-full w-full p-4 md:p-6 flex overflow-hidden relative">
      <Sidebar />
      <div className="flex-1 glass-panel flex flex-col overflow-hidden relative">
        {/* Private Whisper Overlay Drawer — wrapper statis agar tidak mengganggu flex layout */}
        <div className="absolute inset-0 pointer-events-none z-50 overflow-hidden">
          <AnimatePresence>
            {activePrivateAgent && (
               <PrivateDrawer 
                  agent={activePrivateAgent} 
                  onClose={() => setActivePrivateAgent(null)} 
                  sendMessage={sendMessage} 
                  status={status} 
               />
            )}
          </AnimatePresence>
        </div>
        
        {toastEvent && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-indigo-600/90 backdrop-blur-md px-5 py-2 rounded-full text-sm font-medium z-10 animate-fade-in shadow-xl shadow-indigo-500/20 border border-indigo-400">
            {toastEvent}
          </div>
        )}
        
        {/* Header */}
        <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5">
           <div>
              <h2 className="text-xl font-semibold">
                {currentSession ? currentSession.title : 'Loading Session...'}
              </h2>
              <span className="text-xs text-slate-400">
                WebSocket: <span className={status === 'connected' ? 'text-emerald-400' : 'text-rose-400'}>{status}</span>
              </span>
           </div>
           
           <div className="flex items-center gap-2">
             <button 
                onClick={generateSummary}
                disabled={publicMessages.length < 2 || isSummarizing || isTyping}
                className="glass-button flex items-center gap-2 px-4 py-2 bg-amber-500/20 text-amber-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-amber-500/30 transition-colors"
             >
               {isSummarizing ? <Loader2 size={18} className="animate-spin" /> : <FileText size={18} />}
               {isSummarizing ? 'Merangkum...' : 'Rangkum'}
             </button>
             <button 
                onClick={handleNewSession} 
                disabled={messages.length === 0}
                className="glass-button flex items-center gap-2 px-4 py-2 bg-indigo-500/20 text-indigo-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
             >
                <PlusCircle size={18} /> New Session
             </button>
           </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2">
           {publicMessages.length === 0 && (
             <div className="h-full flex flex-col items-center justify-center text-slate-500">
               <div className="text-6xl mb-4">💬</div>
               <p className="text-lg">Mulai forum diskusi publik...</p>
             </div>
           )}
           
           {publicMessages.map(msg => (
             <MessageBubble key={msg.id} message={msg} />
           ))}

           {isModerating && (
             <div className="flex items-center gap-4 p-4 glass-panel bg-indigo-900/10 max-w-[90%] md:max-w-[70%] border border-indigo-500/20">
               <div className="flex gap-1.5">
                 <div className="w-2 h-2 bg-indigo-400/80 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                 <div className="w-2 h-2 bg-indigo-400/80 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                 <div className="w-2 h-2 bg-indigo-400/80 rounded-full animate-bounce"></div>
               </div>
               <span className="text-sm font-medium text-indigo-300/80 italic">Moderator sedang merancang giliran diskusi...</span>
             </div>
           )}
           
           {isTyping && typingAgent && !messages.some(m => m.isStreaming && m.agent_id === typingAgent.id) && (
             <TypingIndicator name={typingAgent.name} emoji={typingAgent.emoji} />
           )}
           <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white/5 border-t border-white/10 relative z-20">
          {/* Reply Preview Bar */}
          {replyTo && (
            <div className="flex items-center gap-3 mb-3 max-w-4xl mx-auto bg-indigo-900/30 border border-indigo-500/20 rounded-lg px-4 py-2">
              <Reply size={14} className="text-indigo-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-indigo-300">Membalas {replyTo.agentEmoji} {replyTo.agentName}</p>
                <p className="text-[10px] text-slate-400 truncate">{replyTo.snippet}...</p>
              </div>
              <button 
                onClick={() => setReplyTo(null)} 
                className="p-1 text-slate-400 hover:text-white hover:bg-white/10 rounded transition-colors flex-shrink-0"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {/* Pending File Preview Bar */}
          {pendingFile && (
            <div className="flex items-center gap-3 mb-3 max-w-4xl mx-auto bg-slate-800/80 border border-slate-600/50 rounded-lg p-2">
              <div className="w-10 h-10 rounded bg-black/30 flex items-center justify-center overflow-hidden flex-shrink-0 border border-white/5">
                {pendingFile.is_image && pendingFile.localPreview ? (
                  <img src={pendingFile.localPreview} alt="preview" className="w-full h-full object-cover" />
                ) : pendingFile.is_document ? (
                  <FileText size={20} className="text-emerald-400" />
                ) : (
                  <ImageIcon size={20} className="text-blue-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">{pendingFile.filename}</p>
                <p className="text-[10px] text-slate-400 truncate">
                  {pendingFile.is_image ? 'Gambar disisipkan' : pendingFile.has_extracted_text ? 'Teks dokumen diekstrak' : 'File disisipkan'}
                </p>
              </div>
              <button 
                onClick={clearPendingFile} 
                className="p-1 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded transition-colors flex-shrink-0"
              >
                <X size={14} />
              </button>
            </div>
          )}

          <form onSubmit={handleSend} className="flex gap-3 relative max-w-4xl mx-auto">
             <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                className="hidden" 
                accept="image/png, image/jpeg, image/webp, image/gif, application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, text/plain"
             />
             <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={activeAgentsCount === 0 || status !== 'connected' || isUploading}
                className={`glass-button bg-white/5 hover:bg-white/10 text-slate-300 p-4 rounded-xl flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed ${isUploading ? 'animate-pulse text-indigo-400' : ''}`}
             >
                {isUploading ? <Loader2 size={20} className="animate-spin" /> : <Paperclip size={20} />}
             </button>
             
             <input 
               type="text" 
               value={input}
               onChange={(e) => setInput(e.target.value)}
               disabled={activeAgentsCount === 0 || status !== 'connected'}
               placeholder={replyTo 
                  ? `Balas ke ${replyTo.agentName}...`
                  : activeAgentsCount === 0 
                     ? "⚠️ Tidak ada agen aktif. Hidupkan agen di menu Agents terlebih dahulu..." 
                     : "Type a message to start the brain trust..."}
               className="flex-1 bg-black/20 border border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
             />
              <button 
               type="submit" 
               disabled={status !== 'connected' || (!input.trim() && !pendingFile) || isTyping || isModerating || activeAgentsCount === 0 || isUploading}
               className="glass-button bg-indigo-600 hover:bg-indigo-500 text-white p-4 rounded-xl flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
             >
               <Send size={20} />
             </button>
          </form>
        </div>
      </div>
    </div>
  );
}
