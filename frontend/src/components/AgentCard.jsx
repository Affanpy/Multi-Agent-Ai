import React, { useState } from 'react';
import { Trash2, Edit2, Eye, EyeOff } from 'lucide-react';
import { useStore } from '../store';

export default function AgentCard({ agent, onEdit }) {
  const { deleteAgent } = useStore();
  const [showKey, setShowKey] = useState(false);

  return (
    <div className="glass-panel p-5 flex flex-col gap-4 relative overflow-hidden group">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500 opacity-75" />
      
      <div className="flex justify-between items-start">
        <div className="flex gap-3 items-center">
            <div className="text-4xl bg-white/5 p-3 rounded-xl border border-white/10 shadow-inner">
                {agent.avatar_emoji}
            </div>
            <div>
                <h3 className="text-xl font-bold text-white tracking-wide">{agent.name}</h3>
                <p className="text-sm text-indigo-300 font-semibold">{agent.role}</p>
            </div>
        </div>
        <div className="flex gap-2 opacity-50 group-hover:opacity-100 transition-opacity">
            <button onClick={() => onEdit(agent)} className="p-2 hover:bg-indigo-500/20 text-indigo-300 rounded-lg transition-colors"><Edit2 size={16}/></button>
            <button onClick={() => deleteAgent(agent.id)} className="p-2 hover:bg-rose-500/20 text-rose-400 rounded-lg transition-colors"><Trash2 size={16}/></button>
        </div>
      </div>

      <div className="mt-2 flex-1">
        <p className="text-sm text-slate-300 line-clamp-2 italic">"{agent.soul}"</p>
      </div>
      
      <div className="mt-4 pt-4 border-t border-white/10 flex flex-col gap-2 text-xs text-slate-400">
        <div className="flex justify-between">
            <span className="uppercase font-bold tracking-wider">{agent.provider}</span>
            <span>{agent.model}</span>
        </div>
        <div className="flex justify-between items-center bg-black/20 p-2 rounded">
            <span className="font-mono">{showKey ? agent.api_key_encrypted || '*********' : '••••••••••••••••'}</span>
            <button onClick={() => setShowKey(!showKey)} className="text-slate-500 hover:text-slate-300">
                {showKey ? <EyeOff size={14}/> : <Eye size={14}/>}
            </button>
        </div>
      </div>
    </div>
  );
}
