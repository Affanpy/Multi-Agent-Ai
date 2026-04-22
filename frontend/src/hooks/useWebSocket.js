import { useEffect, useRef, useState } from 'react';
import { useStore } from '../store';

const WS_URL = "ws://localhost:8000/ws";

export function useWebSocket(sessionId) {
  const ws = useRef(null);
  const [status, setStatus] = useState('disconnected');
  const [toastEvent, setToastEvent] = useState(null);
  
  const { 
      addMessage, 
      appendStreamToken, 
      finalizeAgentMessage, 
      setTyping, 
      setActiveOrder 
  } = useStore();

  useEffect(() => {
    if (!sessionId) return;
    
    setStatus('connecting');
    ws.current = new WebSocket(`${WS_URL}/${sessionId}`);
    
    ws.current.onopen = () => setStatus('connected');
    
    ws.current.onclose = () => {
        setStatus('disconnected');
        // Simple reconnect logic could go here
    };
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.type) {
        case 'user_message':
          // We might have already added it speculatively, but let's keep it simple and add it purely from server.
          // Or if client added exactly this one, we skip. But usually client sends and server rebroadcasts.
          // To avoid duplicates, client should not add speculatively if it trusts the connection.
          // However for snappiness, client might add. If so, we'd need ID tracking. We'll simply let server bounce it back for now.
          addMessage({ 
            id: data.timestamp, 
            role: 'user', 
            content: data.content, 
            timestamp: data.timestamp,
            is_private: data.is_private,
            target_agent_id: data.target_agent_id,
            replyToAgent: data.reply_to_agent_name || null,
            fileInfo: data.file_info || null
          });
          break;
        case 'moderator_decision':
          useStore.getState().setModerating(false);
          setActiveOrder(data.speaking_order);
          if (data.speaking_order.length > 0) {
             const currentAgents = useStore.getState().agents;
             const names = data.speaking_order.map(id => {
                const agent = currentAgents.find(a => a.id === id);
                return agent ? agent.name : 'Unknown';
             });
             setToastEvent(`💡 Moderator decided turn: ${names.join(' ➔ ')}`);
             setTimeout(() => setToastEvent(null), 4000);
          }
          break;
        case 'agent_typing':
          setTyping(true, { id: data.agent_id, name: data.agent_name, emoji: data.agent_emoji });
          break;
        case 'agent_stream':
          appendStreamToken(data.agent_id, data.token, data.is_private, data.target_agent_id);
          break;
        case 'agent_done':
          finalizeAgentMessage(data.agent_id, data.full_message, data.timestamp, data.is_private, data.target_agent_id);
          setTyping(false);
          break;
        case 'round_complete':
          setActiveOrder([]);
          setTyping(false);
          break;
        case 'error':
          console.error("WS Server Error:", data.content);
          break;
        default:
          break;
      }
    };

    return () => {
      if (ws.current) {
          ws.current.close();
      }
    };
  }, [sessionId, addMessage, appendStreamToken, finalizeAgentMessage, setTyping, setActiveOrder]);

  const sendMessage = (content, isPrivate = false, targetAgentId = null, replyToAgentId = null, fileId = null) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const moderatorEnabled = useStore.getState().moderatorEnabled;
      // Reply bypass moderator; private juga bypass
      if (!isPrivate && !replyToAgentId && moderatorEnabled) {
         useStore.getState().setModerating(true);
      }
      ws.current.send(JSON.stringify({ 
          type: 'chat', 
          content, 
          session_id: sessionId,
          is_private: isPrivate,
          target_agent_id: targetAgentId,
          moderator_enabled: moderatorEnabled,
          reply_to_agent_id: replyToAgentId,
          file_id: fileId
      }));
    } else {
      console.warn("WebSocket not connected");
    }
  };

  return { status, sendMessage, toastEvent };
}
