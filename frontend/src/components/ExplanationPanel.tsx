/**
 * Explanation Panel Component
 * Displays explanations with citations.
 */

'use client';

import React, { useState } from 'react';
import type { ExplanationPanelProps, Source } from '../types';

export default function ExplanationPanel({ explanation, sources }: ExplanationPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!explanation) {
    return null;
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-blue-50 rounded-lg border border-blue-200">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Explanation
        </h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-gray-400 hover:text-gray-600"
        >
          {isExpanded ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </button>
      </div>

      {isExpanded && (
        <>
          <div className="prose prose-sm max-w-none mb-4">
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{explanation}</p>
          </div>

          {sources && sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-blue-200">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">Sources:</h4>
              <ul className="space-y-2">
                {sources.map((source, idx) => (
                  <li key={idx} className="text-sm">
                    {source.url ? (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        {source.topic || source.poi || `Source ${idx + 1}`}
                      </a>
                    ) : (
                      <span className="text-gray-600">
                        {source.topic || source.poi || `Source ${idx + 1}`}
                      </span>
                    )}
                    {source.source_id && (
                      <span className="text-gray-500 ml-2">({source.source_id})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
