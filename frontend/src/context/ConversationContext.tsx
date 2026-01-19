/**
 * Conversation Context for managing conversation state.
 */

'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect, useRef } from 'react';

// Types
interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface Itinerary {
  city: string;
  duration_days: number;
  pace?: string;
  interests?: string[];
  day_1?: any;
  day_2?: any;
  day_3?: any;
  total_travel_time?: number;
}

interface Source {
  type: string;
  url?: string;
  poi?: string;
  source_id?: string;
  topic?: string;
}

interface ConversationState {
  sessionId: string | null;
  messages: Message[];
  itinerary: Itinerary | null;
  sources: Source[];
  isProcessing: boolean;
  error: string | null;
}

interface ConversationContextType extends ConversationState {
  sendMessage: (message: string, inputMethod?: 'text' | 'voice') => Promise<void>;
  addSystemMessage: (message: string) => void; // Add message directly without API call
  clearConversation: () => void;
  updateItinerary: (itinerary: Itinerary) => void;
  setError: (error: string | null) => void;
  enableTTS: boolean;
  setEnableTTS: (enabled: boolean) => void;
}

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

export function ConversationProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ConversationState>({
    sessionId: null,
    messages: [],
    itinerary: null,
    sources: [],
    isProcessing: false,
    error: null,
  });
  
  const [enableTTS, setEnableTTSState] = useState<boolean>(true);
  
  const setEnableTTS = useCallback((enabled: boolean) => {
    setEnableTTSState(enabled);
  }, []);
  
  // Load voices for TTS on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      // Load voices (may need to be called after user interaction in some browsers)
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => {
          // Voices loaded
        };
      }
      // Try to get voices immediately
      window.speechSynthesis.getVoices();
    }
  }, []);

  const sendMessage = useCallback(async (message: string, inputMethod: 'text' | 'voice' = 'text') => {
    // Add user message to state
    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isProcessing: true,
      error: null,
    }));

    try {
      // Import API client dynamically to avoid SSR issues
      const { apiClient } = await import('../services/api');
      
      // Call API
      const data = await apiClient.sendMessage({
        message,
        session_id: state.sessionId || undefined,
      });

      // Handle different response statuses
      if (data.status === 'error') {
        // Error response
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error: data.message || 'An error occurred',
        }));
        return;
      }

      // Build assistant message
      let assistantContent = data.message || 'Response received';
      
      // For clarifying questions, use the question from response
      if (data.status === 'clarifying' && data.question) {
        assistantContent = data.question;
      }
      
      // For confirmation required, show the confirmation message
      if (data.status === 'confirmation_required') {
        assistantContent = data.message || 'Please confirm to proceed.';
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date().toISOString(),
      };

      // Log sources for debugging
      console.log('Received sources from API:', data.sources);
      console.log('Sources type:', typeof data.sources);
      console.log('Sources length:', data.sources?.length);
      
      setState((prev) => ({
        ...prev,
        sessionId: data.session_id || prev.sessionId,
        messages: [...prev.messages, assistantMessage],
        itinerary: data.itinerary || prev.itinerary,
        sources: Array.isArray(data.sources) ? data.sources : (data.sources || prev.sources || []),
        isProcessing: false,
        error: null,
      }));
      
      // Only speak the assistant's response aloud using TTS if input was from voice
      // Text messages should receive text-only replies
      if (inputMethod === 'voice' && enableTTS && assistantContent && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        speakText(assistantContent);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setState((prev) => ({
        ...prev,
        isProcessing: false,
        error: errorMessage,
      }));
    }
  }, [state.sessionId, enableTTS]);

  const clearConversation = useCallback(() => {
    setState({
      sessionId: null,
      messages: [],
      itinerary: null,
      sources: [],
      isProcessing: false,
      error: null,
    });
  }, []);

  const updateItinerary = useCallback((itinerary: Itinerary) => {
    setState((prev) => ({
      ...prev,
      itinerary,
    }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState((prev) => ({
      ...prev,
      error,
    }));
  }, []);

  const addSystemMessage = useCallback((message: string) => {
    const systemMessage: Message = {
      role: 'assistant',
      content: message,
      timestamp: new Date().toISOString(),
    };
    
    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, systemMessage],
    }));
  }, []);

  return (
    <ConversationContext.Provider
      value={{
        ...state,
        sendMessage,
        addSystemMessage,
        clearConversation,
        updateItinerary,
        setError,
        enableTTS,
        setEnableTTS,
      }}
    >
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversation() {
  const context = useContext(ConversationContext);
  if (context === undefined) {
    throw new Error('useConversation must be used within a ConversationProvider');
  }
  return context;
}

/**
 * Text-to-Speech function using Web Speech API
 * Smart TTS: If text is longer than 3 lines, only read first part and ask user to continue
 */
function speakText(text: string) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    console.warn('Speech synthesis not supported in this browser');
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  // Split text into lines
  const lines = text.split('\n').filter(line => line.trim().length > 0);
  
  // If text has more than 3 lines, only read first 3 lines and ask to continue
  let textToSpeak = text;
  let shouldAskToContinue = false;
  
  if (lines.length > 3) {
    // Take first 3 lines
    const firstThreeLines = lines.slice(0, 3).join('\n');
    textToSpeak = firstThreeLines + '\n\nShall I continue reading, or would you like to proceed with the itinerary?';
    shouldAskToContinue = true;
  }

  const utterance = new SpeechSynthesisUtterance(textToSpeak);
  utterance.lang = 'en-US';
  utterance.rate = 0.95; // Slightly faster for better responsiveness
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  // Try to use a better voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(
    (voice) => voice.lang.startsWith('en') && (voice.name.includes('Natural') || voice.name.includes('Premium'))
  ) || voices.find((voice) => voice.lang.startsWith('en-US'));
  
  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }

  // Store the callback to handle continuation if needed
  utterance.onend = () => {
    if (shouldAskToContinue) {
      // After asking to continue, wait a moment then ask again if user wants to continue
      // This is handled by the UI showing the full message
    }
  };

  window.speechSynthesis.speak(utterance);
}
