import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, StopCircle, MessageSquare } from 'lucide-react';

export default function Sidebar() {
  const { agents, fetchAgents, isTyping, typingAgent, setActivePrivateAgent, activePrivateAgent } = useStore();
  const [hoveredAgent, setHoveredAgent] = useState(null);

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
            <div key={agent.id} className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors group relative">
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

              <div className="absolute top-3 right-3">
                <button
                  onClick={() => activePrivateAgent?.id === agent.id ? setActivePrivateAgent(null) : setActivePrivateAgent(agent)}
                  onMouseEnter={() => setHoveredAgent(agent.id)}
                  onMouseLeave={() => setHoveredAgent(null)}
                  className={`p-2 rounded-lg transition-colors relative ${
                    activePrivateAgent?.id === agent.id 
                      ? 'bg-indigo-500/50 text-white ring-2 ring-indigo-400/50' 
                      : 'bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/40'
                  }`}
                >
                  <MessageSquare size={16} />
                </button>

                <AnimatePresence>
                  {hoveredAgent === agent.id && (
                    <motion.div
                      initial={{ opacity: 0, y: 5, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 5, scale: 0.9 }}
                      transition={{ type: "tween", duration: 0.15 }}
                      className="absolute right-0 top-full mt-2 z-50 pointer-events-none"
                    >
                      <div className="bg-slate-800/95 backdrop-blur-xl border border-indigo-500/30 rounded-lg px-3 py-2 shadow-xl shadow-indigo-500/10 whitespace-nowrap">
                        <p className="text-[10px] text-slate-400 mt-0.5">
                          {activePrivateAgent?.id === agent.id ? 'Tutup chat pribadi' : `Chat pribadi dengan ${agent.name}`}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
