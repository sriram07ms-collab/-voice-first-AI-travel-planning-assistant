/**
 * Main Page Component
 * Travel Planning Assistant main interface with modern UI/UX.
 */

'use client';

import React, { useState } from 'react';
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
      {/* Modern Header with Gradient */}
      <header className="glass border-b border-slate-200/50 sticky top-0 z-50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold gradient-text mb-1">
                ✈️ Voice-First Travel Assistant
              </h1>
              <p className="text-slate-600 text-sm">Plan your perfect trip with AI-powered assistance</p>
            </div>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer group">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={enableTTS}
                    onChange={(e) => setEnableTTS(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`w-11 h-6 rounded-full transition-colors duration-200 ${
                    enableTTS ? 'bg-blue-600' : 'bg-slate-300'
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-180px)] lg:h-[calc(100vh-140px)]">
          {/* Left Panel - Chat */}
          <div className="lg:col-span-2 flex flex-col gap-4 min-h-0">
            {/* Chat Messages Card */}
            <div className="card flex-1 flex flex-col min-h-0 overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <h2 className="text-lg font-semibold text-slate-800">Conversation</h2>
                </div>
                {sources && sources.length > 0 && (
                  <span className="text-xs font-medium text-slate-600 bg-blue-50 px-3 py-1 rounded-full border border-blue-200">
                    {sources.length} source{sources.length > 1 ? 's' : ''}
                  </span>
                )}
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center py-12 animate-fade-in">
                    <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg">
                      <span className="text-3xl">✈️</span>
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">Start Planning Your Trip!</h3>
                    <p className="text-slate-600 max-w-md">Ask me anything about your travel plans. I can help you create a personalized itinerary.</p>
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
                            ? 'bg-amber-50 border-2 border-amber-300 text-slate-800'
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
                            message.role === 'user' ? 'text-blue-100' : 'text-slate-500'
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
                    <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-blue-50 border-2 border-blue-200">
                      <p className="text-xs text-blue-600 mb-1 font-semibold flex items-center gap-1">
                        <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                        Listening...
                      </p>
                      <p className="text-slate-700 italic">{liveTranscript}</p>
                    </div>
                  </div>
                )}
                
                {/* Processing indicator */}
                {isProcessing && (
                  <div className="flex justify-start animate-fade-in">
                    <div className="bg-white rounded-2xl px-4 py-3 border border-slate-200 shadow-md">
                      <div className="flex items-center gap-3">
                        <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-sm text-slate-600 font-medium">Processing your request...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Error Display */}
              {error && (
                <div className="mx-4 mb-4 p-3 bg-red-50 border-2 border-red-200 rounded-lg animate-fade-in">
                  <p className="text-sm text-red-800 font-medium flex items-center gap-2">
                    <span>⚠️</span>
                    {error}
                  </p>
                </div>
              )}
            </div>

            {/* Input Section */}
            <div className="card p-4">
              <div className="mb-3">
                <TextInput 
                  onSendMessage={handleTextMessage} 
                  disabled={isProcessing}
                  placeholder="Type your message or ask a question..."
                />
              </div>
              <div className="flex flex-col items-center gap-3">
                <div className="flex items-center justify-center gap-4 w-full">
                  <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-300 to-transparent"></div>
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">or</span>
                  <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-300 to-transparent"></div>
                </div>
                <div className="flex items-center gap-3">
                  <VoiceInput 
                    onTranscript={handleTranscript} 
                    onInterimTranscript={handleInterimTranscript}
                    disabled={isProcessing}
                  />
                  {showVoicePrompt && !isProcessing && (
                    <p className="text-sm text-blue-600 font-medium animate-pulse">
                      💬 Click to speak
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel - Itinerary & Sources */}
          <div className="lg:col-span-1 flex flex-col gap-4 min-h-0">
            {/* Tabs */}
            <div className="card p-1 flex gap-1">
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex-1 px-4 py-2 font-medium text-sm rounded-lg transition-all duration-200 ${
                  activeTab === 'chat'
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
                }`}
              >
                Chat
              </button>
              {itinerary && (
                <button
                  onClick={() => setActiveTab('itinerary')}
                  className={`flex-1 px-4 py-2 font-medium text-sm rounded-lg transition-all duration-200 ${
                    activeTab === 'itinerary'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                      : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
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
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                      : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
                  }`}
                >
                  Sources {sources && sources.length > 0 && `(${sources.length})`}
                </button>
              )}
            </div>

            {/* Content Area */}
            <div className="card flex-1 overflow-y-auto scrollbar-thin">
              <div className="p-4">
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
                    <div className="pt-4 border-t border-slate-200">
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

                {activeTab === 'sources' && (
                  <div>
                    {sources && sources.length > 0 ? (
                      <SourcesView sources={sources} />
                    ) : (
                      <div className="text-center text-slate-500 py-12">
                        <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <span className="text-2xl">📚</span>
                        </div>
                        <p className="font-medium mb-1">No sources available yet</p>
                        <p className="text-sm text-slate-400">Sources will appear after planning starts</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'chat' && (
                  <div className="text-center text-slate-500 py-12">
                    <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-2xl">💬</span>
                    </div>
                    <p className="font-medium mb-1">Chat messages appear in the left panel</p>
                    <p className="text-sm text-slate-400">Use the tabs above to view itinerary and sources</p>
                  </div>
                )}

                {!itinerary && activeTab === 'itinerary' && (
                  <div className="text-center text-slate-500 py-12">
                    <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-2xl">🗺️</span>
                    </div>
                    <p className="font-medium mb-1">No itinerary yet</p>
                    <p className="text-sm text-slate-400">Start planning to see your itinerary here</p>
                  </div>
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
