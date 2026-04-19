import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../store';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import { X, Send, Lock } from 'lucide-react';

export default function PrivateDrawer({ agent, onClose, sendMessage, status }) {
  const { messages, isTyping, typingAgent } = useStore();
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const endRef = useRef(null);

  // Filter ONLY private interaction with this specific agent
  const privateMessages = messages.filter(m =>
    m.is_private && m.target_agent_id === agent.id
  );

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [privateMessages, isTyping, isSending]);

  useEffect(() => {
    if (isTyping && typingAgent?.id === agent.id) {
      setIsSending(false);
    }
  }, [isTyping, typingAgent, agent.id]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim() || status !== 'connected') return;
    setIsSending(true);
    sendMessage(input, true, agent.id);
    setInput('');
  };

  return (
    <motion.div
      initial={{ x: "100%", opacity: 0 }}
      animate={{ 
        x: 0, 
        opacity: 1, 
        transition: { 
          x: { type: "tween", ease: "easeOut", duration: 0.5 },
          opacity: { type: "tween", duration: 0.15 }
        } 
      }}
      exit={{ 
        x: "100%", 
        opacity: 0, 
        transition: { 
          x: { type: "tween", ease: "easeIn", duration: 0.5 },
          opacity: { type: "tween", duration: 0.15 }
        } 
      }}
      className="pointer-events-auto absolute top-0 right-0 h-full w-full sm:max-w-[420px] bg-slate-900/95 backdrop-blur-xl border-l border-white/10 shadow-2xl flex flex-col"
    >
      <div className="p-4 border-b border-white/10 flex justify-between items-center bg-indigo-900/40">
        <div className="flex items-center gap-3">
          <div className="text-2xl drop-shadow-md">{agent.avatar_emoji}</div>
          <div>
            <h3 className="font-bold flex items-center gap-2 text-slate-100">
              Whispering {agent.name} <Lock size={14} className="text-emerald-400" />
            </h3>
            <p className="text-xs text-indigo-300">Jalur rahasia forum utama</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 text-slate-400 hover:text-white bg-white/5 rounded-lg hover:bg-rose-500/80 transition-colors">
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {privateMessages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center px-4">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-white/10">
              <Lock size={24} className="opacity-60" />
            </div>
            <p className="text-sm font-medium text-slate-400">Diskusi tatap muka 1-on-1</p>
            <p className="text-xs mt-2 opacity-60 max-w-[250px]">Konteks percakapan awal diingat, namun percakapan ini tidak akan lebur ke otak agen lain.</p>
          </div>
        )}

        {privateMessages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isSending && !isTyping && (
          <div className="flex items-center gap-3 p-3 bg-indigo-900/40 border border-indigo-500/30 rounded-xl max-w-[80%] animate-pulse">
            <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs font-semibold text-indigo-300 italic">Menyandikan pesan & mengirim...</span>
          </div>
        )}

        {isTyping && typingAgent?.id === agent.id && !privateMessages.some(m => m.isStreaming) && (
          <TypingIndicator name={typingAgent.name} emoji={typingAgent.emoji} />
        )}
        <div ref={endRef} />
      </div>

      <div className="p-4 border-t border-white/10 bg-black/40">
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Bisikkan misi spesifik..."
            className="flex-1 bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-500"
          />
          <button
            type="submit"
            disabled={status !== 'connected' || !input.trim() || isTyping || isSending}
            className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl px-4 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shadow-indigo-500/20"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </motion.div>
  );
}
