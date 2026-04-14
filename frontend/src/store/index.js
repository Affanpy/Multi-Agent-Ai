import { create } from 'zustand';

const API_URL = "http://localhost:8000/api";

export const useStore = create((set, get) => ({
  agents: [],
  sessions: [],
  currentSession: null,
  messages: [],
  isTyping: false,
  typingAgent: null,
  activeOrder: [],
  isCreatingSession: false,
  
  fetchAgents: async () => {
    try {
      const res = await fetch(`${API_URL}/agents`);
      if (res.ok) set({ agents: await res.json() });
    } catch(e) { console.error(e) }
  },
  
  createAgent: async (agentData) => {
    const res = await fetch(`${API_URL}/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(agentData)
    });
    if (res.ok) {
      const newAgent = await res.json();
      set(state => ({ agents: [...state.agents, newAgent] }));
    }
  },

  deleteAgent: async (id) => {
    const res = await fetch(`${API_URL}/agents/${id}`, { method: 'DELETE' });
    if (res.ok) {
      set(state => ({ agents: state.agents.filter(a => a.id !== id) }));
    }
  },
  
  updateAgent: async (id, updatedData) => {
    const res = await fetch(`${API_URL}/agents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedData)
    });
    if (res.ok) {
      const updatedAgent = await res.json();
      set(state => ({ agents: state.agents.map(a => a.id === id ? updatedAgent : a) }));
    }
  },
  
  fetchSessions: async () => {
    try {
      const res = await fetch(`${API_URL}/sessions`);
      if (res.ok) set({ sessions: await res.json() });
    } catch(e) { console.error(e) }
  },

  createSession: async () => {
    if (get().isCreatingSession) return;
    set({ isCreatingSession: true });
    
    try {
      const res = await fetch(`${API_URL}/sessions`, { method: 'POST' });
      if (res.ok) {
        const newSession = await res.json();
        set(state => ({ 
           sessions: [newSession, ...state.sessions],
           currentSession: newSession,
           messages: [],
           isCreatingSession: false
        }));
        return newSession;
      }
    } catch (e) {
      console.error("Gagal membuat sesi:", e);
    }
    set({ isCreatingSession: false });
  },
  
  loadSession: async (id) => {
    const res = await fetch(`${API_URL}/sessions/${id}`);
    if (res.ok) {
      const data = await res.json();
      set({ currentSession: data, messages: data.messages || [] });
    }
  },

  deleteSession: async (id) => {
    const res = await fetch(`${API_URL}/sessions/${id}`, { method: 'DELETE' });
    if (res.ok) {
        set(state => ({ 
            sessions: state.sessions.filter(s => s.id !== id),
            currentSession: state.currentSession?.id === id ? null : state.currentSession,
            messages: state.currentSession?.id === id ? [] : state.messages
        }));
    }
  },

  clearSession: () => set({ currentSession: null, messages: [] }),
  
  addMessage: (msg) => set(state => ({ messages: [...state.messages, msg] })),
  
  appendStreamToken: (agentId, token) => set(state => {
    const messages = [...state.messages];
    const lastMsg = messages[messages.length - 1];
    
    if (lastMsg && lastMsg.agent_id === agentId && lastMsg.isStreaming) {
      lastMsg.content += token;
    } else {
      messages.push({
        id: `temp-${Date.now()}`,
        role: 'agent',
        agent_id: agentId,
        content: token,
        isStreaming: true
      });
    }
    return { messages };
  }),
  
  finalizeAgentMessage: (agentId, fullContent, timestamp) => set(state => {
    const messages = [...state.messages];
    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.agent_id === agentId && lastMsg.isStreaming) {
      lastMsg.content = fullContent;
      lastMsg.isStreaming = false;
      if (timestamp) lastMsg.timestamp = timestamp;
    } else {
        messages.push({
            id: `temp-${Date.now()}`,
            role: 'agent',
            agent_id: agentId,
            content: fullContent,
            timestamp: timestamp,
            isStreaming: false
        });
    }
    return { messages, isTyping: false };
  }),

  setTyping: (status, agent = null) => set({ isTyping: status, typingAgent: agent }),
  setActiveOrder: (order) => set({ activeOrder: order })
}));
