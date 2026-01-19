/**
 * Text Input Component
 * Text-based message input for chat interface.
 */

'use client';

import React, { useState, KeyboardEvent } from 'react';

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

  const handleSubmit = () => {
    if (!message.trim() || disabled) return;
    
    const textToSend = message.trim();
    setMessage('');
    onSendMessage(textToSend);
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="flex items-end gap-2 bg-white rounded-lg border border-gray-300 p-3 shadow-sm">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          placeholder={placeholder}
          rows={1}
          className="
            flex-1 resize-none border-none outline-none
            text-gray-900 placeholder-gray-500
            disabled:opacity-50 disabled:cursor-not-allowed
            max-h-32 overflow-y-auto
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
            px-6 py-2 bg-blue-500 text-white rounded-lg
            hover:bg-blue-600 active:bg-blue-700
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors font-medium
            flex items-center gap-2
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
      <p className="text-xs text-gray-500 mt-2 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}
