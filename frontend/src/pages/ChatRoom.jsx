import React, { useEffect, useState, useRef } from 'react';
import { useStore } from '../store';
import { useWebSocket } from '../hooks/useWebSocket';
import Sidebar from '../components/Sidebar';
import MessageBubble from '../components/MessageBubble';
import TypingIndicator from '../components/TypingIndicator';
import { Send, PlusCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ChatRoom() {
  const { currentSession, messages, isTyping, typingAgent, createSession, clearSession } = useStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!currentSession) {
      createSession();
    }
  }, [currentSession, createSession]);
  
  const { status, sendMessage, toastEvent } = useWebSocket(currentSession?.id);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim() || status !== 'connected') return;
    sendMessage(input);
    setInput('');
  };

  const handleNewSession = async () => {
     clearSession();
     await createSession();
  };

  return (
    <div className="h-full w-full p-4 md:p-6 flex overflow-hidden">
      <Sidebar />
      <div className="flex-1 glass-panel flex flex-col overflow-hidden relative">
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
           
           <button onClick={handleNewSession} className="glass-button flex items-center gap-2 px-4 py-2 bg-indigo-500/20 text-indigo-300 rounded-lg">
              <PlusCircle size={18} /> New Session
           </button>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2">
           {messages.length === 0 && (
             <div className="h-full flex flex-col items-center justify-center text-slate-500">
               <div className="text-6xl mb-4">💬</div>
               <p className="text-lg">Start the conversation...</p>
             </div>
           )}
           
           {messages.map(msg => (
             <MessageBubble key={msg.id} message={msg} />
           ))}
           
           {isTyping && typingAgent && (
             <TypingIndicator name={typingAgent.name} emoji={typingAgent.emoji} />
           )}
           <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white/5 border-t border-white/10 relative z-20">
          <form onSubmit={handleSend} className="flex gap-3 relative max-w-4xl mx-auto">
             <input 
               type="text" 
               value={input}
               onChange={(e) => setInput(e.target.value)}
               placeholder="Type a message to start the brain trust..."
               className="flex-1 bg-black/20 border border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-500"
             />
             <button 
               type="submit" 
               disabled={status !== 'connected' || !input.trim() || isTyping}
               className="glass-button bg-indigo-600 hover:bg-indigo-500 text-white p-4 rounded-xl flex items-center justify-center disabled:opacity-50"
             >
               <Send size={20} />
             </button>
          </form>
        </div>
      </div>
    </div>
  );
}
