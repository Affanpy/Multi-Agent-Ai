import React, { useState, useEffect, useRef } from 'react';
import { useStore } from '../store';
import { useWebSocket } from '../hooks/useWebSocket';
import MessageBubble from '../components/MessageBubble';
import TypingIndicator from '../components/TypingIndicator';
import { Play, Square, Settings, Users, Sword, Plus, X, Shield, ShieldAlert, Send } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function DebateArena() {
  const { 
    currentSession, createSession, clearSession, messages, 
    agents, isTyping, typingAgent
  } = useStore();

  const [topic, setTopic] = useState('');
  const [rounds, setRounds] = useState(3);
  const [selectedAgents, setSelectedAgents] = useState([]); // [{id, stance}]
  
  const [isDebating, setIsDebating] = useState(false);
  const [setupMode, setSetupMode] = useState(true);
  const [input, setInput] = useState('');
  
  const messagesEndRef = useRef(null);

  // Paksa ke session baru jika masuk page ini (asumsi debat adalah sesi baru, atau kita pakai session saat ini)
  useEffect(() => {
    if (!currentSession) {
      createSession();
    }
  }, [currentSession, createSession]);

  const { status, sendMessage, sendCommand, toastEvent } = useWebSocket(currentSession?.id);

  const publicMessages = messages.filter(m => !m.is_private);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [publicMessages, isTyping]);

  // Pantau jika ada pesan system debat selesai
  useEffect(() => {
    const lastMsg = messages[messages.length - 1];
    if (lastMsg?.role === 'system' && (lastMsg.content.includes('Selesai!') || lastMsg.content.includes('dihentikan'))) {
       setIsDebating(false);
    }
  }, [messages]);

  const toggleAgentSelection = (agentId) => {
    const exists = selectedAgents.find(a => a.id === agentId);
    if (exists) {
      setSelectedAgents(selectedAgents.filter(a => a.id !== agentId));
    } else {
      if (selectedAgents.length < 4) {
        setSelectedAgents([...selectedAgents, { id: agentId, stance: 'bebas' }]);
      }
    }
  };

  const updateAgentStance = (agentId, stance) => {
    setSelectedAgents(selectedAgents.map(a => 
      a.id === agentId ? { ...a, stance } : a
    ));
  };

  const startDebate = () => {
    if (!topic.trim()) {
      alert("Topik debat tidak boleh kosong!");
      return;
    }
    if (selectedAgents.length < 2) {
      alert("Pilih minimal 2 agen untuk berdebat!");
      return;
    }
    
    setIsDebating(true);
    setSetupMode(false);
    
    sendCommand({
      type: "start_debate",
      topic: topic,
      max_rounds: parseInt(rounds),
      agents_config: selectedAgents.map(a => ({
          agent_id: a.id,
          stance: a.stance
      }))
    });
  };

  const stopDebate = () => {
     sendCommand({ type: "stop_debate" });
     setIsDebating(false);
  };

  const handleInterrupt = (e) => {
      e.preventDefault();
      if (!input.trim() || status !== 'connected') return;
      // Kirim interupsi sebagai chat biasa
      sendMessage(input);
      setInput('');
  };

  const handleNewDebate = () => {
      clearSession();
      createSession();
      setSetupMode(true);
      setIsDebating(false);
  };

  return (
    <div className="flex flex-col h-full relative overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-indigo-950/20 to-slate-900">
      
      {/* Header */}
      <div className="p-4 border-b border-indigo-500/20 flex justify-between items-center bg-indigo-950/30 backdrop-blur-md relative z-20">
         <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-rose-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-rose-500/20">
              <Sword size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-rose-200 to-indigo-200">
                AI Debate Arena
              </h2>
              <span className="text-xs text-indigo-300">
                {status === 'connected' ? '🟢 Arena Live' : '🔴 Disconnected'}
              </span>
            </div>
         </div>
         
         <div className="flex items-center gap-2">
           {!setupMode && (
             <button 
                onClick={() => setSetupMode(true)} 
                className="glass-button flex items-center gap-2 px-4 py-2 bg-white/5 text-slate-300 rounded-lg"
             >
                <Settings size={16} /> Setup
             </button>
           )}
           <button 
              onClick={handleNewDebate} 
              className="glass-button flex items-center gap-2 px-4 py-2 bg-indigo-500/20 text-indigo-300 rounded-lg"
           >
              <Plus size={16} /> Debat Baru
           </button>
         </div>
      </div>

      <div className="flex-1 overflow-hidden relative flex flex-col md:flex-row">
        
        {/* Setup Sidebar (Kiri) - Hanya muncul jika setup mode */}
        <AnimatePresence>
          {setupMode && (
            <motion.div 
              initial={{ x: -400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -400, opacity: 0 }}
              className="w-full md:w-80 bg-slate-900/80 border-r border-indigo-500/20 p-5 overflow-y-auto z-10 shadow-2xl flex flex-col"
            >
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2 text-rose-200">
                <Settings size={18} /> Pengaturan Debat
              </h3>
              
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Topik Perdebatan</label>
                  <textarea 
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Contoh: Apakah AI akan merebut pekerjaan manusia?"
                    className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-sm focus:border-indigo-500 focus:outline-none min-h-[80px]"
                    disabled={isDebating}
                  />
                </div>
                
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Jumlah Ronde</label>
                  <input 
                    type="number" 
                    min="1" max="10"
                    value={rounds}
                    onChange={(e) => setRounds(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-sm focus:border-indigo-500 focus:outline-none"
                    disabled={isDebating}
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Partisipan (Maks 4)</label>
                    <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full">{selectedAgents.length}/4</span>
                  </div>
                  
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
                    {agents.map(agent => {
                      const isSelected = selectedAgents.find(a => a.id === agent.id);
                      return (
                        <div 
                          key={agent.id}
                          className={`p-3 rounded-xl border transition-all ${
                            isSelected 
                              ? 'bg-indigo-900/30 border-indigo-500/50' 
                              : 'bg-white/5 border-transparent hover:bg-white/10'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2 cursor-pointer" onClick={() => !isDebating && toggleAgentSelection(agent.id)}>
                            <div className="flex items-center gap-2">
                              <span className="text-xl">{agent.avatar_emoji}</span>
                              <div>
                                <div className="text-sm font-semibold text-white">{agent.name}</div>
                                <div className="text-[10px] text-slate-400">{agent.role}</div>
                              </div>
                            </div>
                            <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${isSelected ? 'bg-indigo-500 border-indigo-400' : 'border-slate-600'}`}>
                              {isSelected && <div className="w-2 h-2 bg-white rounded-full"></div>}
                            </div>
                          </div>
                          
                          {isSelected && !isDebating && (
                            <div className="flex gap-1 mt-2 pt-2 border-t border-white/10">
                              <button 
                                onClick={() => updateAgentStance(agent.id, 'pro')}
                                className={`flex-1 text-[10px] py-1 rounded transition-colors ${isSelected.stance === 'pro' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-black/30 text-slate-400 hover:bg-black/50'}`}
                              >
                                PRO
                              </button>
                              <button 
                                onClick={() => updateAgentStance(agent.id, 'kontra')}
                                className={`flex-1 text-[10px] py-1 rounded transition-colors ${isSelected.stance === 'kontra' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-black/30 text-slate-400 hover:bg-black/50'}`}
                              >
                                KONTRA
                              </button>
                              <button 
                                onClick={() => updateAgentStance(agent.id, 'bebas')}
                                className={`flex-1 text-[10px] py-1 rounded transition-colors ${isSelected.stance === 'bebas' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-black/30 text-slate-400 hover:bg-black/50'}`}
                              >
                                BEBAS
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
              
              <div className="mt-auto pt-6">
                {!isDebating ? (
                  <button 
                    onClick={startDebate}
                    className="w-full bg-gradient-to-r from-rose-600 to-indigo-600 hover:from-rose-500 hover:to-indigo-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-rose-500/20 transition-all flex items-center justify-center gap-2"
                  >
                    <Play size={18} fill="currentColor" /> Mulai Pertarungan
                  </button>
                ) : (
                  <button 
                    onClick={stopDebate}
                    className="w-full bg-rose-600 hover:bg-rose-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-rose-500/20 transition-all flex items-center justify-center gap-2"
                  >
                    <Square size={18} fill="currentColor" /> Hentikan Debat
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat / Arena Area (Kanan) */}
        <div className="flex-1 flex flex-col relative z-0 h-full">
           
           {/* Visualisasi Arena Latar Belakang */}
           <div className="absolute inset-0 opacity-10 pointer-events-none flex items-center justify-center">
             <Sword size={400} />
           </div>

           <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2 relative z-10">
              {publicMessages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-slate-500">
                  <div className="text-6xl mb-4 opacity-50">⚔️</div>
                  <p className="text-lg text-slate-400 text-center max-w-md">
                    {setupMode ? 'Atur topik dan partisipan di panel kiri, lalu klik "Mulai Pertarungan" untuk melihat AI berdebat!' : 'Menunggu debat dimulai...'}
                  </p>
                </div>
              )}
              
              <AnimatePresence initial={false}>
                {publicMessages.map((msg, idx) => (
                  <MessageBubble key={msg.id || idx} message={msg} />
                ))}
              </AnimatePresence>
              
              {isTyping && typingAgent && !messages.some(m => m.isStreaming && m.agent_id === typingAgent.id) && (
                <div className="flex w-full justify-start mb-6">
                   <div className="flex items-center gap-2 bg-indigo-900/30 border border-indigo-500/30 px-4 py-2 rounded-full">
                     <span className="text-lg">{typingAgent.emoji}</span>
                     <span className="text-sm font-semibold text-indigo-300">{typingAgent.name} sedang menyusun argumen</span>
                     <div className="flex gap-1 ml-2">
                       <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                       <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                       <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></div>
                     </div>
                   </div>
                </div>
              )}
              <div ref={messagesEndRef} />
           </div>

           {/* Input Interupsi */}
           {(isDebating || publicMessages.length > 0) && (
             <div className="p-4 bg-slate-900/80 border-t border-indigo-500/20 backdrop-blur-md relative z-20">
               <form onSubmit={handleInterrupt} className="flex gap-3 relative max-w-4xl mx-auto">
                 <input 
                   type="text" 
                   value={input}
                   onChange={(e) => setInput(e.target.value)}
                   disabled={status !== 'connected'}
                   placeholder="Interupsi debat atau berikan fakta baru ke dalam arena..."
                   className="flex-1 bg-black/40 border border-white/10 rounded-xl px-5 py-4 focus:outline-none focus:border-rose-500 transition-colors placeholder:text-slate-500 disabled:opacity-50"
                 />
                 <button 
                   type="submit" 
                   disabled={status !== 'connected' || !input.trim()}
                   className="glass-button bg-rose-600 hover:bg-rose-500 text-white px-6 rounded-xl flex items-center justify-center disabled:opacity-50 font-bold tracking-wide shadow-lg shadow-rose-500/20"
                 >
                   INTERUPSI <Send size={16} className="ml-2" />
                 </button>
               </form>
             </div>
           )}

        </div>
      </div>
      
      {toastEvent && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-indigo-600/90 backdrop-blur-md px-5 py-2 rounded-full text-sm font-medium z-50 animate-fade-in shadow-xl shadow-indigo-500/20 border border-indigo-400">
          {toastEvent}
        </div>
      )}
    </div>
  );
}
