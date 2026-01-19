/**
 * Itinerary View Component
 * Displays day-wise itinerary with time blocks.
 */

'use client';

import React, { useState } from 'react';
import type { ItineraryViewProps, Activity, DayItinerary } from '../types';

export default function ItineraryView({ 
  itinerary, 
  onExplainActivity,
  onGeneratePDF,
  isGeneratingPDF = false
}: ItineraryViewProps) {
  const [selectedDay, setSelectedDay] = useState(1);
  const [expandedActivities, setExpandedActivities] = useState<Set<string>>(new Set());

  if (!itinerary) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>No itinerary available. Start planning your trip!</p>
      </div>
    );
  }

  const durationDays = itinerary.duration_days || 1;
  const days = Array.from({ length: durationDays }, (_, i) => i + 1);
  
  // Format date for display
  const formatDate = (dateStr: string | undefined, dayNum: number): string => {
    if (dateStr) {
      try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          year: 'numeric' 
        });
      } catch (e) {
        return `Day ${dayNum}`;
      }
    }
    return `Day ${dayNum}`;
  };
  
  // Get date for a specific day
  const getDayDate = (dayNum: number): string => {
    const travelDates = itinerary.travel_dates;
    if (travelDates && Array.isArray(travelDates) && travelDates.length >= dayNum) {
      return formatDate(travelDates[dayNum - 1], dayNum);
    }
    return `Day ${dayNum}`;
  };

  const toggleActivity = (activityId: string) => {
    setExpandedActivities((prev) => {
      const next = new Set(prev);
      if (next.has(activityId)) {
        next.delete(activityId);
      } else {
        next.add(activityId);
      }
      return next;
    });
  };

  const getDayItinerary = (dayNum: number): DayItinerary | null => {
    const dayKey = `day_${dayNum}` as keyof typeof itinerary;
    return itinerary[dayKey] as DayItinerary | null;
  };

  const getPaceColor = (pace?: string) => {
    switch (pace?.toLowerCase()) {
      case 'relaxed':
        return 'bg-green-100 text-green-800';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800';
      case 'fast':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const renderActivity = (activity: Activity, activityId: string) => {
    const isExpanded = expandedActivities.has(activityId);
    
    return (
      <div
        key={activityId}
        className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-3 hover:shadow-md transition-shadow"
      >
        <div
          className="flex items-start justify-between cursor-pointer"
          onClick={() => toggleActivity(activityId)}
        >
          <div className="flex-1">
            <h4 className="font-semibold text-lg text-gray-900">{activity.activity}</h4>
            <p className="text-sm text-gray-600 mt-1">{activity.time}</p>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <span title="Time spent at this activity">⏱️ Duration: {activity.duration_minutes} min</span>
              {activity.travel_time_from_previous && activity.travel_time_from_previous > 0 && (
                <span title="Travel time from previous activity to this one">🚶 Travel: {activity.travel_time_from_previous} min</span>
              )}
              {activity.category && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                  {activity.category}
                </span>
              )}
            </div>
          </div>
          <button className="ml-4 text-gray-400 hover:text-gray-600">
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
          <div className="mt-3 pt-3 border-t border-gray-200">
            {activity.description && (
              <p className="text-sm text-gray-700 mb-2">{activity.description}</p>
            )}
            {activity.location && (
              <p className="text-xs text-gray-500">
                Location: {activity.location.lat.toFixed(4)}, {activity.location.lon.toFixed(4)}
              </p>
            )}
            {activity.source_id && (
              <p className="text-xs text-gray-500 mt-1">
                Source: {activity.source_id}
              </p>
            )}
            {activity.note && (
              <p className="text-xs text-blue-600 mt-2 italic">{activity.note}</p>
            )}
            {onExplainActivity && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onExplainActivity(activity.activity);
                }}
                className="mt-2 px-3 py-1.5 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
              >
                Explain this activity
              </button>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderTimeBlock = (title: string, activities: Activity[], dayNum: number, timeBlock: string) => {
    if (activities.length === 0) {
      return null;
    }

    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
          {title}
        </h3>
        <div className="space-y-2">
          {activities.map((activity, idx) => {
            const activityId = `day-${dayNum}-${timeBlock}-${idx}`;
            return renderActivity(activity, activityId);
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6 pb-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Trip to {itinerary.city}
        </h2>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>{durationDays} {durationDays === 1 ? 'day' : 'days'}</span>
          {itinerary.pace && (
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPaceColor(itinerary.pace)}`}>
              {itinerary.pace} pace
            </span>
          )}
          {itinerary.interests && itinerary.interests.length > 0 && (
            <span>Interests: {itinerary.interests.join(', ')}</span>
          )}
          {itinerary.total_travel_time && (
            <span title="Total time spent traveling between activities across all days">🚶 Total travel time: {itinerary.total_travel_time} min</span>
          )}
        </div>
        {onGeneratePDF && (
          <div className="mt-4">
            <button
              onClick={onGeneratePDF}
              disabled={isGeneratingPDF}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isGeneratingPDF ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Generating PDF...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Generate PDF & Send Email
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Day Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {days.map((dayNum) => (
          <button
            key={dayNum}
            onClick={() => setSelectedDay(dayNum)}
            className={`
              px-6 py-3 font-medium text-sm transition-colors
              ${selectedDay === dayNum
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            {getDayDate(dayNum)}
          </button>
        ))}
      </div>

      {/* Day Content */}
      {days.map((dayNum) => {
        if (selectedDay !== dayNum) return null;
        
        const dayItinerary = getDayItinerary(dayNum);
        if (!dayItinerary) {
          return (
            <div key={dayNum} className="text-center text-gray-500 py-8">
              No activities planned for {getDayDate(dayNum)}
            </div>
          );
        }

        return (
          <div key={dayNum} className="space-y-6">
            {renderTimeBlock('Morning', dayItinerary.morning?.activities || [], dayNum, 'morning')}
            {renderTimeBlock('Afternoon', dayItinerary.afternoon?.activities || [], dayNum, 'afternoon')}
            {renderTimeBlock('Evening', dayItinerary.evening?.activities || [], dayNum, 'evening')}
            
            {dayItinerary.morning?.activities.length === 0 &&
             dayItinerary.afternoon?.activities.length === 0 &&
             dayItinerary.evening?.activities.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                No activities planned for {getDayDate(dayNum)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
