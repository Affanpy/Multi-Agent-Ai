import React from 'react';
import { useStore } from '../store';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const { agents } = useStore();
  
  const agent = isUser ? null : agents.find(a => a.id === message.agent_id);
  
  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6 animate-fade-in`}>
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
            {message.content}
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
    </div>
  );
}
