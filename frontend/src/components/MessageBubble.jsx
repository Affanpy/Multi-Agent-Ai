import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../store';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, Reply } from 'lucide-react';

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button 
      onClick={handleCopy}
      className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-slate-200 transition-colors px-2 py-1 rounded hover:bg-white/10"
    >
      {copied ? <><Check size={12} className="text-emerald-400" /> Copied!</> : <><Copy size={12} /> Copy</>}
    </button>
  );
}

const markdownComponents = {
  // Code blocks with syntax highlighting
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '');
    const codeString = String(children).replace(/\n$/, '');
    
    if (!inline && match) {
      return (
        <div className="my-3 rounded-lg overflow-hidden border border-white/10">
          <div className="flex items-center justify-between px-4 py-2 bg-slate-800/80 border-b border-white/10">
            <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">{match[1]}</span>
            <CopyButton text={codeString} />
          </div>
          <SyntaxHighlighter
            style={oneDark}
            language={match[1]}
            PreTag="div"
            customStyle={{ 
              margin: 0, 
              padding: '1rem', 
              background: 'rgba(0,0,0,0.3)',
              fontSize: '12px',
              lineHeight: '1.6'
            }}
            {...props}
          >
            {codeString}
          </SyntaxHighlighter>
        </div>
      );
    }
    
    if (!inline && !match) {
      return (
        <div className="my-3 rounded-lg overflow-hidden border border-white/10">
          <div className="flex items-center justify-between px-4 py-2 bg-slate-800/80 border-b border-white/10">
            <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">code</span>
            <CopyButton text={codeString} />
          </div>
          <pre className="p-4 bg-black/30 overflow-x-auto text-xs leading-relaxed">
            <code className="text-slate-200">{children}</code>
          </pre>
        </div>
      );
    }

    // Inline code
    return (
      <code className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-xs font-mono border border-indigo-500/10" {...props}>
        {children}
      </code>
    );
  },

  // Headings
  h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2 text-slate-100 border-b border-white/10 pb-2">{children}</h1>,
  h2: ({ children }) => <h2 className="text-lg font-bold mt-3 mb-2 text-slate-100">{children}</h2>,
  h3: ({ children }) => <h3 className="text-base font-semibold mt-3 mb-1 text-slate-200">{children}</h3>,
  h4: ({ children }) => <h4 className="text-sm font-semibold mt-2 mb-1 text-slate-200">{children}</h4>,

  // Paragraphs
  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,

  // Lists
  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1 pl-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1 pl-1">{children}</ol>,
  li: ({ children }) => <li className="text-sm leading-relaxed">{children}</li>,

  // Tables
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto rounded-lg border border-white/10">
      <table className="w-full text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-white/5 border-b border-white/10">{children}</thead>,
  th: ({ children }) => <th className="px-3 py-2 text-left text-xs font-semibold text-indigo-300 uppercase tracking-wider">{children}</th>,
  td: ({ children }) => <td className="px-3 py-2 border-t border-white/5 text-slate-300">{children}</td>,
  tr: ({ children }) => <tr className="even:bg-white/[0.02]">{children}</tr>,

  // Blockquote
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-indigo-500/50 pl-3 my-2 text-slate-400 italic">{children}</blockquote>
  ),

  // Links
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition-colors">
      {children}
    </a>
  ),

  // Horizontal rule
  hr: () => <hr className="my-3 border-white/10" />,

  // Strong & emphasis
  strong: ({ children }) => <strong className="font-bold text-slate-50">{children}</strong>,
  em: ({ children }) => <em className="italic text-slate-300">{children}</em>,
};

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const { agents, setReplyTo } = useStore();
  
  const agent = isUser ? null : agents.find(a => a.id === message.agent_id);

  const [displayedContent, setDisplayedContent] = useState(message.isStreaming ? '' : message.content);
  const bufferRef = useRef(message.content);

  useEffect(() => {
    bufferRef.current = message.content;
  }, [message.content]);

  useEffect(() => {
    if (!message.isStreaming && bufferRef.current.length === displayedContent.length) {
       return;
    }
    
    let localInterval;
    localInterval = setInterval(() => {
      setDisplayedContent((current) => {
        const target = bufferRef.current;
        if (current.length < target.length) {
          let step = 1;
          const gap = target.length - current.length;
          if (gap > 20) step = 3;
          if (gap > 60) step = 8;
          if (!message.isStreaming) step = Math.max(step, Math.ceil(gap / 3)); 
          return current + target.substring(current.length, current.length + step);
        } else if (!message.isStreaming) {
          clearInterval(localInterval);
        }
        return current;
      });
    }, 20);

    return () => clearInterval(localInterval);
  }, [message.isStreaming]);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`max-w-[80%] md:max-w-[70%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        {!isUser && agent && (
          <div className="flex items-center gap-2 mb-1 px-1">
            <span className="text-lg">{agent.avatar_emoji}</span>
            <span className="text-sm font-semibold text-indigo-300">{agent.name}</span>
            <span className="text-xs text-slate-400">— {agent.role}</span>
          </div>
        )}
        
        {/* Reply indicator — jika pesan ini adalah balasan ke agen tertentu */}
        {isUser && message.replyToAgent && (
          <div className="flex items-center gap-1.5 mb-1 px-1">
            <Reply size={12} className="text-slate-500" />
            <span className="text-[10px] text-slate-500">Membalas <span className="text-indigo-400 font-semibold">{message.replyToAgent}</span></span>
          </div>
        )}
        
        <div className={`p-4 rounded-xl shadow-lg ${
          isUser 
            ? 'bg-indigo-600 text-white rounded-tr-none' 
            : 'bg-white/10 backdrop-blur-md border border-white/10 text-slate-100 rounded-tl-none'
        }`}>
          {isUser ? (
            <div className="whitespace-pre-wrap text-sm leading-relaxed font-sans">
              {displayedContent}
            </div>
          ) : (
            <div className="text-sm leading-relaxed font-sans prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {displayedContent}
              </ReactMarkdown>
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 ml-1 bg-emerald-400 animate-pulse align-middle" />
              )}
            </div>
          )}
        </div>
        
        <div className="text-[10px] text-slate-500 mt-1 px-1 flex items-center gap-2">
            {!isUser && agent && <span className="uppercase text-xs font-bold tracking-wider">{agent.model}</span>}
            <span>{message.timestamp ? new Date(message.timestamp.endsWith('Z') ? message.timestamp : message.timestamp + 'Z').toLocaleTimeString() : ''}</span>
            {!isUser && !message.isStreaming && (
              <CopyButton text={message.content} />
            )}
            {!isUser && !message.isStreaming && (
              <button
                onClick={() => setReplyTo({ agentId: message.agent_id, agentName: agent?.name, agentEmoji: agent?.avatar_emoji, snippet: message.content.substring(0, 60) })}
                className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-slate-200 transition-colors px-2 py-1 rounded hover:bg-white/10"
              >
                <Reply size={12} /> Reply
              </button>
            )}
        </div>
      </div>
    </motion.div>
  );
}
