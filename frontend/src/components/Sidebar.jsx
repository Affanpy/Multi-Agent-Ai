import React, { useEffect } from 'react';
import { useStore } from '../store';
import { Users, StopCircle } from 'lucide-react';

export default function Sidebar() {
  const { agents, fetchAgents, isTyping, typingAgent } = useStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const activeAgents = agents.filter(a => a.is_active);

  return (
    <div className="w-1/4 h-full glass-panel flex flex-col p-4 mr-4 hidden md:flex">
      <div className="flex items-center gap-2 mb-6">
        <Users className="text-indigo-400" />
        <h2 className="text-xl font-semibold tracking-wide">Active Agents</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-2 space-y-3">
        {activeAgents.length === 0 ? (
          <p className="text-slate-400 text-sm">No active agents.</p>
        ) : (
          activeAgents.map(agent => (
            <div key={agent.id} className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
              <div className="flex items-start gap-3">
                <div className="text-2xl mt-1">{agent.avatar_emoji}</div>
                <div className="flex-1">
                  <h3 className="font-medium text-slate-100">{agent.name}</h3>
                  <p className="text-xs text-indigo-300 font-semibold mb-1">{agent.role}</p>
                  
                  {isTyping && typingAgent?.id === agent.id ? (
                     <div className="flex items-center gap-2 text-xs text-emerald-400 mt-2 animate-pulse">
                        <div className="w-2 h-2 rounded-full bg-emerald-400" />
                        Generating...
                     </div>
                  ) : (
                     <div className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                        <StopCircle size={10} /> Idle
                     </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
