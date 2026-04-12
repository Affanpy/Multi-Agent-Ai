import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import AgentCard from '../components/AgentCard';
import { Plus } from 'lucide-react';

export default function AgentManager() {
  const { agents, fetchAgents, createAgent, updateAgent } = useStore();
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const defaultForm = {
      name: '', avatar_emoji: '🤖', role: '', soul: '', system_prompt: '',
      provider: 'openai', model: '', api_key: '', temperature: 0.7, max_tokens: 1024, is_active: true
  };
  const [formData, setFormData] = useState(defaultForm);

  const handleEdit = (agent) => {
      setEditId(agent.id);
      setFormData({
          name: agent.name, avatar_emoji: agent.avatar_emoji, role: agent.role, soul: agent.soul, system_prompt: agent.system_prompt,
          provider: agent.provider, model: agent.model, api_key: '', temperature: agent.temperature, max_tokens: agent.max_tokens, is_active: agent.is_active
      });
      setShowForm(true);
  };

  const handleAddNew = () => {
      setEditId(null);
      setFormData(defaultForm);
      setShowForm(!showForm);
  };

  const handleSubmit = async (e) => {
      e.preventDefault();
      if (editId) {
          await updateAgent(editId, formData);
      } else {
          await createAgent(formData);
      }
      setShowForm(false);
      setEditId(null);
      setFormData(defaultForm);
  };

  return (
    <div className="h-full overflow-y-auto p-6 md:p-10 w-full max-w-7xl mx-auto pb-20">
      <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">Agent Manager</h1>
            <p className="text-slate-400 mt-2">Manage your AI brainstorming personalities.</p>
          </div>
          <button onClick={handleAddNew} className="glass-button flex items-center gap-2 px-6 py-3 bg-indigo-600 rounded-xl text-white font-medium shadow-lg shadow-indigo-500/20">
              <Plus size={20}/> {showForm && !editId ? 'Cancel' : 'Add Agent'}
          </button>
      </div>

      {showForm && (
          <div className="glass-panel p-6 mb-10 animate-fade-in border border-indigo-500/30 shadow-[0_0_30px_rgba(99,102,241,0.1)]">
              <h2 className="text-xl font-bold mb-6">{editId ? 'Edit Agent' : 'Create New Agent'}</h2>
              <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                      <label className="block text-sm text-slate-400 mb-1">Name</label>
                      <input required className="w-full bg-black/20 border border-white/10 rounded-lg p-3" value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} />
                  </div>
                  <div>
                      <label className="block text-sm text-slate-400 mb-1">Emoji / Avatar</label>
                      <input required className="w-full bg-black/20 border border-white/10 rounded-lg p-3" value={formData.avatar_emoji} onChange={e=>setFormData({...formData, avatar_emoji: e.target.value})} />
                  </div>
                  <div>
                      <label className="block text-sm text-slate-400 mb-1">Role / Job Title</label>
                      <input required className="w-full bg-black/20 border border-white/10 rounded-lg p-3" value={formData.role} onChange={e=>setFormData({...formData, role: e.target.value})} />
                  </div>
                  <div>
                      <label className="block text-sm text-slate-400 mb-1">Provider</label>
                      <select className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-white [&>option]:bg-slate-800" value={formData.provider} onChange={e=>setFormData({...formData, provider: e.target.value})}>
                          <option value="openai">OpenAI</option>
                          <option value="anthropic">Anthropic</option>
                          <option value="gemini">Gemini</option>
                      </select>
                  </div>
                  <div>
                      <label className="block text-sm text-slate-400 mb-1">Model (e.g. gpt-4o, claude-3-5-sonnet-20241022)</label>
                      <input required className="w-full bg-black/20 border border-white/10 rounded-lg p-3" value={formData.model} onChange={e=>setFormData({...formData, model: e.target.value})} />
                  </div>
                  <div>
                      <label className="block text-sm text-slate-400 mb-1">API Key {editId && '(Kosongkan jika tidak ingin diubah)'}</label>
                      <input required={!editId} type="password" placeholder="••••••••••••••••" className="w-full bg-black/20 border border-white/10 rounded-lg p-3" value={formData.api_key} onChange={e=>setFormData({...formData, api_key: e.target.value})} />
                  </div>
                  
                  <div className="md:col-span-2">
                      <label className="block text-sm text-slate-400 mb-1">Soul / Personality</label>
                      <textarea required rows={2} className="w-full bg-black/20 border border-white/10 rounded-lg p-3" value={formData.soul} onChange={e=>setFormData({...formData, soul: e.target.value})} />
                  </div>
                  <div className="md:col-span-2">
                      <label className="block text-sm text-slate-400 mb-1">System Prompt / Core Directives</label>
                      <textarea required rows={3} className="w-full bg-black/20 border border-white/10 rounded-lg p-3" value={formData.system_prompt} onChange={e=>setFormData({...formData, system_prompt: e.target.value})} />
                  </div>
                  
                  <div className="md:col-span-2 flex justify-end gap-3 mt-4">
                      <button type="button" onClick={()=>setShowForm(false)} className="px-6 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition">Cancel</button>
                      <button type="submit" className="px-6 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 transition">{editId ? 'Update Agent' : 'Save Agent'}</button>
                  </div>
              </form>
          </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {agents.map(agent => (
              <AgentCard key={agent.id} agent={agent} onEdit={() => handleEdit(agent)} />
          ))}
      </div>
      {agents.length === 0 && !showForm && (
          <div className="text-center py-20 bg-white/5 rounded-2xl border border-white/5 border-dashed">
              <span className="text-6xl mb-4 block">🤖</span>
              <p className="text-slate-400">No agents yet. Create one to start brainstorming!</p>
          </div>
      )}
    </div>
  );
}
