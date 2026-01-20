# Test Guide - Voice-First AI Travel Planning Assistant

This document provides comprehensive test scenarios covering all workflows, edge cases, and expected outputs for the Voice-First AI Travel Planning Assistant.

## 📋 Table of Contents

- [Final Product Output](#final-product-output)
- [Test Scenarios](#test-scenarios)
  - [Scenario 1: Complete Trip Planning (No Clarifying Questions)](#scenario-1-complete-trip-planning-no-clarifying-questions)
  - [Scenario 2: Trip Planning with Clarifying Questions](#scenario-2-trip-planning-with-clarifying-questions)
  - [Scenario 3: Edit - Change Pace](#scenario-3-edit---change-pace)
  - [Scenario 4: Edit - Swap Activity](#scenario-4-edit---swap-activity)
  - [Scenario 5: Edit - Add Activity](#scenario-5-edit---add-activity)
  - [Scenario 6: Edit - Reduce Travel Time](#scenario-6-edit---reduce-travel-time)
  - [Scenario 7: Explanation - Why POI Selected](#scenario-7-explanation---why-poi-selected)
  - [Scenario 8: Explanation - Is Plan Feasible?](#scenario-8-explanation---is-plan-feasible)
  - [Scenario 9: Explanation - Weather Alternative](#scenario-9-explanation---weather-alternative)
  - [Scenario 10: Explanation - Why Timing](#scenario-10-explanation---why-timing)
  - [Scenario 11: Error - City Not Found](#scenario-11-error---city-not-found)
  - [Scenario 12: Error - Missing Data](#scenario-12-error---missing-data)
  - [Scenario 13: Evaluation - Feasibility Violation](#scenario-13-evaluation---feasibility-violation)
  - [Scenario 14: Evaluation - Edit Correctness Violation](#scenario-14-evaluation---edit-correctness-violation)
  - [Scenario 15: PDF Generation](#scenario-15-pdf-generation)
  - [Scenario 16: Maximum Clarifying Questions Reached](#scenario-16-maximum-clarifying-questions-reached)
  - [Scenario 17: Voice Input with Errors](#scenario-17-voice-input-with-errors)
  - [Scenario 18: Multiple Edits in Sequence](#scenario-18-multiple-edits-in-sequence)
  - [Scenario 19: Explanation - Missing Source](#scenario-19-explanation---missing-source)
  - [Scenario 20: Complete Conversation Flow](#scenario-20-complete-conversation-flow)

---

## Final Product Output

### User Interface
When fully implemented, users will see:
- **Web Application** with:
  - Microphone button for voice input
  - Live transcript panel showing conversation
  - Itinerary display with Day 1/2/3 tabs
  - Morning/Afternoon/Evening time blocks
  - Travel times between activities
  - Sources/References section with clickable links
  - Explanation panel for "why" questions
  - PDF download button

### Backend API Responses
- Structured JSON responses with itinerary data
- Citations and source references
- Evaluation results (feasibility, grounding, edit correctness)
- Error messages when appropriate

---

## Test Scenarios

### Scenario 1: Complete Trip Planning (No Clarifying Questions)

**Input (Voice/Text):**
```
"Plan a 3-day trip to Jaipur next weekend. I like food and culture, relaxed pace."
```

**System Flow:**
1. Intent Classification: `PLAN_TRIP`
2. Entity Extraction: city="Jaipur", duration=3, interests=["food", "culture"], pace="relaxed"
3. No clarifying questions needed (all information present)
4. POI Search MCP → Returns ranked POIs
5. RAG System → Retrieves Wikivoyage tips
6. Itinerary Builder MCP → Creates structured plan
7. Feasibility Evaluator → Validates plan
8. Grounding Evaluator → Checks all sources

**Expected Output:**
```json
{
  "status": "success",
  "itinerary": {
    "city": "Jaipur",
    "duration_days": 3,
    "pace": "relaxed",
    "day_1": {
      "morning": [
        {
          "activity": "Hawa Mahal",
          "time": "09:00 - 10:30",
          "duration_minutes": 90,
          "location": {"lat": 26.9240, "lon": 75.8266},
          "category": "historical",
          "source_id": "way:123456",
          "description": "Palace of Winds, iconic pink sandstone structure"
        }
      ],
      "afternoon": [
        {
          "activity": "City Palace",
          "time": "11:00 - 13:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 15,
          "location": {"lat": 26.9255, "lon": 75.8236},
          "source_id": "way:123457"
        },
        {
          "activity": "Lunch at Laxmi Misthan Bhandar",
          "time": "13:00 - 14:00",
          "duration_minutes": 60,
          "travel_time_from_previous": 5,
          "category": "restaurant",
          "source_id": "node:789012"
        }
      ],
      "evening": [
        {
          "activity": "Jantar Mantar",
          "time": "16:00 - 17:30",
          "duration_minutes": 90,
          "travel_time_from_previous": 10,
          "source_id": "way:123458"
        }
      ]
    },
    "day_2": {
      "morning": [
        {
          "activity": "Amber Fort",
          "time": "09:00 - 12:00",
          "duration_minutes": 180,
          "travel_time_from_previous": 30,
          "source_id": "way:123459"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Rawat Mishthan Bhandar",
          "time": "12:30 - 14:00",
          "duration_minutes": 90,
          "travel_time_from_previous": 5,
          "source_id": "node:789013"
        }
      ],
      "evening": [
        {
          "activity": "Johari Bazaar",
          "time": "16:00 - 18:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 20,
          "source_id": "way:123460"
        }
      ]
    },
    "day_3": {
      "morning": [
        {
          "activity": "Nahargarh Fort",
          "time": "09:00 - 11:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 25,
          "source_id": "way:123461"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Chokhi Dhani",
          "time": "12:00 - 14:30",
          "duration_minutes": 150,
          "travel_time_from_previous": 30,
          "source_id": "node:789014"
        }
      ],
      "evening": [
        {
          "activity": "Albert Hall Museum",
          "time": "16:00 - 17:30",
          "duration_minutes": 90,
          "travel_time_from_previous": 15,
          "source_id": "way:123462"
        }
      ]
    }
  },
  "total_travel_time": 180,
  "sources": [
    {
      "type": "openstreetmap",
      "poi": "Hawa Mahal",
      "source_id": "way:123456",
      "url": "https://www.openstreetmap.org/way/123456"
    },
    {
      "type": "openstreetmap",
      "poi": "City Palace",
      "source_id": "way:123457",
      "url": "https://www.openstreetmap.org/way/123457"
    },
    {
      "type": "wikivoyage",
      "topic": "Jaipur travel tips",
      "url": "https://en.wikivoyage.org/wiki/Jaipur",
      "section": "See"
    },
    {
      "type": "wikivoyage",
      "topic": "Jaipur food recommendations",
      "url": "https://en.wikivoyage.org/wiki/Jaipur#Eat",
      "section": "Eat"
    }
  ],
  "evaluation": {
    "feasibility": {
      "is_feasible": true,
      "score": 0.95,
      "violations": [],
      "warnings": []
    },
    "grounding": {
      "is_grounded": true,
      "score": 0.98,
      "all_pois_have_sources": true,
      "uncertain_data": []
    }
  },
  "explanation": "I've created a relaxed 3-day itinerary for Jaipur focusing on food and culture. Day 1 includes iconic historical sites grouped together to minimize travel time. Each day has 2-3 activities to maintain a relaxed pace."
}
```

**UI Display:**
- Itinerary shown in Day 1/2/3 tabs
- Each day shows Morning/Afternoon/Evening blocks
- Travel times between activities visible
- Sources section with clickable links
- Transcript shows conversation

---

### Scenario 2: Trip Planning with Clarifying Questions

**Input 1:**
```
"Plan a trip to Mumbai"
```

**System Response:**
```json
{
  "status": "clarifying",
  "question": "How many days would you like to spend in Mumbai?",
  "clarifying_questions_count": 1
}
```

**Input 2:**
```
"3 days"
```

**System Response:**
```json
{
  "status": "clarifying",
  "question": "What are your interests? For example, food, culture, shopping, nightlife?",
  "clarifying_questions_count": 2
}
```

**Input 3:**
```
"I like food and beaches"
```

**System Response:**
```json
{
  "status": "clarifying",
  "question": "What pace do you prefer? Relaxed, moderate, or fast?",
  "clarifying_questions_count": 3
}
```

**Input 4:**
```
"Moderate pace"
```

**System Response:**
```json
{
  "status": "success",
  "itinerary": {
    "city": "Mumbai",
    "duration_days": 3,
    "interests": ["food", "beaches"],
    "pace": "moderate",
    "day_1": {
      "morning": [
        {
          "activity": "Gateway of India",
          "time": "09:00 - 10:30",
          "duration_minutes": 90,
          "source_id": "way:234567"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Trishna",
          "time": "12:00 - 13:30",
          "duration_minutes": 90,
          "category": "restaurant",
          "source_id": "node:345678"
        },
        {
          "activity": "Colaba Causeway",
          "time": "14:00 - 16:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 10,
          "source_id": "way:234568"
        }
      ],
      "evening": [
        {
          "activity": "Marine Drive",
          "time": "17:00 - 19:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 15,
          "source_id": "way:234569"
        }
      ]
    },
    "day_2": {
      "morning": [
        {
          "activity": "Juhu Beach",
          "time": "08:00 - 10:00",
          "duration_minutes": 120,
          "source_id": "way:234570"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Bademiya",
          "time": "12:00 - 13:30",
          "duration_minutes": 90,
          "source_id": "node:345679"
        },
        {
          "activity": "Elephanta Caves",
          "time": "14:30 - 17:00",
          "duration_minutes": 150,
          "travel_time_from_previous": 45,
          "source_id": "way:234571"
        }
      ],
      "evening": [
        {
          "activity": "Dinner at The Table",
          "time": "19:00 - 21:00",
          "duration_minutes": 120,
          "source_id": "node:345680"
        }
      ]
    },
    "day_3": {
      "morning": [
        {
          "activity": "Chhatrapati Shivaji Terminus",
          "time": "09:00 - 10:30",
          "duration_minutes": 90,
          "source_id": "way:234572"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Britannia & Co.",
          "time": "12:00 - 13:30",
          "duration_minutes": 90,
          "source_id": "node:345681"
        },
        {
          "activity": "Chor Bazaar",
          "time": "14:00 - 16:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 20,
          "source_id": "way:234573"
        }
      ],
      "evening": [
        {
          "activity": "Chowpatty Beach",
          "time": "17:00 - 19:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 25,
          "source_id": "way:234574"
        }
      ]
    }
  },
  "sources": [
    {
      "type": "openstreetmap",
      "poi": "Gateway of India",
      "source_id": "way:234567",
      "url": "https://www.openstreetmap.org/way/234567"
    },
    {
      "type": "wikivoyage",
      "topic": "Mumbai travel guide",
      "url": "https://en.wikivoyage.org/wiki/Mumbai",
      "section": "See"
    }
  ],
  "evaluation": {
    "feasibility": {
      "is_feasible": true,
      "score": 0.92,
      "violations": [],
      "warnings": []
    },
    "grounding": {
      "is_grounded": true,
      "score": 0.97,
      "all_pois_have_sources": true,
      "uncertain_data": []
    }
  }
}
```

---

### Scenario 3: Edit - Change Pace

**Input:**
```
"Make Day 2 more relaxed"
```

**System Flow:**
1. Intent Classification: `EDIT_ITINERARY`
2. Entity Extraction: target_day=2, edit_type="CHANGE_PACE", new_pace="relaxed"
3. Extract Day 2 current itinerary
4. POI Search MCP → Find alternative relaxed activities
5. Itinerary Builder MCP → Rebuild Day 2 only
6. Edit Correctness Evaluator → Verify only Day 2 changed

**Expected Output:**
```json
{
  "status": "success",
  "edit_type": "CHANGE_PACE",
  "modified_section": "day_2",
  "itinerary": {
    "day_1": {
      // UNCHANGED - same as before
      "morning": [
        {
          "activity": "Hawa Mahal",
          "time": "09:00 - 10:30",
          "duration_minutes": 90,
          "source_id": "way:123456"
        }
      ],
      "afternoon": [
        {
          "activity": "City Palace",
          "time": "11:00 - 13:00",
          "duration_minutes": 120,
          "source_id": "way:123457"
        },
        {
          "activity": "Lunch at Laxmi Misthan Bhandar",
          "time": "13:00 - 14:00",
          "duration_minutes": 60,
          "source_id": "node:789012"
        }
      ],
      "evening": [
        {
          "activity": "Jantar Mantar",
          "time": "16:00 - 17:30",
          "duration_minutes": 90,
          "source_id": "way:123458"
        }
      ]
    },
    "day_2": {
      // MODIFIED - fewer activities, more time per activity
      "morning": [
        {
          "activity": "Amber Fort",
          "time": "09:00 - 12:30",
          "duration_minutes": 210,
          "travel_time_from_previous": 30,
          "source_id": "way:123459",
          "note": "Extended time for relaxed exploration"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Rawat Mishthan Bhandar",
          "time": "13:00 - 15:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 10,
          "source_id": "node:789013",
          "note": "Extended lunch break"
        }
      ],
      "evening": [
        {
          "activity": "Johari Bazaar",
          "time": "16:00 - 18:30",
          "duration_minutes": 150,
          "travel_time_from_previous": 20,
          "source_id": "way:123460",
          "note": "More time for shopping"
        }
      ]
    },
    "day_3": {
      // UNCHANGED - same as before
      "morning": [
        {
          "activity": "Nahargarh Fort",
          "time": "09:00 - 11:00",
          "duration_minutes": 120,
          "source_id": "way:123461"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Chokhi Dhani",
          "time": "12:00 - 14:30",
          "duration_minutes": 150,
          "source_id": "node:789014"
        }
      ],
      "evening": [
        {
          "activity": "Albert Hall Museum",
          "time": "16:00 - 17:30",
          "duration_minutes": 90,
          "source_id": "way:123462"
        }
      ]
    }
  },
  "evaluation": {
    "edit_correctness": {
      "is_correct": true,
      "modified_sections": ["day_2"],
      "unchanged_sections": ["day_1", "day_3"],
      "violations": []
    },
    "feasibility": {
      "is_feasible": true,
      "score": 0.96,
      "violations": [],
      "warnings": []
    }
  },
  "explanation": "I've made Day 2 more relaxed by reducing the number of activities from 4 to 3, and increasing the time allocated to each activity. Amber Fort now has 3.5 hours instead of 3 hours, lunch is extended to 2 hours, and shopping time increased. Day 1 and Day 3 remain unchanged."
}
```

---

### Scenario 4: Edit - Swap Activity

**Input:**
```
"Swap the Day 1 evening plan to something indoors"
```

**Expected Output:**
```json
{
  "status": "success",
  "edit_type": "SWAP_ACTIVITY",
  "modified_section": "day_1_evening",
  "itinerary": {
    "day_1": {
      "morning": [
        {
          "activity": "Hawa Mahal",
          "time": "09:00 - 10:30",
          "duration_minutes": 90,
          "source_id": "way:123456"
        }
      ],
      "afternoon": [
        {
          "activity": "City Palace",
          "time": "11:00 - 13:00",
          "duration_minutes": 120,
          "source_id": "way:123457"
        },
        {
          "activity": "Lunch at Laxmi Misthan Bhandar",
          "time": "13:00 - 14:00",
          "duration_minutes": 60,
          "source_id": "node:789012"
        }
      ],
      "evening": [
        {
          "activity": "Chhatrapati Shivaji Maharaj Vastu Sangrahalaya",
          "time": "16:00 - 18:00",
          "duration_minutes": 120,
          "category": "museum",
          "indoor": true,
          "source_id": "way:456789",
          "description": "Indoor museum with historical artifacts"
        }
      ]
    },
    "day_2": {
      // UNCHANGED
    },
    "day_3": {
      // UNCHANGED
    }
  },
  "evaluation": {
    "edit_correctness": {
      "is_correct": true,
      "modified_sections": ["day_1_evening"],
      "unchanged_sections": ["day_1_morning", "day_1_afternoon", "day_2", "day_3"],
      "violations": []
    }
  },
  "explanation": "I've replaced the outdoor evening activity (Jantar Mantar) with a visit to the museum, which is indoors. The rest of your itinerary remains the same."
}
```

---

### Scenario 5: Edit - Add Activity

**Input:**
```
"Add one famous local food place to Day 2"
```

**Expected Output:**
```json
{
  "status": "success",
  "edit_type": "ADD_ACTIVITY",
  "modified_section": "day_2",
  "itinerary": {
    "day_2": {
      "morning": [
        {
          "activity": "Amber Fort",
          "time": "09:00 - 12:00",
          "duration_minutes": 180,
          "source_id": "way:123459"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Rawat Mishthan Bhandar",
          "time": "12:30 - 14:00",
          "duration_minutes": 90,
          "source_id": "node:789013"
        },
        {
          "activity": "Bademiya Restaurant",
          "time": "14:00 - 15:30",
          "duration_minutes": 90,
          "category": "restaurant",
          "cuisine": "Mughlai",
          "source_id": "node:234567",
          "description": "Famous for kebabs and biryani"
        }
      ],
      "evening": [
        {
          "activity": "Johari Bazaar",
          "time": "16:00 - 18:00",
          "duration_minutes": 120,
          "source_id": "way:123460"
        }
      ]
    }
  },
  "evaluation": {
    "edit_correctness": {
      "is_correct": true,
      "modified_sections": ["day_2_afternoon"],
      "unchanged_sections": ["day_1", "day_3"],
      "violations": []
    },
    "feasibility": {
      "is_feasible": true,
      "score": 0.90,
      "warnings": ["Day 2 afternoon is now more packed"]
    }
  },
  "explanation": "I've added Bademiya Restaurant to Day 2 afternoon, a famous local food place known for Mughlai cuisine. The timing has been adjusted to accommodate this addition while maintaining a reasonable schedule."
}
```

---

### Scenario 6: Edit - Reduce Travel Time

**Input:**
```
"Reduce travel time"
```

**Expected Output:**
```json
{
  "status": "success",
  "edit_type": "REDUCE_TRAVEL",
  "modified_sections": ["day_1", "day_2", "day_3"],
  "itinerary": {
    "day_1": {
      // Activities reordered to group nearby attractions
      "morning": [
        {
          "activity": "Hawa Mahal",
          "time": "09:00 - 10:30",
          "duration_minutes": 90,
          "source_id": "way:123456"
        },
        {
          "activity": "City Palace",
          "time": "11:00 - 13:00",
          "duration_minutes": 120,
          "travel_time_from_previous": 5,
          "source_id": "way:123457"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Laxmi Misthan Bhandar",
          "time": "13:00 - 14:00",
          "duration_minutes": 60,
          "travel_time_from_previous": 2,
          "source_id": "node:789012"
        },
        {
          "activity": "Jantar Mantar",
          "time": "14:30 - 16:00",
          "duration_minutes": 90,
          "travel_time_from_previous": 5,
          "source_id": "way:123458"
        }
      ],
      "evening": [
        {
          "activity": "Johari Bazaar",
          "time": "16:30 - 18:00",
          "duration_minutes": 90,
          "travel_time_from_previous": 8,
          "source_id": "way:123460"
        }
      ]
    },
    "day_2": {
      // Similar reordering for proximity
    },
    "day_3": {
      // Similar reordering for proximity
    }
  },
  "total_travel_time": 90,
  "previous_travel_time": 180,
  "evaluation": {
    "feasibility": {
      "is_feasible": true,
      "score": 0.98,
      "violations": [],
      "warnings": []
    }
  },
  "explanation": "I've reorganized activities across all days to group nearby attractions together, reducing total travel time from 180 to 90 minutes. Activities are now clustered by location to minimize transit."
}
```

---

### Scenario 7: Explanation - Why POI Selected

**Input:**
```
"Why did you pick Hawa Mahal?"
```

**Expected Output:**
```json
{
  "status": "success",
  "explanation": "I selected Hawa Mahal because it aligns with your interests in culture and history. It's one of Jaipur's most iconic landmarks, built in 1799, and represents the city's architectural heritage. According to Wikivoyage, it's a must-see attraction that can be visited in about 1-2 hours, fitting well into a relaxed pace itinerary. Additionally, it's centrally located near other attractions like City Palace, minimizing travel time.",
  "sources": [
    {
      "type": "wikivoyage",
      "url": "https://en.wikivoyage.org/wiki/Jaipur#See",
      "snippet": "Hawa Mahal (Palace of Winds) is a five-story palace built in 1799. It's one of Jaipur's most iconic landmarks and can be visited in 1-2 hours."
    },
    {
      "type": "openstreetmap",
      "poi": "Hawa Mahal",
      "source_id": "way:123456",
      "url": "https://www.openstreetmap.org/way/123456"
    }
  ],
  "reasoning": {
    "criteria": [
      "Cultural significance - aligns with user's interest in culture",
      "Time fit - 90 minutes fits relaxed pace",
      "Location - central, minimizes travel",
      "Tourist rating - highly recommended"
    ]
  }
}
```

---

### Scenario 8: Explanation - Is Plan Feasible?

**Input:**
```
"Is this plan doable?"
```

**Expected Output:**
```json
{
  "status": "success",
  "explanation": "Yes, this plan is feasible. Here's why:\n\n1. **Time Management**: Each day has activities totaling 8-10 hours, well within the 13-hour window (9 AM - 10 PM).\n\n2. **Travel Times**: All travel between activities is under 20 minutes, which is reasonable for walking or short taxi rides.\n\n3. **Pace Consistency**: With 2-3 activities per day, this matches your requested relaxed pace.\n\n4. **Rest Periods**: There are adequate breaks between activities for meals and rest.\n\nHowever, Day 2 has a slightly tighter schedule - you may want to start earlier or extend one activity.",
  "evaluation_summary": {
    "feasibility_score": 0.95,
    "daily_duration_ok": true,
    "travel_times_reasonable": true,
    "pace_consistent": true,
    "warnings": ["Day 2 schedule is slightly tight"]
  },
  "detailed_checks": {
    "day_1": {
      "total_duration": 8.5,
      "travel_time": 30,
      "within_window": true
    },
    "day_2": {
      "total_duration": 9.5,
      "travel_time": 35,
      "within_window": true,
      "warning": "Slightly packed"
    },
    "day_3": {
      "total_duration": 8.0,
      "travel_time": 25,
      "within_window": true
    }
  },
  "sources": [
    {
      "type": "evaluation",
      "source": "feasibility_evaluator"
    }
  ]
}
```

---

### Scenario 9: Explanation - Weather Alternative

**Input:**
```
"What if it rains?"
```

**Expected Output:**
```json
{
  "status": "success",
  "explanation": "If it rains, here are indoor alternatives I can suggest:\n\n**Day 1 Alternatives:**\n- Replace outdoor activities with: City Palace Museum (indoor), Jawahar Kala Kendra (art center), or shopping at Johari Bazaar (covered markets)\n\n**Day 2 Alternatives:**\n- Albert Hall Museum (indoor), Birla Mandir (covered temple), or local cafes for extended food experiences\n\n**Day 3 Alternatives:**\n- Nahargarh Fort (partially covered), or spend more time at indoor restaurants and cafes\n\nAccording to Wikivoyage, Jaipur's monsoon season is July-September. If you're traveling during this time, I recommend having these backup plans ready.",
  "sources": [
    {
      "type": "wikivoyage",
      "url": "https://en.wikivoyage.org/wiki/Jaipur#Climate",
      "snippet": "Monsoon season: July-September. Indoor alternatives include museums, covered markets, and temples."
    },
    {
      "type": "rag",
      "query": "indoor activities Jaipur rainy weather",
      "results": 5
    }
  ],
  "alternatives": [
    {
      "day": 1,
      "original": "Hawa Mahal (outdoor)",
      "alternative": "City Palace Museum (indoor)",
      "source_id": "way:789012"
    },
    {
      "day": 1,
      "original": "Jantar Mantar (outdoor)",
      "alternative": "Jawahar Kala Kendra (indoor art center)",
      "source_id": "way:789013"
    },
    {
      "day": 2,
      "original": "Amber Fort (outdoor)",
      "alternative": "Albert Hall Museum (indoor)",
      "source_id": "way:789014"
    }
  ],
  "weather_info": {
    "monsoon_season": "July-September",
    "recommendation": "Have indoor backup plans ready during monsoon"
  }
}
```

---

### Scenario 10: Explanation - Why Timing

**Input:**
```
"Why did you schedule Hawa Mahal in the morning?"
```

**Expected Output:**
```json
{
  "status": "success",
  "explanation": "I scheduled Hawa Mahal in the morning (9:00 AM) for several reasons:\n\n1. **Lighting**: Morning light is best for photography of the pink sandstone facade, as mentioned in travel guides.\n\n2. **Crowds**: It's less crowded in the morning, allowing for a more relaxed experience that matches your pace preference.\n\n3. **Temperature**: Jaipur can get hot in the afternoon, so visiting outdoor attractions in the morning is more comfortable.\n\n4. **Flow**: It's close to City Palace (your next stop), so grouping them together in the morning minimizes travel time.\n\n5. **Opening Hours**: Hawa Mahal opens at 9 AM, making it an ideal first activity of the day.",
  "sources": [
    {
      "type": "wikivoyage",
      "url": "https://en.wikivoyage.org/wiki/Jaipur#See",
      "snippet": "Best visited in morning for photography and to avoid crowds. Opens at 9 AM."
    },
    {
      "type": "openstreetmap",
      "poi": "Hawa Mahal",
      "source_id": "way:123456",
      "opening_hours": "09:00-17:00"
    }
  ],
  "reasoning": {
    "factors": [
      "Optimal lighting conditions",
      "Lower crowd density",
      "Comfortable temperature",
      "Proximity to next activity",
      "Opening hours alignment"
    ]
  }
}
```

---

### Scenario 11: Error - City Not Found

**Input:**
```
"Plan a 3-day trip to XyzCity"
```

**Expected Output:**
```json
{
  "status": "error",
  "error_type": "CITY_NOT_FOUND",
  "message": "I couldn't find information about XyzCity. Could you please:\n1. Check the spelling\n2. Provide the country/state if it's a smaller city\n3. Or choose a nearby major city\n\nI have data available for major cities in India, including Jaipur, Mumbai, Delhi, Bangalore, and others.",
  "suggestions": [
    "Jaipur",
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Goa"
  ],
  "help_text": "If XyzCity is a smaller city, please specify the state or country. For example: 'XyzCity, Maharashtra' or 'XyzCity, India'."
}
```

---

### Scenario 12: Error - Missing Data

**Input:**
```
"Plan a 2-day trip to SmallTown"
```

**Expected Output:**
```json
{
  "status": "partial_success",
  "itinerary": {
    "city": "SmallTown",
    "duration_days": 2,
    "day_1": {
      "morning": [
        {
          "activity": "Local Museum",
          "time": "09:00 - 11:00",
          "duration_minutes": 120,
          "source_id": "way:999001",
          "note": "Opening hours not verified - please check before visiting"
        }
      ],
      "afternoon": [
        {
          "activity": "Local Restaurant",
          "time": "12:00 - 13:30",
          "duration_minutes": 90,
          "source_id": "node:999002"
        }
      ]
    },
    "day_2": {
      "morning": [
        {
          "activity": "Town Park",
          "time": "09:00 - 11:00",
          "duration_minutes": 120,
          "source_id": "way:999003"
        }
      ]
    }
  },
  "warnings": [
    "Limited POI data available for SmallTown",
    "Opening hours not available for some attractions",
    "Travel time estimates may be approximate"
  ],
  "uncertain_data": [
    {
      "poi": "Local Museum",
      "missing_info": "opening_hours",
      "note": "Please verify opening hours before visiting"
    },
    {
      "poi": "Local Restaurant",
      "missing_info": "cuisine_type",
      "note": "Cuisine information not available"
    }
  ],
  "evaluation": {
    "grounding": {
      "is_grounded": true,
      "score": 0.75,
      "uncertain_data": [
        "Opening hours for Local Museum not available",
        "Cuisine type for Local Restaurant not available"
      ],
      "all_pois_have_sources": true
    },
    "feasibility": {
      "is_feasible": true,
      "score": 0.80,
      "warnings": ["Some timing estimates are approximate"]
    }
  },
  "sources": [
    {
      "type": "openstreetmap",
      "poi": "Local Museum",
      "source_id": "way:999001",
      "url": "https://www.openstreetmap.org/way/999001",
      "data_completeness": "partial"
    }
  ]
}
```

---

### Scenario 13: Evaluation - Feasibility Violation

**System Internal Check (Before Returning to User):**
```json
{
  "feasibility": {
    "is_feasible": false,
    "score": 0.60,
    "violations": [
      {
        "day": 2,
        "issue": "daily_duration_exceeded",
        "details": "Day 2 activities total 15 hours, exceeding 13-hour window (9 AM - 10 PM)"
      },
      {
        "day": 1,
        "issue": "travel_time_too_long",
        "details": "Travel from Activity A to Activity B is 2 hours, exceeding 1-hour limit"
      }
    ],
    "warnings": [
      "Day 2 has 5 activities, which is fast pace, but you requested relaxed"
    ]
  }
}
```

**System Response (Auto-Corrects or Warns):**
```json
{
  "status": "success",
  "itinerary": {
    // System automatically adjusts to fix violations
    "day_1": {
      // Activities reordered to reduce travel time
    },
    "day_2": {
      // Activities reduced to fit time window
    }
  },
  "evaluation": {
    "feasibility": {
      "is_feasible": true,
      "score": 0.92,
      "violations": [],
      "warnings": ["Day 2 was adjusted to fit time constraints"],
      "auto_corrected": true
    }
  },
  "message": "I've created your itinerary. I made some adjustments to ensure it's feasible - Day 2 was slightly adjusted to fit within the time window."
}
```

**OR (If Auto-Correction Not Possible):**
```json
{
  "status": "warning",
  "itinerary": {
    // Original itinerary with violations
  },
  "evaluation": {
    "feasibility": {
      "is_feasible": false,
      "score": 0.60,
      "violations": [
        {
          "day": 2,
          "issue": "daily_duration_exceeded",
          "details": "Day 2 activities total 15 hours"
        }
      ]
    }
  },
  "message": "I've created your itinerary, but there are some feasibility concerns. Day 2 may be too packed (15 hours of activities). Would you like me to adjust it to be more relaxed?"
}
```

---

### Scenario 14: Evaluation - Edit Correctness Violation

**Input:**
```
"Make Day 2 more relaxed"
```

**But System Accidentally Modifies Day 1 Too:**

**Expected Output:**
```json
{
  "status": "error",
  "error_type": "EDIT_CORRECTNESS_VIOLATION",
  "evaluation": {
    "edit_correctness": {
      "is_correct": false,
      "modified_sections": ["day_1", "day_2"],
      "unchanged_sections": ["day_3"],
      "violations": [
        {
          "issue": "unintended_modification",
          "details": "Day 1 was modified but should have remained unchanged",
          "expected": "Only Day 2 should be modified",
          "actual": "Both Day 1 and Day 2 were modified"
        }
      ]
    }
  },
  "message": "I apologize, but I accidentally modified Day 1 when I should have only changed Day 2. Let me fix this and regenerate only Day 2.",
  "corrected_itinerary": {
    "day_1": {
      // RESTORED to original state
    },
    "day_2": {
      // CORRECTED - only Day 2 modified
    },
    "day_3": {
      // UNCHANGED
    }
  },
  "evaluation": {
    "edit_correctness": {
      "is_correct": true,
      "modified_sections": ["day_2"],
      "unchanged_sections": ["day_1", "day_3"],
      "violations": []
    }
  }
}
```

---

### Scenario 15: PDF Generation

**Input (Button Click):**
```
User clicks "Generate PDF" button in UI
```

**System Flow:**
1. Frontend sends POST request to `/api/generate-pdf` with itinerary data
2. Backend receives request and calls n8n webhook
3. n8n workflow:
   - Receives itinerary data
   - Generates PDF using Puppeteer/pdfkit
   - Sends email with PDF attachment
   - Returns confirmation

**Expected Output:**
```json
{
  "status": "success",
  "message": "PDF itinerary has been generated and sent to your email",
  "email_sent": true,
  "pdf_url": "https://n8n-instance.com/pdfs/itinerary_12345.pdf",
  "email_address": "user@example.com",
  "generated_at": "2024-01-15T10:30:00Z"
}
```

**Email Received by User:**
- **Subject**: "Your Jaipur 3-Day Itinerary"
- **Body**: 
  ```
  Hello,
  
  Your travel itinerary for Jaipur (3 days) has been generated and is attached.
  
  Have a great trip!
  
  Best regards,
  Travel Planning Assistant
  ```
- **Attachment**: `Jaipur_3Day_Itinerary_20240115.pdf`

**PDF Contents:**
- **Header**: "3-Day Trip to Jaipur"
- **Subtitle**: "Relaxed Pace | Food & Culture Focus"
- **Day 1 Section**:
  - Morning: Hawa Mahal (09:00 - 10:30, 90 min)
  - Afternoon: City Palace (11:00 - 13:00, 120 min) | Travel: 15 min
  - Afternoon: Lunch at Laxmi Misthan Bhandar (13:00 - 14:00, 60 min) | Travel: 5 min
  - Evening: Jantar Mantar (16:00 - 17:30, 90 min) | Travel: 10 min
- **Day 2 Section**: (similar format)
- **Day 3 Section**: (similar format)
- **Sources Section**:
  - OpenStreetMap: [links]
  - Wikivoyage: [links]
- **Footer**: Generated on [date]

---

### Scenario 16: Maximum Clarifying Questions Reached

**Input Sequence:**
1. User: "Plan a trip"
   - System: Question 1 - "Which city?"
2. User: "Mumbai"
   - System: Question 2 - "How many days?"
3. User: "3 days"
   - System: Question 3 - "What are your interests?"
4. User: "Food"
   - System: Question 4 - "Any other interests?"
5. User: "Beaches"
   - System: Question 5 - "What pace do you prefer?"
6. User: "Moderate"
   - System: Question 6 - "What's your budget range?"
7. User: "Budget friendly"
   - System: **Stops asking, generates plan**

**System Response (After 6 Questions):**
```json
{
  "status": "success",
  "message": "I've gathered enough information. Let me create your itinerary now.",
  "itinerary": {
    "city": "Mumbai",
    "duration_days": 3,
    "interests": ["food", "beaches"],
    "pace": "moderate",
    "budget": "budget_friendly",
    "day_1": {...},
    "day_2": {...},
    "day_3": {...}
  },
  "note": "Some preferences were not fully specified, so I've used reasonable defaults based on your stated preferences.",
  "clarifying_questions_asked": 6,
  "max_questions_reached": true
}
```

---

### Scenario 17: Voice Input with Errors

**Input (Voice - Misrecognized by STT):**
```
User speaks: "Plan a three day trip to Jaipur"
STT Output: "Plan a tree day trip to Jai poor"
```

**Option 1: System Auto-Corrects:**
```json
{
  "status": "processing",
  "original_input": "Plan a tree day trip to Jai poor",
  "corrected_input": "Plan a 3-day trip to Jaipur",
  "confidence": 0.95,
  "itinerary": {
    // Generated with corrected input
  }
}
```

**Option 2: System Asks for Confirmation:**
```json
{
  "status": "clarifying",
  "question": "I heard 'tree day trip to Jai poor'. Did you mean '3-day trip to Jaipur'?",
  "transcript_correction": true,
  "suggested_correction": "Plan a 3-day trip to Jaipur"
}
```

**User Confirms:**
```
"Yes, that's correct"
```

**System Response:**
```json
{
  "status": "success",
  "itinerary": {
    // Generated itinerary
  }
}
```

---

### Scenario 18: Multiple Edits in Sequence

**Input 1:**
```
"Make Day 2 more relaxed"
```

**System Response:**
```json
{
  "status": "success",
  "edit_type": "CHANGE_PACE",
  "modified_section": "day_2",
  "itinerary": {
    // Day 2 modified, Day 1 and Day 3 unchanged
  }
}
```

**Input 2 (After First Edit):**
```
"Now add a food place to Day 1"
```

**System Response:**
```json
{
  "status": "success",
  "edit_type": "ADD_ACTIVITY",
  "modified_section": "day_1",
  "itinerary": {
    "day_1": {
      // Day 1 now has food place added
      // Previous Day 2 edit is preserved
    },
    "day_2": {
      // Previous edit preserved - still relaxed
    },
    "day_3": {
      // Unchanged
    }
  },
  "evaluation": {
    "edit_correctness": {
      "is_correct": true,
      "modified_sections": ["day_1"],
      "unchanged_sections": ["day_2", "day_3"],
      "violations": []
    }
  }
}
```

**Input 3:**
```
"Swap Day 3 morning to something cultural"
```

**System Response:**
```json
{
  "status": "success",
  "edit_type": "SWAP_ACTIVITY",
  "modified_section": "day_3_morning",
  "itinerary": {
    "day_1": {
      // Previous edits preserved
    },
    "day_2": {
      // Previous edits preserved
    },
    "day_3": {
      "morning": [
        {
          "activity": "Albert Hall Museum",
          "time": "09:00 - 11:00",
          "category": "cultural",
          "source_id": "way:123462"
        }
      ],
      // Rest of day unchanged
    }
  },
  "evaluation": {
    "edit_correctness": {
      "is_correct": true,
      "modified_sections": ["day_3_morning"],
      "unchanged_sections": ["day_1_afternoon", "day_1_evening", "day_2", "day_3_afternoon", "day_3_evening"],
      "violations": []
    }
  },
  "edit_history": [
    {"edit": "CHANGE_PACE", "target": "day_2", "timestamp": "..."},
    {"edit": "ADD_ACTIVITY", "target": "day_1", "timestamp": "..."},
    {"edit": "SWAP_ACTIVITY", "target": "day_3_morning", "timestamp": "..."}
  ]
}
```

---

### Scenario 19: Explanation - Missing Source

**Input:**
```
"Why did you pick Restaurant X?"
```

**Expected Output (if source missing):**
```json
{
  "status": "partial_success",
  "explanation": "I selected Restaurant X based on its location near your other activities and positive reviews from travel sources. However, I couldn't find detailed information about this restaurant in my data sources, so I recommend verifying its current status, opening hours, and reviews before visiting.",
  "sources": [
    {
      "type": "openstreetmap",
      "poi": "Restaurant X",
      "source_id": "node:999999",
      "url": "https://www.openstreetmap.org/node/999999",
      "data_completeness": "partial",
      "missing_info": ["detailed_reviews", "cuisine_type", "price_range"]
    }
  ],
  "uncertainty": true,
  "note": "Limited data available for this POI. Please verify independently through other sources or by calling the restaurant.",
  "recommendations": [
    "Check restaurant's website or social media",
    "Call to verify opening hours",
    "Read recent reviews on travel platforms"
  ]
}
```

---

### Scenario 20: Complete Conversation Flow

**Full Conversation Example:**
```
User: "Plan a 3-day trip to Jaipur. I like food and culture."
System: "What pace do you prefer - relaxed, moderate, or fast?"
User: "Relaxed"
System: [Generates itinerary and displays in UI]

User: "Make Day 2 more relaxed"
System: [Updates Day 2 only, shows changes in UI]

User: "Why did you pick Hawa Mahal?"
System: [Shows explanation panel with citations]

User: "What if it rains?"
System: [Shows indoor alternatives with sources]

User: [Clicks "Generate PDF" button]
System: [Shows success message, user receives email with PDF]
```

**Final System State:**
```json
{
  "session_id": "session_12345",
  "conversation_history": [
    {"role": "user", "content": "Plan a 3-day trip to Jaipur. I like food and culture."},
    {"role": "assistant", "content": "What pace do you prefer?"},
    {"role": "user", "content": "Relaxed"},
    {"role": "assistant", "content": "[Generated itinerary]"},
    {"role": "user", "content": "Make Day 2 more relaxed"},
    {"role": "assistant", "content": "[Updated Day 2]"},
    {"role": "user", "content": "Why did you pick Hawa Mahal?"},
    {"role": "assistant", "content": "[Explanation]"},
    {"role": "user", "content": "What if it rains?"},
    {"role": "assistant", "content": "[Indoor alternatives]"}
  ],
  "current_itinerary": {
    // Final itinerary with all edits applied
    "day_1": {...},
    "day_2": {
      // Modified to be more relaxed
    },
    "day_3": {...}
  },
  "evaluation": {
    "feasibility": {
      "is_feasible": true,
      "score": 0.96
    },
    "grounding": {
      "is_grounded": true,
      "score": 0.98
    },
    "edit_correctness": {
      "all_edits_correct": true
    }
  },
  "pdf_generated": true,
  "pdf_sent_at": "2024-01-15T10:30:00Z"
}
```

---

## Summary of Expected Outputs

### 1. **Structured JSON Responses**
   - Itinerary data with day/time blocks
   - Activity details (name, time, duration, location)
   - Travel times between activities
   - Sources and citations
   - Evaluation results

### 2. **User Interface Display**
   - Day-wise itinerary tabs
   - Morning/Afternoon/Evening blocks
   - Live transcript
   - Sources section with links
   - Explanation panel
   - PDF download button

### 3. **Evaluation Results**
   - Feasibility scores and violations
   - Grounding verification
   - Edit correctness checks

### 4. **Error Handling**
   - City not found → Suggestions
   - Missing data → Explicit warnings
   - Edit violations → Auto-correction or warnings

### 5. **PDF Document**
   - Professional layout
   - Complete itinerary
   - Sources section
   - Email delivery

### 6. **Conversation Management**
   - Max 6 clarifying questions
   - State preservation across edits
   - Edit history tracking

---

### Scenario 21: Food-Focused Itinerary

**Input (Voice/Text):**
```
"Plan a 2-day trip to Chennai. I like food. Relaxed pace."
```

**System Flow:**
1. Intent Classification: `PLAN_TRIP`
2. Entity Extraction: city="Chennai", duration=2, interests=["food"], pace="relaxed"
3. POI Search MCP → Returns restaurants, cafes, food places
4. Itinerary Builder MCP → Creates food-focused plan prioritizing restaurants
5. Feasibility Evaluator → Validates plan
6. Grounding Evaluator → Checks all sources

**Expected Output:**
```json
{
  "status": "success",
  "itinerary": {
    "city": "Chennai",
    "duration_days": 2,
    "interests": ["food"],
    "pace": "relaxed",
    "day_1": {
      "morning": [
        {
          "activity": "Breakfast at Saravana Bhavan",
          "time": "09:00 - 10:30",
          "duration_minutes": 90,
          "category": "restaurant",
          "source_id": "node:123456",
          "description": "Famous South Indian vegetarian restaurant"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Anjappar Chettinad Restaurant",
          "time": "12:30 - 14:00",
          "duration_minutes": 90,
          "category": "restaurant",
          "source_id": "node:123457",
          "description": "Authentic Chettinad cuisine"
        }
      ],
      "evening": [
        {
          "activity": "Dinner at The Marina",
          "time": "19:00 - 21:00",
          "duration_minutes": 120,
          "category": "restaurant",
          "source_id": "node:123458",
          "description": "Seafood restaurant with beach view"
        }
      ]
    },
    "day_2": {
      "morning": [
        {
          "activity": "Breakfast at Murugan Idli Shop",
          "time": "08:30 - 10:00",
          "duration_minutes": 90,
          "category": "restaurant",
          "source_id": "node:123459"
        }
      ],
      "afternoon": [
        {
          "activity": "Lunch at Rayar's Mess",
          "time": "12:00 - 13:30",
          "duration_minutes": 90,
          "category": "restaurant",
          "source_id": "node:123460"
        }
      ],
      "evening": [
        {
          "activity": "Dinner at Zaitoon",
          "time": "19:00 - 21:00",
          "duration_minutes": 120,
          "category": "restaurant",
          "source_id": "node:123461"
        }
      ]
    }
  },
  "sources": [
    {
      "type": "openstreetmap",
      "poi": "Saravana Bhavan",
      "source_id": "node:123456",
      "url": "https://www.openstreetmap.org/node/123456"
    }
  ],
  "evaluation": {
    "feasibility": {
      "is_feasible": true,
      "score": 0.95
    },
    "grounding": {
      "is_grounded": true,
      "score": 0.98
    }
  },
  "explanation": "I've created a 2-day food-focused itinerary for Chennai with relaxed pace. Each day includes breakfast, lunch, and dinner at different restaurants showcasing Chennai's diverse culinary scene, from traditional South Indian to Chettinad and seafood specialties."
}
```

**Validation Criteria:**
- ✅ At least 60% of activities should be restaurants/cafes/food places
- ✅ Multiple food experiences per day (breakfast, lunch, dinner)
- ✅ Restaurants should be distributed across morning, afternoon, and evening time slots
- ✅ All restaurants should have valid source IDs
- ✅ Itinerary respects relaxed pace (2-3 activities per day)

---

## Testing Checklist

Use this checklist to verify all scenarios:

- [ ] Scenario 1: Complete trip planning (no questions)
- [ ] Scenario 2: Trip planning with clarifying questions
- [ ] Scenario 3: Edit - Change pace
- [ ] Scenario 4: Edit - Swap activity
- [ ] Scenario 5: Edit - Add activity
- [ ] Scenario 6: Edit - Reduce travel time
- [ ] Scenario 7: Explanation - Why POI selected
- [ ] Scenario 8: Explanation - Is plan feasible?
- [ ] Scenario 9: Explanation - Weather alternative
- [ ] Scenario 10: Explanation - Why timing
- [ ] Scenario 11: Error - City not found
- [ ] Scenario 12: Error - Missing data
- [ ] Scenario 13: Evaluation - Feasibility violation
- [ ] Scenario 14: Evaluation - Edit correctness violation
- [ ] Scenario 15: PDF generation
- [ ] Scenario 16: Maximum clarifying questions
- [ ] Scenario 17: Voice input errors
- [ ] Scenario 18: Multiple sequential edits
- [ ] Scenario 19: Explanation with missing source
- [ ] Scenario 20: Complete conversation flow
- [ ] Scenario 21: Food-focused itinerary (restaurants prioritized)

---

**Note**: All scenarios should be tested with both voice input (STT) and text input to ensure both modes work correctly.
