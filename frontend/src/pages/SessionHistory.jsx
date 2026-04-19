import React, { useEffect } from 'react';
import { useStore } from '../store';
import { MessageSquare, Trash2, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function SessionHistory() {
  const { sessions, fetchSessions, loadSession, deleteSession } = useStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleOpenSession = async (id) => {
    await loadSession(id);
    navigate('/');
  };

  return (
    <div className="h-full overflow-y-auto">
    <div className="p-6 md:p-10 w-full max-w-5xl mx-auto pb-20">
      <div className="mb-10">
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">Session History</h1>
          <p className="text-slate-400 mt-2">Resume past brainstorming discussions.</p>
      </div>

      <div className="flex flex-col gap-4">
        {sessions.length === 0 && (
          <div className="text-center py-20 bg-white/5 rounded-2xl border border-white/5 border-dashed">
             <p className="text-slate-400">No sessions recorded yet.</p>
          </div>
        )}
        
        {sessions.map(session => (
            <div key={session.id} className="glass-panel p-6 flex flex-col md:flex-row justify-between items-center group cursor-pointer hover:bg-white/10 transition-colors" onClick={() => handleOpenSession(session.id)}>
                <div className="flex items-center gap-4 mb-4 md:mb-0">
                    <div className="bg-emerald-500/20 p-4 rounded-xl text-emerald-400">
                        <MessageSquare size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-100">{session.title}</h3>
                        <p className="text-sm text-slate-400">{new Date(session.created_at.endsWith('Z') ? session.created_at : session.created_at + 'Z').toLocaleString()}</p>
                    </div>
                </div>
                
                <div className="flex items-center gap-3">
                   <button className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition opacity-0 group-hover:opacity-100">
                      Resume <ArrowRight size={16} />
                   </button>
                   <button onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }} className="p-2 text-rose-500/50 hover:text-rose-500 transition-colors rounded-lg hover:bg-rose-500/10">
                       <Trash2 size={18} />
                   </button>
                </div>
            </div>
        ))}
      </div>
    </div>
    </div>
  );
}
