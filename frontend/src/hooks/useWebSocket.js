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
          addMessage({ id: data.timestamp, role: 'user', content: data.content, timestamp: data.timestamp });
          break;
        case 'moderator_decision':
          setActiveOrder(data.speaking_order);
          if (data.speaking_order.length > 0) {
             setToastEvent(`Moderator decided order: ${data.speaking_order.join(', ')}`);
          }
          break;
        case 'agent_typing':
          setTyping(true, { id: data.agent_id, name: data.agent_name, emoji: data.agent_emoji });
          break;
        case 'agent_stream':
          appendStreamToken(data.agent_id, data.token);
          break;
        case 'agent_done':
          finalizeAgentMessage(data.agent_id, data.full_message, data.timestamp);
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

  const sendMessage = (content) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'chat', content, session_id: sessionId }));
    } else {
      console.warn("WebSocket not connected");
    }
  };

  return { status, sendMessage, toastEvent };
}
