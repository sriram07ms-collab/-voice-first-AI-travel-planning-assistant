/**
 * Transcript Display Component
 * Displays conversation history with auto-scroll.
 */

'use client';

import React, { useEffect, useRef } from 'react';
import type { TranscriptDisplayProps, Message } from '../types';

export default function TranscriptDisplay({ messages }: TranscriptDisplayProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  if (messages.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>No messages yet. Start a conversation!</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Conversation</h3>
      
      <div className="space-y-4 max-h-96 overflow-y-auto bg-gray-50 rounded-lg p-4">
        {messages.map((message, idx) => (
          <div
            key={idx}
            className={`
              flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}
            `}
          >
            <div
              className={`
                max-w-[80%] rounded-lg p-4
                ${message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-900 border border-gray-200'
                }
              `}
            >
              <div className="flex items-start gap-2">
                <div className="flex-1">
                  <p className="whitespace-pre-wrap break-words">{message.content}</p>
                  {message.timestamp && (
                    <p className={`text-xs mt-2 ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      {formatTimestamp(message.timestamp)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
