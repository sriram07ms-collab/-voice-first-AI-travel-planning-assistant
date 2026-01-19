# Voice Editing Feature - Future Implementation Guide

This document outlines the planned voice editing feature for PDF itineraries.

## 🎯 Feature Overview

Allow users to edit specific sections of a generated PDF itinerary using voice commands, then automatically update the plan and regenerate the PDF.

## 📋 Use Cases

### Example Voice Commands:
- *"Change Day 2 morning activity to a museum"*
- *"Replace the Day 1 evening restaurant with a vegetarian option"*
- *"Make Day 3 more relaxed - remove one activity"*
- *"Swap Day 2 afternoon and evening plans"*
- *"Add a shopping stop to Day 1"*

## 🏗️ Architecture

```
User Voice Command
  ↓
Frontend (Voice Input)
  ↓
Backend API (/api/edit)
  ↓
Orchestrator (Edit Handler)
  ↓
MCP Tools (POI Search + Itinerary Builder)
  ↓
Update Itinerary in Session
  ↓
Trigger n8n Workflow
  ↓
Generate Updated PDF
  ↓
Email Updated PDF
  ↓
Display in UI
```

## 🔧 Implementation Plan

### Phase 1: Voice Command Parsing

**File**: `backend/src/orchestrator/edit_handler.py`

**Enhancements Needed**:
1. **Enhanced Voice Command Recognition**:
   - Parse voice commands for PDF section references
   - Identify target day and time block
   - Extract edit intent (replace, add, remove, swap)

2. **PDF Section Mapping**:
   - Map PDF sections to itinerary structure
   - Track which activities are in which PDF sections
   - Maintain PDF → Itinerary mapping

**Example**:
```python
def parse_voice_edit_command(user_input: str, pdf_context: Dict) -> Dict:
    """
    Parse voice command that references PDF sections.
    
    Examples:
    - "Change the first activity on Day 2" → day_2.morning.activities[0]
    - "Replace the restaurant in the evening" → day_X.evening.activities[restaurant]
    """
```

### Phase 2: PDF Section Identification

**New Component**: `backend/src/services/pdf_section_mapper.py`

**Functionality**:
1. **Map PDF to Itinerary**:
   - When PDF is generated, create mapping of PDF sections to itinerary activities
   - Store mapping in session
   - Use mapping to identify which activities to edit

2. **Section Tracking**:
   - Track page numbers
   - Track activity positions
   - Track time blocks

**Data Structure**:
```python
{
    "pdf_sections": [
        {
            "page": 1,
            "day": 1,
            "time_block": "morning",
            "activity_index": 0,
            "activity_name": "Hawa Mahal",
            "itinerary_path": "day_1.morning.activities[0]"
        },
        ...
    ]
}
```

### Phase 3: Edit Workflow Integration

**Update**: `backend/src/orchestrator/orchestrator.py`

**Enhancements**:
1. **Edit Detection**:
   - Detect if edit command references PDF
   - Extract PDF section from command
   - Map to itinerary activity

2. **Edit Application**:
   - Use existing edit handler
   - Update only affected sections
   - Preserve PDF structure

### Phase 4: PDF Regeneration

**Update**: `backend/src/main.py` - `/api/generate-pdf` endpoint

**Enhancements**:
1. **Auto-regenerate on Edit**:
   - After successful edit, automatically trigger PDF regeneration
   - Include option to email updated PDF
   - Return PDF URL for UI display

2. **Version Tracking**:
   - Track PDF versions
   - Allow comparison between versions
   - Store edit history

### Phase 5: Frontend Integration

**Update**: `frontend/src/app/page.tsx`

**New Features**:
1. **PDF Viewer**:
   - Display PDF in iframe or embed
   - Highlight sections that can be edited
   - Show edit buttons on hover

2. **Voice Edit Interface**:
   - Voice button for editing
   - Visual feedback when editing
   - Show diff between old and new

3. **Edit History**:
   - Display edit history
   - Allow undo/redo
   - Show what changed

## 📝 Voice Command Examples

### Replace Activity
**Command**: *"Replace the morning activity on Day 2 with a museum"*

**Processing**:
1. Identify: Day 2, Morning, First activity
2. Search: Museums in city
3. Replace: Update activity
4. Regenerate: PDF with new activity

### Add Activity
**Command**: *"Add a coffee shop to Day 1 afternoon"*

**Processing**:
1. Identify: Day 1, Afternoon, Insert position
2. Search: Coffee shops near other activities
3. Insert: Add new activity
4. Regenerate: PDF with new activity

### Remove Activity
**Command**: *"Remove the last activity from Day 3"*

**Processing**:
1. Identify: Day 3, Last activity
2. Remove: Delete activity
3. Adjust: Update timing if needed
4. Regenerate: PDF without activity

### Swap Activities
**Command**: *"Swap Day 2 morning and afternoon plans"*

**Processing**:
1. Identify: Day 2, Morning and Afternoon blocks
2. Swap: Exchange activities
3. Adjust: Update timing
4. Regenerate: PDF with swapped activities

## 🔄 Edit Workflow

```
1. User: "Change Day 2 morning to a museum"
   ↓
2. System: Identifies Day 2, Morning section
   ↓
3. System: Searches for museums in city
   ↓
4. System: Replaces morning activity
   ↓
5. System: Validates edit (feasibility, travel time)
   ↓
6. System: Updates itinerary in session
   ↓
7. System: Auto-triggers PDF regeneration
   ↓
8. System: Emails updated PDF (optional)
   ↓
9. System: Displays updated PDF in UI
   ↓
10. System: Shows what changed
```

## 🎨 UI Components Needed

### 1. PDF Viewer Component
**File**: `frontend/src/components/PDFViewer.tsx`

**Features**:
- Display PDF in iframe
- Highlight editable sections
- Click to edit functionality
- Zoom and navigation

### 2. Edit History Component
**File**: `frontend/src/components/EditHistory.tsx`

**Features**:
- List of edits made
- Show before/after
- Undo/redo buttons
- Timestamp of edits

### 3. Voice Edit Button
**File**: `frontend/src/components/VoiceEditButton.tsx`

**Features**:
- Voice input for edits
- Visual feedback
- Edit preview
- Confirm/cancel

## 🔍 Technical Considerations

### PDF Section Identification

**Challenge**: How to identify which section user wants to edit?

**Solutions**:
1. **Natural Language Parsing**:
   - "First activity on Day 2" → day_2.morning.activities[0]
   - "The restaurant in the evening" → day_X.evening.activities[restaurant_type]
   - "Last activity" → day_X.evening.activities[-1]

2. **Visual Selection**:
   - User clicks on PDF section
   - System identifies which activity
   - User provides voice command

3. **Context from Conversation**:
   - Use recent conversation context
   - Reference previously mentioned activities
   - Use pronouns ("that activity", "the one we discussed")

### PDF Regeneration Performance

**Considerations**:
- PDF generation takes time (5-10 seconds)
- Show loading indicator
- Option to skip email (just update UI)
- Cache previous PDF versions

### Edit Validation

**Checks**:
- Feasibility (time constraints)
- Travel time between activities
- Pace consistency
- No duplicate activities

## 📊 Data Flow

```
Session State:
├── Original Itinerary
├── Current Itinerary (after edits)
├── PDF Mapping (section → activity)
├── Edit History
└── PDF Versions
```

## 🚀 Implementation Phases

### Phase 1: Basic Voice Edit (Current)
- ✅ Edit handler exists
- ✅ Voice input works
- ✅ Edit endpoint works
- ⏳ Need: Better POI extraction from voice

### Phase 2: PDF Section Mapping
- ⏳ Create PDF section mapper
- ⏳ Store mapping in session
- ⏳ Use mapping for edits

### Phase 3: Auto PDF Regeneration
- ⏳ Auto-trigger PDF after edit
- ⏳ Return PDF URL
- ⏳ Display in UI

### Phase 4: Enhanced Voice Parsing
- ⏳ Better section identification
- ⏳ Context-aware editing
- ⏳ Multi-activity edits

### Phase 5: PDF Viewer Integration
- ⏳ PDF viewer component
- ⏳ Click-to-edit
- ⏳ Visual feedback

## 📝 API Endpoints

### Existing
- `POST /api/edit` - Edit itinerary (works with voice)

### New (Future)
- `POST /api/edit-pdf-section` - Edit specific PDF section
- `GET /api/pdf-versions` - Get PDF version history
- `POST /api/regenerate-pdf` - Force PDF regeneration

## 🎯 Success Criteria

1. ✅ User can edit itinerary via voice
2. ⏳ User can reference PDF sections in voice commands
3. ⏳ PDF automatically updates after edits
4. ⏳ Changes are clearly visible
5. ⏳ Edit history is maintained

## 🔮 Future Enhancements

1. **Multi-Edit Commands**:
   - "Change all restaurants to vegetarian options"
   - "Make all days more relaxed"

2. **Smart Suggestions**:
   - "This activity is far from others, want to swap?"
   - "Day 2 is packed, suggest removing one activity?"

3. **Batch Edits**:
   - Edit multiple days at once
   - Apply same change to all days

4. **Voice Confirmation**:
   - "Did you mean to replace X with Y?"
   - "This will change 3 activities, confirm?"

## 📚 Related Documentation

- [Edit Handler Implementation](../backend/src/orchestrator/edit_handler.py)
- [n8n Integration Guide](./N8N_INTEGRATION_GUIDE.md)
- [Orchestrator Documentation](../backend/src/orchestrator/orchestrator.py)

---

**Status**: 📋 Planned for Future Implementation  
**Priority**: Medium  
**Estimated Effort**: 2-3 weeks

---

**Last Updated**: 2024-01-15
