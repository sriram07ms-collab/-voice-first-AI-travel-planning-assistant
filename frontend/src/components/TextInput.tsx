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
      <div className="flex items-end gap-1.5 bg-white rounded-lg border border-[#CCD0D5] p-2 shadow-sm focus-within:border-[#1877F2] focus-within:ring-1 focus-within:ring-[#1877F2]/20 transition-all duration-200">
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
            text-[#050505] placeholder:text-[#65676B]
            disabled:opacity-50 disabled:cursor-not-allowed
            max-h-24 overflow-y-auto scrollbar-thin
            text-sm leading-relaxed
          "
          style={{
            minHeight: '20px',
            height: 'auto',
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !message.trim()}
          className="
            px-3 py-1.5 bg-[#1877F2] text-white rounded-md
            hover:bg-[#166FE5]
            active:scale-95
            disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100
            transition-all duration-200 font-semibold text-xs
            flex items-center gap-1.5 shadow-sm
            hover:shadow-md
          "
        >
          <span>Send</span>
          <svg
            className="w-3 h-3"
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
      <p className="text-xs text-[#65676B] mt-1 text-center">
        Press <kbd className="px-1 py-0.5 bg-[#E4E6EB] rounded text-[#050505] font-medium text-xs">Enter</kbd> to send, <kbd className="px-1 py-0.5 bg-[#E4E6EB] rounded text-[#050505] font-medium text-xs">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
