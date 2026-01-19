/**
 * Sources View Component
 * Displays citations and sources for the itinerary.
 */

'use client';

import React, { useState } from 'react';
import type { SourcesViewProps, Source } from '../types';

export default function SourcesView({ sources }: SourcesViewProps) {
  const [expandedSource, setExpandedSource] = useState<string | null>(null);

  if (!sources || sources.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        No sources available.
      </div>
    );
  }

  const toggleSource = (sourceId: string) => {
    setExpandedSource(expandedSource === sourceId ? null : sourceId);
  };

  const groupSourcesByType = () => {
    const grouped: Record<string, Source[]> = {};
    sources.forEach((source) => {
      const type = source.type || 'other';
      if (!grouped[type]) {
        grouped[type] = [];
      }
      grouped[type].push(source);
    });
    return grouped;
  };

  const getSourceTypeLabel = (type: string) => {
    switch (type) {
      case 'openstreetmap':
        return 'OpenStreetMap';
      case 'google_places':
        return 'Google Places';
      case 'wikivoyage':
        return 'Wikivoyage';
      default:
        return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ');
    }
  };

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'openstreetmap':
        return '🗺️';
      case 'google_places':
        return '📍';
      case 'wikivoyage':
        return '📖';
      default:
        return '📄';
    }
  };

  const groupedSources = groupSourcesByType();

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Sources & Citations</h3>
      
      <div className="space-y-4">
        {Object.entries(groupedSources).map(([type, typeSources]) => (
          <div key={type} className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <span>{getSourceIcon(type)}</span>
              {getSourceTypeLabel(type)} ({typeSources.length})
            </h4>
            
            <div className="space-y-2">
              {typeSources.map((source, idx) => {
                const sourceId = `${type}-${idx}`;
                const isExpanded = expandedSource === sourceId;
                
                return (
                  <div
                    key={sourceId}
                    className="bg-gray-50 rounded p-3 hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {source.poi && (
                          <p className="font-medium text-gray-900">{source.poi}</p>
                        )}
                        {source.topic && (
                          <p className="font-medium text-gray-900">{source.topic}</p>
                        )}
                        {source.source_id && (
                          <p className="text-xs text-gray-600 mt-1">ID: {source.source_id}</p>
                        )}
                        {source.url && (
                          <div className="mt-2">
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:text-blue-800 underline break-all"
                            >
                              {source.url}
                            </a>
                          </div>
                        )}
                      </div>
                      
                      {source.snippet && (
                        <button
                          onClick={() => toggleSource(sourceId)}
                          className="ml-4 text-gray-400 hover:text-gray-600"
                        >
                          {isExpanded ? (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          )}
                        </button>
                      )}
                    </div>
                    
                    {isExpanded && source.snippet && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-sm text-gray-700 italic">"{source.snippet}"</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
