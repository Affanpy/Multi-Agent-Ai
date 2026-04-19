import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../store';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const { agents } = useStore();
  
  const agent = isUser ? null : agents.find(a => a.id === message.agent_id);

  const [displayedContent, setDisplayedContent] = useState(message.isStreaming ? '' : message.content);
  const bufferRef = useRef(message.content);

  useEffect(() => {
    bufferRef.current = message.content;
  }, [message.content]);

  useEffect(() => {
    if (!message.isStreaming && bufferRef.current.length === displayedContent.length) {
       return; // Sejarah statis tidak butuh loop interval
    }
    
    let localInterval;
    localInterval = setInterval(() => {
      setDisplayedContent((current) => {
        const target = bufferRef.current;
        if (current.length < target.length) {
          // Dinamis catch-up step untuk mencegah macet jika token melimpah
          let step = 1; // Kembali ke ultra-smooth character mode (1 char per tick)
          const gap = target.length - current.length;
          if (gap > 20) step = 3;
          if (gap > 60) step = 8;
          
          // Fase Draining: Tuntaskan mulus dengan ngebut sedikit
          if (!message.isStreaming) step = Math.max(step, Math.ceil(gap / 3)); 
          
          return current + target.substring(current.length, current.length + step);
        } else if (!message.isStreaming) {
          clearInterval(localInterval);
        }
        return current;
      });
    }, 20); // 20ms (50 FPS) sangat ringan dan memberikan sensasi mengalir yang jauh lebih memanjakan

    return () => clearInterval(localInterval);
  }, [message.isStreaming]);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`max-w-[80%] md:max-w-[70%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        {!isUser && agent && (
          <div className="flex items-center gap-2 mb-1 px-1">
            <span className="text-lg">{agent.avatar_emoji}</span>
            <span className="text-sm font-semibold text-indigo-300">{agent.name}</span>
            <span className="text-xs text-slate-400">— {agent.role}</span>
          </div>
        )}
        
        <div className={`p-4 rounded-xl shadow-lg ${
          isUser 
            ? 'bg-indigo-600 text-white rounded-tr-none' 
            : 'bg-white/10 backdrop-blur-md border border-white/10 text-slate-100 rounded-tl-none'
        }`}>
          <div className="whitespace-pre-wrap text-sm leading-relaxed font-sans">
            {displayedContent}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-emerald-400 animate-pulse align-middle" />
            )}
          </div>
        </div>
        
        <div className="text-[10px] text-slate-500 mt-1 px-1 flex items-center gap-2">
            {!isUser && agent && <span className="uppercase text-xs font-bold tracking-wider">{agent.model}</span>}
            <span>{message.timestamp ? new Date(message.timestamp.endsWith('Z') ? message.timestamp : message.timestamp + 'Z').toLocaleTimeString() : ''}</span>
        </div>
      </div>
    </motion.div>
  );
}
