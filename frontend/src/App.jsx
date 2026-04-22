import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useStore } from './store';
import { BrainCircuit, Users, History, Sword } from 'lucide-react';
import ChatRoom from './pages/ChatRoom';
import AgentManager from './pages/AgentManager';
import SessionHistory from './pages/SessionHistory';
import DebateArena from './pages/DebateArena';

function Navigation() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Brainstorm', icon: BrainCircuit },
    { path: '/debate', label: 'Arena', icon: Sword },
    { path: '/agents', label: 'Agents', icon: Users },
    { path: '/sessions', label: 'History', icon: History },
  ];

  return (
    <nav className="w-full h-16 glass-panel border-b border-x-0 border-t-0 rounded-none z-50 px-6 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <BrainCircuit size={18} className="text-white" />
        </div>
        <span className="text-xl font-bold tracking-widest text-slate-100">AGENTROOM</span>
      </div>
      
      <div className="flex gap-1 md:gap-4">
        {navItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link 
              key={item.path} 
              to={item.path}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300 font-medium text-sm
                ${active ? 'bg-indigo-500/20 text-indigo-300 shadow-inner' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}
              `}
            >
              <item.icon size={16} />
              <span className="hidden md:inline">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

function App() {
  const { fetchAgents } = useStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return (
    <BrowserRouter>
      <div className="bg-slate-900 h-screen w-screen flex flex-col text-slate-100 font-sans selection:bg-indigo-500/30 overflow-hidden">
        <Navigation />
        <main className="flex-1 overflow-hidden relative">
          <Routes>
            <Route path="/" element={<ChatRoom />} />
            <Route path="/debate" element={<DebateArena />} />
            <Route path="/agents" element={<AgentManager />} />
            <Route path="/sessions" element={<SessionHistory />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
