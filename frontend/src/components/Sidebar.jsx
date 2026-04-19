import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import { motion, AnimatePresence, Reorder, useDragControls } from 'framer-motion';
import { Users, StopCircle, MessageSquare, Settings, BrainCircuit, Power, Edit2, GripVertical } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Sidebar() {
  const { 
    agents, fetchAgents, isTyping, typingAgent, 
    setActivePrivateAgent, activePrivateAgent, 
    moderatorEnabled, toggleModerator,
    toggleAgentActive, reorderAgents
  } = useStore();
  const [hoveredAgent, setHoveredAgent] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const sortedAgents = [...agents].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  const handleReorder = (newOrder) => {
    reorderAgents(newOrder);
  };

  return (
    <div className="w-1/4 h-full glass-panel flex flex-col p-4 mr-4 hidden md:flex">
      {/* Pengaturan Cepat */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-3">
          <Settings size={18} className="text-amber-400" />
          <h2 className="text-sm font-semibold tracking-wide text-slate-300">Pengaturan Cepat</h2>
        </div>
        
        <div className="p-3 rounded-lg bg-white/5 border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BrainCircuit size={14} className={moderatorEnabled ? 'text-emerald-400' : 'text-slate-500'} />
              <span className="text-xs font-medium text-slate-300">AI Moderator</span>
            </div>
            <button 
              onClick={toggleModerator}
              className={`w-10 h-5 rounded-full relative transition-colors duration-300 ${
                moderatorEnabled ? 'bg-emerald-500' : 'bg-slate-600'
              }`}
            >
              <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-md transition-transform duration-300 ${
                moderatorEnabled ? 'translate-x-5' : 'translate-x-0'
              }`} />
            </button>
          </div>
          <p className="text-[10px] text-slate-500 leading-relaxed">
            {moderatorEnabled 
              ? 'Moderator AI aktif — memilih agen yang relevan untuk menjawab' 
              : 'Moderator OFF — semua agen menjawab berurutan'
            }
          </p>
        </div>
      </div>

      {/* Separator */}
      <div className="border-t border-white/5 mb-4" />

      {/* Agents Header */}
      <div className="flex items-center gap-2 mb-3">
        <Users className="text-indigo-400" size={18} />
        <h2 className="text-sm font-semibold tracking-wide text-slate-300">Agents</h2>
        <span className="ml-auto text-[10px] text-slate-500 bg-white/5 px-2 py-0.5 rounded-full">
          {agents.filter(a => a.is_active).length}/{agents.length}
        </span>
      </div>

      {/* Agent Cards with Drag & Drop */}
      <Reorder.Group 
        axis="y" 
        values={sortedAgents} 
        onReorder={handleReorder}
        className="flex-1 overflow-y-auto pr-1 space-y-2"
      >
        {sortedAgents.map(agent => (
          <AgentCard 
            key={agent.id} 
            agent={agent} 
            isTyping={isTyping}
            typingAgent={typingAgent}
            activePrivateAgent={activePrivateAgent}
            setActivePrivateAgent={setActivePrivateAgent}
            toggleAgentActive={toggleAgentActive}
            hoveredAgent={hoveredAgent}
            setHoveredAgent={setHoveredAgent}
            navigate={navigate}
          />
        ))}
      </Reorder.Group>
    </div>
  );
}

function AgentCard({ agent, isTyping, typingAgent, activePrivateAgent, setActivePrivateAgent, toggleAgentActive, hoveredAgent, setHoveredAgent, navigate }) {
  const controls = useDragControls();

  return (
    <Reorder.Item
      value={agent}
      dragListener={false}
      dragControls={controls}
      className={`rounded-lg border transition-colors overflow-hidden ${
        agent.is_active 
          ? 'bg-white/5 border-white/10 hover:bg-white/[0.07]' 
          : 'bg-white/[0.02] border-white/5 opacity-50'
      }`}
      whileDrag={{ scale: 1.02, boxShadow: "0 8px 30px rgba(99, 102, 241, 0.2)" }}
    >
      {/* Top Section: Grip + Info + Chat Button */}
      <div className="flex items-stretch">
        {/* Drag Handle — hanya area ini yang bisa di-drag */}
        <div 
          onPointerDown={(e) => controls.start(e)}
          className="flex items-center justify-center px-2 bg-white/[0.03] border-r border-white/5 cursor-grab active:cursor-grabbing touch-none hover:bg-white/[0.06] transition-colors"
        >
          <GripVertical size={14} className="text-slate-600" />
        </div>

              {/* Agent Info */}
              <div className="flex-1 p-3">
                <div className="flex items-center gap-2.5">
                  <span className="text-2xl">{agent.avatar_emoji}</span>
                  <div className="flex-1 min-w-0">
                    <h3 className={`font-bold text-sm leading-tight truncate ${agent.is_active ? 'text-slate-100' : 'text-slate-400'}`}>
                      {agent.name}
                    </h3>
                    <p className="text-[11px] text-indigo-400 font-semibold truncate">{agent.role}</p>
                  </div>
                </div>

                {/* Status */}
                <div className="mt-2">
                  {isTyping && typingAgent?.id === agent.id ? (
                    <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 animate-pulse">
                      <div className="w-2 h-2 rounded-full bg-emerald-400" />
                      Generating...
                    </div>
                  ) : (
                    <div className={`flex items-center gap-1.5 text-[10px] ${agent.is_active ? 'text-slate-500' : 'text-slate-600'}`}>
                      <div className={`w-2 h-2 rounded-full ${agent.is_active ? 'bg-slate-500' : 'bg-slate-700'}`} />
                      {agent.is_active ? 'Idle' : 'Nonaktif'}
                    </div>
                  )}
                </div>
              </div>

              {/* Chat Button (prominent, right side) */}
              <div className="flex items-center pr-3 relative">
                <button
                  onClick={(e) => { e.stopPropagation(); activePrivateAgent?.id === agent.id ? setActivePrivateAgent(null) : setActivePrivateAgent(agent); }}
                  onMouseEnter={() => setHoveredAgent(agent.id)}
                  onMouseLeave={() => setHoveredAgent(null)}
                  disabled={!agent.is_active}
                  className={`p-2.5 rounded-xl transition-all ${
                    activePrivateAgent?.id === agent.id 
                      ? 'bg-indigo-500/40 text-white ring-2 ring-indigo-400/50 shadow-lg shadow-indigo-500/20' 
                      : agent.is_active
                        ? 'bg-indigo-500/15 text-indigo-400 hover:bg-indigo-500/30 hover:shadow-lg hover:shadow-indigo-500/10'
                        : 'bg-white/5 text-slate-600 cursor-not-allowed'
                  }`}
                >
                  <MessageSquare size={20} />
                </button>

                <AnimatePresence>
                  {hoveredAgent === agent.id && agent.is_active && (
                    <motion.div
                      initial={{ opacity: 0, y: 5, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 5, scale: 0.9 }}
                      transition={{ type: "tween", duration: 0.15 }}
                      className="absolute right-0 top-full mt-2 z-50 pointer-events-none"
                    >
                      <div className="bg-slate-800/95 backdrop-blur-xl border border-indigo-500/30 rounded-lg px-3 py-2 shadow-xl shadow-indigo-500/10 whitespace-nowrap">
                        <p className="text-[10px] text-slate-400">
                          {activePrivateAgent?.id === agent.id ? 'Tutup chat pribadi' : `Chat pribadi dengan ${agent.name}`}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Bottom Section: Actions + Model */}
            <div className="flex items-center gap-2 px-3 py-2 border-t border-white/5 bg-white/[0.02]">
              {/* Power Toggle */}
              <button
                onClick={(e) => { e.stopPropagation(); toggleAgentActive(agent.id); }}
                className={`p-1.5 rounded-md transition-colors ${
                  agent.is_active 
                    ? 'text-emerald-400 hover:bg-emerald-500/20' 
                    : 'text-rose-400/60 hover:bg-rose-500/20'
                }`}
                title={agent.is_active ? 'Nonaktifkan agen' : 'Aktifkan agen'}
              >
                <Power size={14} />
              </button>

              {/* Edit */}
              <button
                onClick={(e) => { e.stopPropagation(); navigate('/agents', { state: { editId: agent.id } }); }}
                className="p-1.5 rounded-md text-slate-400 hover:bg-white/10 hover:text-indigo-300 transition-colors"
                title="Edit agen"
              >
                <Edit2 size={14} />
              </button>

              {/* Model Name */}
              <span className="ml-auto text-[10px] text-slate-500 font-mono truncate max-w-[60%]">
                {agent.model}
              </span>
        </div>
      </Reorder.Item>
  );
}
