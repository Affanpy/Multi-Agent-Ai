import React, { useEffect, useState, useRef } from 'react';
import { useStore } from '../store';
import { useWebSocket } from '../hooks/useWebSocket';
import Sidebar from '../components/Sidebar';
import MessageBubble from '../components/MessageBubble';
import TypingIndicator from '../components/TypingIndicator';
import PrivateDrawer from '../components/PrivateDrawer';
import { AnimatePresence } from 'framer-motion';
import { Send, PlusCircle, X, Reply } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ChatRoom() {
  const { 
    currentSession, messages, isTyping, typingAgent, 
    createSession, clearSession, activePrivateAgent, 
    setActivePrivateAgent, agents, isModerating,
    replyTo, setReplyTo
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

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim() || status !== 'connected') return;
    sendMessage(input, false, null, replyTo?.agentId || null);
    setInput('');
    setReplyTo(null);
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
           
           <button 
              onClick={handleNewSession} 
              disabled={messages.length === 0}
              className="glass-button flex items-center gap-2 px-4 py-2 bg-indigo-500/20 text-indigo-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
           >
              <PlusCircle size={18} /> New Session
           </button>
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

          <form onSubmit={handleSend} className="flex gap-3 relative max-w-4xl mx-auto">
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
               disabled={status !== 'connected' || !input.trim() || isTyping || isModerating || activeAgentsCount === 0}
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
