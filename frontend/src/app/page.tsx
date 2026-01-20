/**
 * Main Page Component
 * Travel Planning Assistant main interface with modern UI/UX.
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ConversationProvider, useConversation } from '../context/ConversationContext';
import VoiceInput from '../components/VoiceInput';
import TextInput from '../components/TextInput';
import TranscriptDisplay from '../components/TranscriptDisplay';
import ItineraryView from '../components/ItineraryView';
import SourcesView from '../components/SourcesView';
import ExplanationPanel from '../components/ExplanationPanel';
import { apiClient } from '../services/api';
import type { ExplainRequest, EditRequest, GeneratePDFRequest } from '../types';

function TravelAssistantContent() {
  const {
    sessionId,
    messages,
    itinerary,
    sources,
    isProcessing,
    error,
    sendMessage,
    addSystemMessage,
    clearConversation,
    updateItinerary,
    setError,
    enableTTS,
    setEnableTTS,
  } = useConversation();

  const [currentExplanation, setCurrentExplanation] = useState<string | null>(null);
  const [explanationSources, setExplanationSources] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'itinerary' | 'sources'>('chat');
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string>('');
  const [showVoicePrompt, setShowVoicePrompt] = useState<boolean>(false);
  
  // Ref for messages container for auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    // Small delay to ensure DOM is updated
    const timeoutId = setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages, liveTranscript, isProcessing]);

  const handleTranscript = async (text: string) => {
    if (!text.trim()) return;
    setLiveTranscript('');
    setShowVoicePrompt(false);
    await sendMessage(text, 'voice');
    setTimeout(() => {
      setShowVoicePrompt(true);
    }, 2000);
  };

  const handleInterimTranscript = (text: string) => {
    setLiveTranscript(text);
  };

  const handleTextMessage = async (text: string) => {
    setLiveTranscript('');
    await sendMessage(text, 'text');
  };

  const handleExplain = async (question: string) => {
    if (!sessionId) {
      setError('Please start a conversation first');
      return;
    }

    try {
      setError(null);
      let finalQuestion = question;
      if (itinerary && !question.toLowerCase().includes('why') && !question.toLowerCase().includes('explain')) {
        finalQuestion = `Why did you pick ${question}?`;
      }
      
      const request: ExplainRequest = {
        session_id: sessionId,
        question: finalQuestion,
      };

      const response = await apiClient.explainDecision(request);
      setCurrentExplanation(response.explanation || null);
      setExplanationSources(response.sources || []);
    } catch (err: any) {
      console.error('Error getting explanation:', err);
      const errorMsg = err.message || 'Failed to get explanation. Make sure you have an itinerary first.';
      setError(errorMsg);
      setCurrentExplanation(null);
      setExplanationSources([]);
    }
  };

  const handleExplainActivity = async (activityName: string) => {
    await handleExplain(`Why did you pick ${activityName}?`);
  };

  const handleGeneratePDF = async () => {
    if (!sessionId) {
      setError('Please start a conversation first');
      return;
    }

    if (!itinerary) {
      setError('No itinerary available. Please plan a trip first.');
      return;
    }

    let email = userEmail;
    if (!email) {
      email = prompt('Please enter your email address to receive the PDF:');
      if (!email) {
        return;
      }
      setUserEmail(email);
    }

    setIsGeneratingPDF(true);
    setError(null);

    try {
      const request: GeneratePDFRequest = {
        session_id: sessionId,
        email: email,
      };

      const response = await apiClient.generatePDF(request);
      
      if (response.email_sent) {
        setError(null);
        const pdfMessage = `✅ Itinerary PDF has been generated and sent to ${response.email_address}. Please check your email.`;
        addSystemMessage(pdfMessage);
        
        if (response.pdf_url) {
          setPdfUrl(response.pdf_url);
        }
      } else {
        setError('PDF generation completed but email may not have been sent.');
      }
    } catch (err: any) {
      console.error('Error generating PDF:', err);
      setError(err.message || 'Failed to generate PDF. Please try again.');
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const handleEdit = async (editCommand: string) => {
    if (!sessionId) {
      setError('Please start a conversation first');
      return;
    }

    try {
      const request: EditRequest = {
        session_id: sessionId,
        edit_command: editCommand,
      };

      const response = await apiClient.editItinerary(request);
      if (response.itinerary) {
        updateItinerary(response.itinerary);
      }
    } catch (err: any) {
      console.error('Error editing itinerary:', err);
      setError(err.message || 'Failed to edit itinerary');
    }
  };

  const lastMessage = messages[messages.length - 1];
  const isClarifyingQuestion = lastMessage?.role === 'assistant' && 
    messages.length > 0 &&
    itinerary === null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Modern Header - Meta Style */}
      <header className="glass border-b border-[#CCD0D5] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-[#1877F2] mb-1">
                ✈️ Voice-First Travel Assistant
              </h1>
              <p className="text-[#65676B] text-sm">Plan your perfect trip with AI-powered assistance</p>
            </div>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-[#050505] cursor-pointer group">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={enableTTS}
                    onChange={(e) => setEnableTTS(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`w-11 h-6 rounded-full transition-colors duration-200 ${
                    enableTTS ? 'bg-[#1877F2]' : 'bg-[#CCD0D5]'
                  }`}>
                    <div className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-200 mt-0.5 ${
                      enableTTS ? 'translate-x-5' : 'translate-x-0.5'
                    }`} />
                  </div>
                </div>
                <span className="font-medium">Voice Responses</span>
              </label>
              {sessionId && (
                <button
                  onClick={clearConversation}
                  className="btn-secondary text-sm px-4 py-2"
                >
                  Clear Chat
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
        {/* Single chat window - ChatGPT/Gemini style */}
        <div className="card h-[calc(100vh-180px)] lg:h-[calc(100vh-140px)] flex flex-col overflow-hidden">
          {/* Tabs at top */}
          <div className="flex items-center gap-1 p-2 border-b border-[#CCD0D5] flex-shrink-0 bg-[#F0F2F5]">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 font-medium text-sm rounded-lg transition-all duration-200 ${
                activeTab === 'chat'
                  ? 'bg-[#1877F2] text-white shadow-md'
                  : 'text-[#65676B] hover:text-[#050505] hover:bg-white'
              }`}
            >
              Chat
            </button>
            {itinerary && (
              <button
                onClick={() => setActiveTab('itinerary')}
                className={`px-4 py-2 font-medium text-sm rounded-lg transition-all duration-200 ${
                  activeTab === 'itinerary'
                    ? 'bg-[#1877F2] text-white shadow-md'
                    : 'text-[#65676B] hover:text-[#050505] hover:bg-white'
                }`}
              >
                Itinerary
              </button>
            )}
            {itinerary && (
              <button
                onClick={() => setActiveTab('sources')}
                className={`px-4 py-2 font-medium text-sm rounded-lg transition-all duration-200 ${
                  activeTab === 'sources'
                    ? 'bg-[#1877F2] text-white shadow-md'
                    : 'text-[#65676B] hover:text-[#050505] hover:bg-white'
                }`}
              >
                Sources {sources && sources.length > 0 && `(${sources.length})`}
              </button>
            )}
          </div>
          
          {/* Content Area - switches based on active tab */}
          <div 
            ref={messagesContainerRef}
            className="flex-1 p-4 space-y-4 min-h-0 overflow-y-auto scrollbar-thin"
          >
            {/* Chat Tab Content */}
            {activeTab === 'chat' && (
              <>
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center py-12 animate-fade-in">
                    <div className="w-16 h-16 bg-[#1877F2] rounded-2xl flex items-center justify-center mb-4 shadow-lg">
                      <span className="text-3xl">✈️</span>
                    </div>
                    <h3 className="text-xl font-semibold text-[#050505] mb-2">Start Planning Your Trip!</h3>
                    <p className="text-[#65676B] max-w-md">Ask me anything about your travel plans. I can help you create a personalized itinerary.</p>
                  </div>
                )}
                
                {messages.map((message, idx) => {
                  const isLastMessage = idx === messages.length - 1;
                  const isClarifying = isLastMessage && isClarifyingQuestion;
                  
                  return (
                    <div
                      key={idx}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                          message.role === 'user'
                            ? 'message-user'
                            : isClarifying
                            ? 'bg-amber-50 border-2 border-amber-300 text-[#050505]'
                            : 'message-assistant'
                        }`}
                      >
                        {isClarifying && (
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs font-semibold text-amber-700 bg-amber-200 px-2 py-1 rounded-full">
                              💡 Clarifying Question
                            </span>
                          </div>
                        )}
                        <p className="whitespace-pre-wrap break-words leading-relaxed">{message.content}</p>
                        {message.timestamp && (
                          <p className={`text-xs mt-2 ${
                            message.role === 'user' ? 'text-white/80' : 'text-[#65676B]'
                          }`}>
                            {new Date(message.timestamp).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
                
                {/* Live transcript display */}
                {liveTranscript && (
                  <div className="flex justify-start animate-fade-in">
                    <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-[#E4E6EB] border-2 border-[#1877F2]">
                      <p className="text-xs text-[#1877F2] mb-1 font-semibold flex items-center gap-1">
                        <span className="w-2 h-2 bg-[#1877F2] rounded-full animate-pulse"></span>
                        Listening...
                      </p>
                      <p className="text-[#050505] italic">{liveTranscript}</p>
                    </div>
                  </div>
                )}
                
                {/* Processing indicator */}
                {isProcessing && (
                  <div className="flex justify-start animate-fade-in">
                    <div className="bg-white rounded-2xl px-4 py-3 border border-[#CCD0D5] shadow-md">
                      <div className="flex items-center gap-3">
                        <div className="w-5 h-5 border-2 border-[#1877F2] border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-sm text-[#65676B] font-medium">Processing your request...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Invisible element for auto-scroll */}
                <div ref={messagesEndRef} />
              </>
            )}

            {/* Itinerary Tab Content */}
            {activeTab === 'itinerary' && itinerary && (
              <div className="space-y-4">
                <ItineraryView 
                  itinerary={itinerary}
                  onExplainActivity={handleExplainActivity}
                  onGeneratePDF={handleGeneratePDF}
                  isGeneratingPDF={isGeneratingPDF}
                />
                {currentExplanation && (
                  <div className="mt-4 animate-fade-in">
                    <ExplanationPanel explanation={currentExplanation} sources={explanationSources} />
                  </div>
                )}
                {pdfUrl && (
                  <div className="mt-4 p-4 bg-green-50 border-2 border-green-200 rounded-lg animate-fade-in">
                    <p className="text-sm text-green-800 font-medium mb-2">✅ PDF generated successfully!</p>
                    <a
                      href={pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-green-600 hover:underline font-medium"
                    >
                      Open PDF →
                    </a>
                  </div>
                )}
                <div className="pt-4 border-t border-[#CCD0D5]">
                  <button
                    onClick={() => handleExplain('Why did you create this itinerary?')}
                    disabled={!sessionId || isProcessing}
                    className="btn-primary w-full text-sm"
                  >
                    Explain Itinerary
                  </button>
                </div>
              </div>
            )}

            {/* Sources Tab Content */}
            {activeTab === 'sources' && (
              <div>
                {sources && sources.length > 0 ? (
                  <SourcesView sources={sources} />
                ) : (
                  <div className="text-center text-[#65676B] py-12">
                    <div className="w-12 h-12 bg-[#E4E6EB] rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-2xl">📚</span>
                    </div>
                    <p className="font-medium mb-1">No sources available yet</p>
                    <p className="text-sm text-[#65676B]">Sources will appear after planning starts</p>
                  </div>
                )}
              </div>
            )}

            {/* Empty state for itinerary tab when no itinerary */}
            {!itinerary && activeTab === 'itinerary' && (
              <div className="text-center text-[#65676B] py-12">
                <div className="w-12 h-12 bg-[#E4E6EB] rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">🗺️</span>
                </div>
                <p className="font-medium mb-1">No itinerary yet</p>
                <p className="text-sm text-[#65676B]">Start planning to see your itinerary here</p>
              </div>
            )}
          </div>
          
          {/* Input Section at Bottom - Always visible */}
          <div className="border-t border-[#CCD0D5] bg-[#F0F2F5] p-4 flex-shrink-0">
            {/* Error Display */}
            {error && (
              <div className="mb-3 p-3 bg-red-50 border-2 border-red-200 rounded-lg animate-fade-in">
                <p className="text-sm text-red-800 font-medium flex items-center gap-2">
                  <span>⚠️</span>
                  {error}
                </p>
              </div>
            )}
            
            {/* Text Input */}
            <div className="mb-3">
              <TextInput 
                onSendMessage={handleTextMessage} 
                disabled={isProcessing}
                placeholder="Type your message or ask a question..."
              />
            </div>
            
            {/* Voice Input Option */}
            <div className="flex flex-col items-center gap-2">
              <div className="flex items-center justify-center gap-4 w-full">
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[#CCD0D5] to-transparent"></div>
                <span className="text-xs font-medium text-[#65676B] uppercase tracking-wider">or</span>
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[#CCD0D5] to-transparent"></div>
              </div>
              <div className="flex items-center gap-3">
                <VoiceInput 
                  onTranscript={handleTranscript} 
                  onInterimTranscript={handleInterimTranscript}
                  disabled={isProcessing}
                />
                {showVoicePrompt && !isProcessing && (
                  <p className="text-sm text-[#1877F2] font-medium animate-pulse">
                    💬 Click to speak
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function TravelAssistantPage() {
  return (
    <ConversationProvider>
      <TravelAssistantContent />
    </ConversationProvider>
  );
}
