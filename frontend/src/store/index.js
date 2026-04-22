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
  activePrivateAgent: null,
  isModerating: false,
  moderatorEnabled: true,
  replyTo: null,
  isSummarizing: false,
  
  setModerating: (status) => set({ isModerating: status }),
  setActivePrivateAgent: (agentId) => set({ activePrivateAgent: agentId }),
  toggleModerator: () => set(state => ({ moderatorEnabled: !state.moderatorEnabled })),
  setReplyTo: (message) => set({ replyTo: message }),

  generateSummary: async () => {
    const session = get().currentSession;
    if (!session) return;
    set({ isSummarizing: true });
    try {
      const res = await fetch(`${API_URL}/sessions/${session.id}/summary`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        set(state => ({
          messages: [...state.messages, {
            id: `summary-${Date.now()}`,
            role: 'system',
            content: data.summary,
            timestamp: new Date().toISOString(),
            isSummary: true
          }]
        }));
      } else {
        const err = await res.json();
        alert(err.detail || 'Gagal menghasilkan rangkuman');
      }
    } catch(e) {
      console.error('Summary error:', e);
      alert('Gagal menghasilkan rangkuman');
    }
    set({ isSummarizing: false });
  },

  pendingFile: null,
  isUploading: false,

  uploadFile: async (file) => {
    set({ isUploading: true });
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
      if (res.ok) {
        const data = await res.json();
        // Simpan preview lokal
        const localPreview = file.type.startsWith('image/') ? URL.createObjectURL(file) : null;
        set({ pendingFile: { ...data, localPreview } });
      } else {
        const err = await res.json();
        alert(err.detail || 'Gagal upload file');
      }
    } catch(e) {
      console.error('Upload error:', e);
      alert('Gagal upload file');
    }
    set({ isUploading: false });
  },

  clearPendingFile: () => set({ pendingFile: null }),
  
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

  toggleAgentActive: async (id) => {
    const res = await fetch(`${API_URL}/agents/${id}/toggle`, { method: 'PATCH' });
    if (res.ok) {
      const updated = await res.json();
      set(state => ({ agents: state.agents.map(a => a.id === id ? { ...a, is_active: updated.is_active } : a) }));
    }
  },

  reorderAgents: async (orderedAgents) => {
    set({ agents: orderedAgents });
    await fetch(`${API_URL}/agents/reorder`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ordered_ids: orderedAgents.map(a => a.id) })
    });
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
  
  appendStreamToken: (agentId, token, isPrivate = false, targetAgentId = null) => set(state => {
    const messages = [...state.messages];
    const lastMsg = messages[messages.length - 1];
    
    if (lastMsg && lastMsg.agent_id === agentId && lastMsg.isStreaming && lastMsg.is_private === isPrivate) {
      lastMsg.content += token;
    } else {
      messages.push({
        id: `temp-${Date.now()}`,
        role: 'agent',
        agent_id: agentId,
        content: token,
        isStreaming: true,
        is_private: isPrivate,
        target_agent_id: targetAgentId
      });
    }
    return { messages };
  }),
  
  finalizeAgentMessage: (agentId, fullContent, timestamp, isPrivate = false, targetAgentId = null) => set(state => {
    const messages = [...state.messages];
    const lastMsg = messages[messages.length - 1];
    if (lastMsg && lastMsg.agent_id === agentId && lastMsg.isStreaming && lastMsg.is_private === isPrivate) {
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
            isStreaming: false,
            is_private: isPrivate,
            target_agent_id: targetAgentId
        });
    }
    return { messages, isTyping: false };
  }),

  setTyping: (status, agent = null) => set({ isTyping: status, typingAgent: agent }),
  setActiveOrder: (order) => set({ activeOrder: order })
}));
