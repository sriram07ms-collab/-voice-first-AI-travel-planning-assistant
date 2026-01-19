/**
 * Main Page Component
 * Travel Planning Assistant main interface.
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
    setLiveTranscript(''); // Clear live transcript when final text is received
    setShowVoicePrompt(false); // Hide prompt while processing
    // Use sendMessage from context with 'voice' input method (will trigger TTS response)
    await sendMessage(text, 'voice');
    // Show prompt for next input after response (with a small delay for TTS)
    setTimeout(() => {
      setShowVoicePrompt(true);
    }, 2000); // Show prompt 2 seconds after response
  };

  const handleInterimTranscript = (text: string) => {
    setLiveTranscript(text);
  };

  const handleTextMessage = async (text: string) => {
    setLiveTranscript(''); // Clear live transcript
    // Use sendMessage from context with 'text' input method (text-only response, no TTS)
    await sendMessage(text, 'text');
  };

  const handleExplain = async (question: string) => {
    if (!sessionId) {
      setError('Please start a conversation first');
      return;
    }

    try {
      // Clear previous error to allow re-clicking
      setError(null);
      
      // If question doesn't contain a POI name, try to extract from itinerary
      let finalQuestion = question;
      if (itinerary && !question.toLowerCase().includes('why') && !question.toLowerCase().includes('explain')) {
        // If it's just an activity name, format as a proper question
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
      // Clear explanation on error so user can try again
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

    // Prompt for email if not provided
    let email = userEmail;
    if (!email) {
      email = prompt('Please enter your email address to receive the PDF:');
      if (!email) {
        return; // User cancelled
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
        // Add success message directly to chat (no API call needed)
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

  // Check if last message is a clarifying question
  const lastMessage = messages[messages.length - 1];
  const isClarifyingQuestion = lastMessage?.role === 'assistant' && 
    messages.length > 0 &&
    itinerary === null; // If no itinerary yet, likely a clarifying question

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Voice-First Travel Assistant</h1>
            <p className="text-sm text-gray-600 mt-1">Plan your trip with text or voice</p>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={enableTTS}
                onChange={(e) => setEnableTTS(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span>Enable Voice Responses</span>
            </label>
            {sessionId && (
              <button
                onClick={clearConversation}
                className="px-3 py-1.5 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors text-sm"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 flex max-w-7xl mx-auto w-full px-4 py-6 gap-6 flex-col lg:flex-row">
        {/* Left Sidebar - Chat */}
        <div className="flex-1 flex flex-col min-w-0 lg:min-w-[500px]">
          {/* Chat Messages */}
          <div className="flex-1 bg-white rounded-lg shadow-sm p-4 mb-4 overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Conversation</h2>
              <div className="flex items-center gap-2">
                {sources && sources.length > 0 && (
                  <span className="text-xs text-gray-500 bg-blue-50 px-2 py-1 rounded">
                    {sources.length} source{sources.length > 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto mb-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 py-12">
                  <p className="mb-2">Start planning your trip!</p>
                  <p className="text-sm">Type a message or use voice input below.</p>
                </div>
              )}
              
              {messages.map((message, idx) => {
                const isLastMessage = idx === messages.length - 1;
                const isClarifying = isLastMessage && isClarifyingQuestion;
                
                return (
                  <div
                    key={idx}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg p-4 ${
                        message.role === 'user'
                          ? 'bg-blue-500 text-white'
                          : isClarifying
                          ? 'bg-yellow-50 border-2 border-yellow-300 text-gray-900'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      {isClarifying && (
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-semibold text-yellow-700 bg-yellow-200 px-2 py-1 rounded">
                            Clarifying Question
                          </span>
                        </div>
                      )}
                      <p className="whitespace-pre-wrap break-words">{message.content}</p>
                      {message.timestamp && (
                        <p className={`text-xs mt-2 ${
                          message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
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
                <div className="flex justify-start">
                  <div className="max-w-[85%] rounded-lg p-4 bg-blue-50 border border-blue-200">
                    <p className="text-xs text-blue-600 mb-1 font-medium">Listening...</p>
                    <p className="text-gray-700 italic">{liveTranscript}</p>
                  </div>
                </div>
              )}
              
              {/* Processing indicator */}
              {isProcessing && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-sm text-gray-600">Processing...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Error Display */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
          </div>

          {/* Input Section */}
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="mb-3">
              <TextInput 
                onSendMessage={handleTextMessage} 
                disabled={isProcessing}
                placeholder="Type your message or ask a question..."
              />
            </div>
            <div className="flex flex-col items-center gap-3">
              <div className="flex items-center justify-center gap-4">
                <div className="text-sm text-gray-500">or</div>
                <VoiceInput 
                  onTranscript={handleTranscript} 
                  onInterimTranscript={handleInterimTranscript}
                  disabled={isProcessing}
                />
              </div>
              {showVoicePrompt && !isProcessing && (
                <div className="text-sm text-blue-600 animate-pulse">
                  💬 Click the microphone to provide your next input
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar - Itinerary & Sources */}
        <div className="w-full lg:w-96 flex flex-col gap-4 mt-6 lg:mt-0">
          {/* Tabs */}
          <div className="flex gap-2 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 font-medium text-sm transition-colors ${
                activeTab === 'chat'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Chat
            </button>
            {itinerary && (
              <button
                onClick={() => setActiveTab('itinerary')}
                className={`px-4 py-2 font-medium text-sm transition-colors ${
                  activeTab === 'itinerary'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Itinerary
              </button>
            )}
            {itinerary && (sources && sources.length > 0 ? (
              <button
                onClick={() => setActiveTab('sources')}
                className={`px-4 py-2 font-medium text-sm transition-colors ${
                  activeTab === 'sources'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Sources ({sources.length})
              </button>
            ) : (
              <button
                onClick={() => setActiveTab('sources')}
                className={`px-4 py-2 font-medium text-sm transition-colors ${
                  activeTab === 'sources'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="No sources available yet"
              >
                Sources (0)
              </button>
            ))}
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'itinerary' && itinerary && (
              <div className="bg-white rounded-lg shadow-sm p-4">
                <ItineraryView 
                  itinerary={itinerary}
                  onExplainActivity={handleExplainActivity}
                  onGeneratePDF={handleGeneratePDF}
                  isGeneratingPDF={isGeneratingPDF}
                />
                {currentExplanation && (
                  <div className="mt-4">
                    <ExplanationPanel explanation={currentExplanation} sources={explanationSources} />
                  </div>
                )}
                {pdfUrl && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-800 mb-2">PDF generated successfully!</p>
                    <a
                      href={pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-green-600 hover:underline"
                    >
                      Open PDF in new tab
                    </a>
                  </div>
                )}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => handleExplain('Why did you create this itinerary?')}
                    disabled={!sessionId || isProcessing}
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed mb-2"
                  >
                    Explain Itinerary
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'sources' && (
              <div className="bg-white rounded-lg shadow-sm p-4">
                {sources && sources.length > 0 ? (
                  <SourcesView sources={sources} />
                ) : (
                  <div className="text-center text-gray-500 text-sm py-8">
                    <p>No sources available yet.</p>
                    <p className="mt-2">Sources will appear after planning starts.</p>
                    <p className="mt-2 text-xs text-gray-400">
                      Sources include POI references and travel guide citations.
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'chat' && (
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="text-center text-gray-500 text-sm py-8">
                  <p>Chat messages appear in the left panel.</p>
                  <p className="mt-2">Use the tabs above to view itinerary and sources.</p>
                </div>
              </div>
            )}

            {!itinerary && activeTab === 'itinerary' && (
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="text-center text-gray-500 text-sm py-8">
                  <p>No itinerary yet.</p>
                  <p className="mt-2">Start planning to see your itinerary here.</p>
                </div>
              </div>
            )}
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
