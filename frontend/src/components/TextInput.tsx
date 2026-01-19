/**
 * Text Input Component
 * Modern text-based message input for chat interface.
 */

'use client';

import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';

export interface TextInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function TextInput({ 
  onSendMessage, 
  disabled = false,
  placeholder = "Type your message..."
}: TextInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = () => {
    if (!message.trim() || disabled) return;
    
    const textToSend = message.trim();
    setMessage('');
    onSendMessage(textToSend);
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full">
      <div className="flex items-end gap-2 bg-white rounded-xl border-2 border-slate-200 p-3 shadow-sm focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all duration-200">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          placeholder={placeholder}
          rows={1}
          className="
            flex-1 resize-none border-none outline-none bg-transparent
            text-slate-900 placeholder-slate-400
            disabled:opacity-50 disabled:cursor-not-allowed
            max-h-32 overflow-y-auto scrollbar-thin
            text-sm leading-relaxed
          "
          style={{
            minHeight: '24px',
            height: 'auto',
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !message.trim()}
          className="
            px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg
            hover:from-blue-700 hover:to-indigo-700
            active:scale-95
            disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100
            transition-all duration-200 font-semibold text-sm
            flex items-center gap-2 shadow-md shadow-blue-500/30
            hover:shadow-lg hover:shadow-blue-500/40
          "
        >
          <span>Send</span>
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </div>
      <p className="text-xs text-slate-500 mt-2 text-center">
        Press <kbd className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-600 font-medium">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-600 font-medium">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
