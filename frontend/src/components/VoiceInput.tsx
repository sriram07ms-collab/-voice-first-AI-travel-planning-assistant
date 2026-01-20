/**
 * Voice Input Component
 * Web Speech API integration for voice input.
 * FIXED: Removed isRecording from useEffect dependencies to prevent abort loop
 */

'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';

export interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  onInterimTranscript?: (text: string) => void;
}

export default function VoiceInput({ onTranscript, disabled = false, onInterimTranscript }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSupported, setIsSupported] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [finalTranscript, setFinalTranscript] = useState<string>('');
  
  // Refs to track state without causing re-renders or closure issues
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isUserStoppedRef = useRef<boolean>(false);
  const sendTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const accumulatedFinalRef = useRef<string>('');
  const shouldBeRecordingRef = useRef<boolean>(false);
  const onTranscriptRef = useRef(onTranscript);
  const onInterimTranscriptRef = useRef(onInterimTranscript);

  // Keep refs updated with latest callbacks
  useEffect(() => {
    onTranscriptRef.current = onTranscript;
    onInterimTranscriptRef.current = onInterimTranscript;
  }, [onTranscript, onInterimTranscript]);

  // Check browser support immediately
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      setIsSupported(true);
    } else {
      setIsSupported(false);
      setError('Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.');
    }
  }, []);

  // Clear send timeout
  const clearSendTimeout = useCallback(() => {
    if (sendTimeoutRef.current) {
      clearTimeout(sendTimeoutRef.current);
      sendTimeoutRef.current = null;
    }
  }, []);

  // Send transcript immediately and stop recording
  const sendTranscript = useCallback((text: string) => {
    if (!text.trim() || isUserStoppedRef.current) return;
    
    clearSendTimeout();
    
    // Stop recording before sending transcript
    isUserStoppedRef.current = true;
    shouldBeRecordingRef.current = false;
    
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // Ignore errors
      }
    }
    
    setIsRecording(false);
    
    // Send the transcript
    onTranscriptRef.current(text.trim());
    
    // Clear accumulated text
    accumulatedFinalRef.current = '';
    setFinalTranscript('');
    setInterimTranscript('');
    if (onInterimTranscriptRef.current) {
      onInterimTranscriptRef.current('');
    }
  }, [clearSendTimeout]);

  // Initialize recognition ONCE when supported - NEVER recreate it
  useEffect(() => {
    if (isSupported !== true) return;
    
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition || recognitionRef.current) {
      console.log('Recognition already initialized or not supported');
      return; // Already initialized, don't recreate
    }

    console.log('Initializing speech recognition (ONCE)');
    const recognition = new SpeechRecognition();
    
    // Configure recognition - OPTIMIZED for lower latency
    recognition.continuous = false; // Stop after each input
    recognition.interimResults = true; // Show interim results for real-time feedback
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;
    
    // Note: Some browsers support serviceURI for faster recognition
    // but it's not standard, so we rely on browser defaults
    
    console.log('Recognition configured:', {
      continuous: recognition.continuous,
      interimResults: recognition.interimResults,
      lang: recognition.lang
    });

    // Handle recognition start
    recognition.onstart = () => {
      console.log('✓ Speech recognition started');
      setIsRecording(true);
      shouldBeRecordingRef.current = true;
      setError(null);
      isUserStoppedRef.current = false;
      accumulatedFinalRef.current = '';
      setFinalTranscript('');
      setInterimTranscript('');
      clearSendTimeout();
    };

    // Handle results - THIS IS WHERE TRANSCRIPTS COME IN
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimText = '';
      let newFinalText = '';

      // Process results from resultIndex onwards (new results)
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;

        if (result.isFinal) {
          // Final result - add to accumulated final transcript
          newFinalText += transcript + ' ';
        } else {
          // Interim result - show live
          interimText += transcript;
        }
      }

      // Update accumulated final transcript
      if (newFinalText.trim()) {
        accumulatedFinalRef.current += newFinalText;
        setFinalTranscript(accumulatedFinalRef.current);
        console.log('✓ Final transcript updated:', accumulatedFinalRef.current);
      }

      // Update interim transcript for display
      const fullText = (accumulatedFinalRef.current + ' ' + interimText).trim();
      if (interimText !== interimTranscript) {
        setInterimTranscript(interimText);
        if (onInterimTranscriptRef.current) {
          onInterimTranscriptRef.current(fullText);
        }
      } else if (newFinalText.trim()) {
        // Update display even if interim hasn't changed but we have final text
        if (onInterimTranscriptRef.current) {
          onInterimTranscriptRef.current(fullText);
        }
      }

      // If we have final results, send immediately (no continuous mode)
      if (newFinalText.trim()) {
        clearSendTimeout();
        
        // Send immediately after final result (shorter delay for responsiveness)
        sendTimeoutRef.current = setTimeout(() => {
          const textToSend = accumulatedFinalRef.current.trim();
          if (textToSend && !isUserStoppedRef.current) {
            console.log('✓ Sending transcript via timeout:', textToSend);
            sendTranscript(textToSend);
          }
          sendTimeoutRef.current = null;
        }, 500); // Reduced to 500ms for faster response
      }
    };

    // Handle when speech ends
    recognition.onspeechend = () => {
      console.log('Speech ended (pause detected)');
      clearSendTimeout();
      
      // Send accumulated final transcript after speech ends (shorter delay)
      sendTimeoutRef.current = setTimeout(() => {
        const currentFinal = accumulatedFinalRef.current.trim();
        if (currentFinal && !isUserStoppedRef.current) {
          console.log('✓ Sending transcript via onspeechend:', currentFinal);
          sendTranscript(currentFinal);
        }
        sendTimeoutRef.current = null;
      }, 300); // Reduced to 300ms for faster response
    };

    // Handle errors
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      // Don't log 'no-speech' or 'aborted' as errors - they're normal
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        console.error('Speech recognition error:', event.error, event.message);
      }

      clearSendTimeout();

      if (event.error === 'not-allowed') {
        setError('Microphone permission denied. Please allow microphone access.');
        shouldBeRecordingRef.current = false;
        setIsRecording(false);
        isUserStoppedRef.current = true;
      } else if (event.error === 'network') {
        console.warn('Network error - will retry automatically');
        // Don't stop on network error - let it retry
      } else if (event.error === 'no-speech') {
        // Normal during pauses - completely ignore
        // Don't log, don't stop, just continue
      } else if (event.error === 'audio-capture') {
        console.warn('Audio capture issue - will retry');
        // Don't stop - let it retry
      } else if (event.error === 'service-not-allowed') {
        setError('Speech recognition service not allowed. Please check browser settings.');
        shouldBeRecordingRef.current = false;
        setIsRecording(false);
        isUserStoppedRef.current = true;
      } else if (event.error === 'language-not-supported') {
        setError('Language not supported. Please check browser language settings.');
        shouldBeRecordingRef.current = false;
        setIsRecording(false);
        isUserStoppedRef.current = true;
      } else if (event.error === 'aborted') {
        // Recognition was aborted - this is normal when stopping or restarting
        // Don't log as error, just continue
      } else {
        // Unknown errors - log but don't stop
        console.warn('Speech recognition error (non-critical):', event.error);
      }
    };

    // Handle recognition end
    recognition.onend = () => {
      console.log('Recognition ended - checking if should restart...', {
        userStopped: isUserStoppedRef.current,
        shouldBeRecording: shouldBeRecordingRef.current
      });
      
      clearSendTimeout();

      // Send any remaining final transcript if user didn't stop
      const currentFinal = accumulatedFinalRef.current.trim();
      if (currentFinal && !isUserStoppedRef.current) {
        console.log('✓ Sending transcript via onend:', currentFinal);
        sendTranscript(currentFinal);
      }

      // With continuous=false, recognition stops after each input
      // Don't auto-restart - user must click to start again
      console.log('Recognition ended - waiting for user to start again');
      shouldBeRecordingRef.current = false;
      setIsRecording(false);
      
      // Clear any remaining text
      accumulatedFinalRef.current = '';
      setFinalTranscript('');
      setInterimTranscript('');
      if (onInterimTranscriptRef.current) {
        onInterimTranscriptRef.current('');
      }
    };

    recognitionRef.current = recognition;

    // Cleanup ONLY on unmount - never abort during normal operation
    return () => {
      console.log('Component unmounting - cleaning up recognition');
      clearSendTimeout();
      if (recognitionRef.current) {
        try {
          // Only abort on actual unmount, not on state changes
          recognitionRef.current.abort();
        } catch (e) {
          // Ignore cleanup errors
        }
        recognitionRef.current = null;
      }
    };
  }, [isSupported, clearSendTimeout, sendTranscript]); // REMOVED isRecording, interimTranscript, onTranscript, onInterimTranscript

  const startRecording = useCallback(() => {
    if (!recognitionRef.current || disabled) {
      console.log('Cannot start: recognition =', !!recognitionRef.current, 'disabled =', disabled);
      return;
    }

    console.log('▶ Starting recording...');
    isUserStoppedRef.current = false;
    shouldBeRecordingRef.current = true;
    accumulatedFinalRef.current = '';
    setError(null);
    setFinalTranscript('');
    setInterimTranscript('');
    clearSendTimeout();

    try {
      // Set recording state optimistically for immediate UI feedback
      setIsRecording(true);
      
      // Start recognition immediately (no delay for lower latency)
      recognitionRef.current.start();
      console.log('Start command sent to recognition');
    } catch (err: any) {
      console.error('Error starting recognition:', err);
      if (err.name === 'InvalidStateError' || err.message?.includes('already started')) {
        // Already started - that's fine
        console.log('Recognition already started');
        setIsRecording(true);
        shouldBeRecordingRef.current = true;
      } else {
        shouldBeRecordingRef.current = false;
        setIsRecording(false);
        if (err.message?.includes('not allowed') || err.message?.includes('permission')) {
          setError('Microphone permission denied. Please allow microphone access in your browser settings.');
        } else {
          setError(`Failed to start recording: ${err.message || 'Unknown error'}`);
        }
        isUserStoppedRef.current = true;
      }
    }
  }, [disabled, clearSendTimeout]);

  const stopRecording = useCallback(() => {
    console.log('■ Stopping recording...');
    isUserStoppedRef.current = true;
    shouldBeRecordingRef.current = false;
    clearSendTimeout();

    // Send any accumulated transcript before stopping
    if (accumulatedFinalRef.current.trim()) {
      console.log('✓ Sending final transcript on stop:', accumulatedFinalRef.current);
      sendTranscript(accumulatedFinalRef.current);
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // Ignore errors
      }
    }

    setIsRecording(false);
    accumulatedFinalRef.current = '';
    setFinalTranscript('');
    setInterimTranscript('');
    if (onInterimTranscriptRef.current) {
      onInterimTranscriptRef.current('');
    }
  }, [sendTranscript, clearSendTimeout]);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  // Show checking state
  if (isSupported === null) {
    return (
      <div className="flex flex-col items-center gap-2">
        <div className="w-16 h-16 rounded-full bg-[#E4E6EB] flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-[#65676B] border-t-transparent rounded-full animate-spin"></div>
        </div>
        <p className="text-sm text-[#65676B]">Checking microphone support...</p>
      </div>
    );
  }

  // Show not supported message
  if (isSupported === false) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-yellow-800 text-sm">
          Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.
        </p>
      </div>
    );
  }

  const displayText = (accumulatedFinalRef.current || finalTranscript) + ' ' + interimTranscript;
  const displayTextTrimmed = displayText.trim();

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={toggleRecording}
        disabled={disabled}
        className={`
          w-16 h-16 rounded-full flex items-center justify-center
          transition-all duration-200
          ${isRecording
            ? 'bg-red-500 hover:bg-red-600 animate-pulse'
            : 'bg-[#1877F2] hover:bg-[#166FE5]'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          shadow-lg hover:shadow-xl
          disabled:animate-none
        `}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        title={isRecording ? 'Click to stop recording' : 'Click to start recording'}
      >
        {isRecording ? (
          <svg
            className="w-8 h-8 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 012 0v4a1 1 0 11-2 0V7zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <svg
            className="w-8 h-8 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </button>
      
      {isRecording && (
        <div className="flex flex-col items-center gap-1">
          <p className="text-sm text-[#65676B] animate-pulse">Recording...</p>
          {displayTextTrimmed && (
            <p className="text-sm text-[#65676B] italic max-w-md text-center">
              "{displayTextTrimmed}"
            </p>
          )}
        </div>
      )}
      
      {error && (
        <p className="text-sm text-red-600 mt-2 text-center max-w-md">{error}</p>
      )}
    </div>
  );
}

// TypeScript declarations for Web Speech API
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}
