import React from 'react';

export default function TypingIndicator({ name, emoji }) {
  return (
    <div className="flex w-full justify-start mb-6 animate-fade-in">
      <div className="flex flex-col items-start">
        <div className="flex items-center gap-2 mb-1 px-1">
            <span className="text-lg">{emoji}</span>
            <span className="text-sm font-semibold text-indigo-300">{name}</span>
        </div>
        <div className="p-4 rounded-xl shadow-lg bg-white/5 border border-white/10 rounded-tl-none flex items-center gap-2">
           <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
           <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }} />
           <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
