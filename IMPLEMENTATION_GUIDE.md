# Step-by-Step Implementation Guide

This guide provides detailed, actionable steps to build the Voice-First AI Travel Planning Assistant. Follow these steps in order, testing after each phase.

## 📋 Implementation Phases Overview

1. **Phase 1**: Core Infrastructure Setup
2. **Phase 2**: Data Integration
3. **Phase 3**: MCP Tools
4. **Phase 4**: Orchestration Layer
5. **Phase 5**: Editing & Explanation
6. **Phase 6**: Evaluation System
7. **Phase 7**: Frontend Components
8. **Phase 8**: n8n Integration
9. **Phase 9**: Testing & Deployment

---

## Phase 1: Core Infrastructure Setup

### Step 1.1: Initialize Project Structure

**Create directories:**
```bash
mkdir -p frontend/src/{components,hooks,services}
mkdir -p backend/src/{orchestrator,mcp,rag,evaluation,data_sources,utils}
mkdir -p mcp-tools/{poi-search,itinerary-builder}
mkdir -p n8n-workflows
mkdir -p tests
mkdir -p docs
```

### Step 1.2: Backend Setup (Python FastAPI)

**Create `backend/requirements.txt`:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
openai==1.3.0
langchain==0.1.0
langchain-openai==0.0.2
chromadb==0.4.18
requests==2.31.0
beautifulsoup4==4.12.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
```

**Create `backend/src/main.py` (skeleton):**
- FastAPI app with CORS
- Basic route structure: `/api/chat`, `/api/plan`, `/api/edit`, `/api/explain`
- Health check endpoint: `/health`
- Error handling middleware
- Environment variable loading

**Create `backend/.env.example`:**
```
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@localhost/db
CHROMA_PERSIST_DIR=./chroma_db
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
OPEN_METEO_API_URL=https://api.open-meteo.com/v1
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/...
```

### Step 1.3: Frontend Setup (Next.js)

**Create `frontend/package.json`:**
```json
{
  "name": "travel-assistant-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "tailwindcss": "3.3.0",
    "axios": "1.6.0"
  }
}
```

**Initialize Next.js project:**
- Set up TailwindCSS
- Create basic app structure
- Create API client service (`services/api.ts`)

### Step 1.4: Git Setup

**Create `.gitignore`:**
```
# Python
__pycache__/
*.py[cod]
.env
venv/
chroma_db/

# Node
node_modules/
.next/
.env.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

**Initialize git:**
```bash
git init
git add .
git commit -m "Initial project structure"
```

---

## Phase 2: Data Integration

### Step 2.1: OpenStreetMap Integration

**Create `backend/src/data_sources/openstreetmap.py`:**

**Functionality:**
1. Query Overpass API for POIs by city
2. Filter by category (restaurant, attraction, museum, etc.)
3. Parse JSON responses
4. Extract: name, location (lat/lon), category, source_id (way/node ID)
5. Handle rate limiting (max 1 request/second recommended)

**Key Functions:**
- `search_pois(city: str, interests: List[str], constraints: Dict) -> List[POI]`
- `get_poi_details(poi_id: str) -> Dict`
- `filter_by_category(pois: List, category: str) -> List`

**Example Overpass Query:**
```python
query = f"""
[out:json][timeout:25];
(
  node["tourism"="attraction"](around:5000,{lat},{lon});
  way["tourism"="attraction"](around:5000,{lat},{lon});
);
out body;
>;
out skel qt;
"""
```

**Test:** Query POIs for "Jaipur" and verify results include valid source IDs.

### Step 2.2: Wikivoyage Scraper

**Create `backend/src/data_sources/wikivoyage.py`:**

**Functionality:**
1. Scrape Wikivoyage city pages (e.g., `https://en.wikivoyage.org/wiki/Jaipur`)
2. Extract sections: "Understand", "See", "Do", "Eat", "Stay", "Stay safe"
3. Clean HTML and extract text
4. Chunk text into paragraphs (~500 tokens each)
5. Store with metadata: city, section, source_url

**Key Functions:**
- `scrape_city_page(city: str) -> Dict[str, str]`
- `chunk_text(text: str, max_tokens: int = 500) -> List[str]`
- `extract_sections(html: str) -> Dict[str, str]`

**Test:** Scrape Jaipur page and verify chunks are created with source URLs.

### Step 2.3: RAG Vector Store Setup

**Create `backend/src/rag/vector_store.py`:**

**Functionality:**
1. Initialize ChromaDB with persistent storage
2. Create collection with metadata schema
3. Embed documents using OpenAI embeddings
4. Store documents with metadata (city, section, source_url, page_title)
5. Implement retrieval functions

**Key Functions:**
- `initialize_store(persist_directory: str) -> ChromaDB`
- `add_documents(documents: List[str], metadatas: List[Dict]) -> None`
- `search_similar(query: str, city: str, top_k: int = 5) -> List[Dict]`
- `get_by_city(city: str) -> List[Dict]`

**Create `backend/src/rag/data_loader.py`:**
- Load Wikivoyage data into vector store
- Preload common cities (optional)
- Function: `load_wikivoyage_data(cities: List[str]) -> None`

**Test:** Load Wikivoyage data for Jaipur and verify semantic search returns relevant results.

### Step 2.4: Retriever Implementation

**Create `backend/src/rag/retriever.py`:**

**Functionality:**
1. Semantic search in vector store
2. Filter by city
3. Return top-k results with citations
4. Format for LLM context

**Key Functions:**
- `retrieve_city_tips(city: str, query: str, top_k: int = 5) -> List[Dict]`
- `retrieve_safety_info(city: str) -> List[Dict]`
- `retrieve_indoor_alternatives(city: str) -> List[Dict]`
- `format_for_context(results: List[Dict]) -> str`

**Test:** Query for "safety tips in Jaipur" and verify results include citations.

---

## Phase 3: MCP Tools Implementation

### Step 3.1: POI Search MCP Tool

**Create `mcp-tools/poi-search/server.py`:**

**MCP Server Requirements:**
- Follow MCP protocol specifications
- Implement tool: `search_pois`

**Input Schema:**
```json
{
  "city": "Jaipur",
  "interests": ["food", "culture"],
  "constraints": {
    "budget": "moderate",
    "accessibility": null,
    "time_of_day": "evening"
  }
}
```

**Output Schema:**
```json
{
  "pois": [
    {
      "name": "Hawa Mahal",
      "category": "historical",
      "location": {"lat": 26.9240, "lon": 75.8266},
      "duration_minutes": 60,
      "data_source": "openstreetmap",
      "source_id": "way:123456",
      "rating": null,
      "description": "..."
    }
  ]
}
```

**Implementation Steps:**
1. Set up MCP server skeleton
2. Integrate OpenStreetMap client
3. Implement filtering and ranking logic
4. Return structured results
5. Handle errors gracefully

**Test:** Call MCP tool with test inputs and verify structured output.

### Step 3.2: Itinerary Builder MCP Tool

**Create `mcp-tools/itinerary-builder/server.py`:**

**MCP Server Requirements:**
- Implement tool: `build_itinerary`

**Input Schema:**
```json
{
  "pois": [...],
  "daily_time_windows": [
    {"day": 1, "start": "09:00", "end": "22:00"},
    {"day": 2, "start": "09:00", "end": "22:00"}
  ],
  "pace": "relaxed",
  "preferences": {"food": true, "culture": true}
}
```

**Output Schema:**
```json
{
  "itinerary": {
    "day_1": {
      "morning": [...],
      "afternoon": [...],
      "evening": [...]
    }
  },
  "total_travel_time": 120,
  "explanation": "Grouped nearby attractions..."
}
```

**Implementation Steps:**
1. Set up MCP server
2. Use LLM (OpenAI) to build itinerary from POIs
3. Structure into day/time blocks
4. Estimate durations
5. Calculate travel times
6. Generate explanations

**LLM Prompt Template:**
```
Given these POIs: {pois}
Time windows: {daily_time_windows}
Pace: {pace}
Preferences: {preferences}

Create a feasible day-wise itinerary grouping nearby attractions and respecting time constraints.
```

**Test:** Build itinerary for 3-day Jaipur trip and verify structure.

### Step 3.3: MCP Client Wrapper

**Create `backend/src/mcp/mcp_client.py`:**

**Functionality:**
1. Connect to MCP servers
2. Wrapper functions for each MCP tool
3. Error handling and retries
4. Connection management

**Key Functions:**
- `connect_to_mcp_servers() -> None`
- `search_pois(city, interests, constraints) -> List[POI]`
- `build_itinerary(pois, time_windows, pace, preferences) -> Dict`
- `estimate_travel_time(origin, destination, mode) -> Dict`

**Test:** Connect to MCP servers and verify tool calls work.

---

## Phase 4: Orchestration Layer

### Step 4.1: Conversation Manager

**Create `backend/src/orchestrator/conversation_manager.py`:**

**Functionality:**
1. Store conversation state (user preferences, itinerary, history)
2. Track context (city, duration, preferences)
3. Manage clarifying questions (max 6)
4. Reset conversation

**Data Structure:**
```python
{
  "session_id": str,
  "preferences": {
    "city": str,
    "duration_days": int,
    "interests": List[str],
    "pace": str,
    "budget": str
  },
  "itinerary": Dict,
  "conversation_history": List[Dict],
  "clarifying_questions_count": int
}
```

**Key Functions:**
- `create_session() -> str`
- `add_message(session_id, role, content) -> None`
- `get_context(session_id) -> Dict`
- `update_preferences(session_id, preferences) -> None`
- `reset_conversation(session_id) -> None`

**Test:** Create session, add messages, verify state management.

### Step 4.2: Intent Classifier

**Create `backend/src/orchestrator/intent_classifier.py`:**

**Functionality:**
1. Classify user input into intents
2. Extract entities
3. Handle voice input normalization

**Intents:**
- `PLAN_TRIP`: "Plan a 3-day trip to Jaipur"
- `EDIT_ITINERARY`: "Make Day 2 more relaxed"
- `EXPLAIN`: "Why did you pick Hawa Mahal?"
- `CLARIFY`: Answer to clarifying question
- `OTHER`: Unrecognized

**LLM-based Classification:**
```python
prompt = f"""
Classify this user input: "{user_input}"

Return JSON:
{{
  "intent": "PLAN_TRIP|EDIT_ITINERARY|EXPLAIN|CLARIFY|OTHER",
  "entities": {{
    "city": "...",
    "duration": ...,
    "target_day": ...,
    "edit_type": "..."
  }},
  "confidence": 0.0-1.0
}}
"""
```

**Key Functions:**
- `classify_intent(user_input: str) -> Dict`
- `extract_entities(user_input: str, intent: str) -> Dict`
- `normalize_voice_input(text: str) -> str`

**Test:** Classify various inputs and verify correct intent extraction.

### Step 4.3: Main Orchestrator

**Create `backend/src/orchestrator/orchestrator.py`:**

**Core Function: `plan_trip(session_id, user_input)`**

**Flow:**
1. Extract preferences from user_input
2. Check if clarifying questions needed (max 6)
3. If needed, generate clarifying question
4. If complete, proceed:
   - Call POI Search MCP
   - Retrieve RAG context (Wikivoyage)
   - Call Itinerary Builder MCP
   - Run Feasibility Evaluator
   - Run Grounding Evaluator
   - Return itinerary + sources

**Core Function: `edit_itinerary(session_id, user_input)`**

**Flow:**
1. Parse edit intent (target_day, edit_type)
2. Extract current itinerary section
3. Call POI Search MCP (if needed)
4. Call Itinerary Builder MCP (for affected day only)
5. Run Edit Correctness Evaluator
6. Return updated itinerary

**Core Function: `explain_decision(session_id, user_input)`**

**Flow:**
1. Identify what to explain (POI, timing, etc.)
2. Retrieve relevant RAG context
3. Retrieve original reasoning
4. Generate explanation with citations
5. Return explanation + sources

**Key Functions:**
- `plan_trip(session_id, user_input) -> Dict`
- `edit_itinerary(session_id, user_input) -> Dict`
- `explain_decision(session_id, user_input) -> Dict`
- `_generate_clarifying_question(preferences) -> str`

**Test:** End-to-end trip planning flow.

---

## Phase 5: Editing & Explanation

### Step 5.1: Voice Edit Handler

**Create `backend/src/orchestrator/edit_handler.py`:**

**Functionality:**
1. Parse edit commands
2. Identify affected section
3. Regenerate only affected part
4. Validate changes

**Edit Types:**
- `CHANGE_PACE`: "Make Day 2 more relaxed"
- `SWAP_ACTIVITY`: "Swap Day 1 evening plan"
- `ADD_ACTIVITY`: "Add one famous local food place"
- `REMOVE_ACTIVITY`: "Remove X from Day 2"
- `REDUCE_TRAVEL`: "Reduce travel time"

**Key Functions:**
- `parse_edit_command(user_input: str) -> Dict`
- `identify_affected_section(edit_command: Dict, itinerary: Dict) -> Dict`
- `apply_edit(itinerary: Dict, edit_command: Dict) -> Dict`

**Test:** Various edit commands and verify only affected sections change.

### Step 5.2: Explanation Generator

**Create `backend/src/orchestrator/explanation_generator.py`:**

**Functionality:**
1. Retrieve context from RAG
2. Retrieve original reasoning
3. Generate explanation with citations
4. Format for display

**Question Types:**
- POI selection: "Why did you pick Hawa Mahal?"
- Timing: "Why this time slot?"
- Feasibility: "Is this plan doable?"
- Alternatives: "What if it rains?"

**Key Functions:**
- `explain_poi_selection(poi_name: str, city: str) -> Dict`
- `explain_timing(activity: Dict, day: int) -> Dict`
- `explain_feasibility(itinerary: Dict) -> Dict`
- `explain_alternatives(scenario: str, city: str) -> Dict`

**Test:** Generate explanations for various questions and verify citations.

---

## Phase 6: Evaluation System

### Step 6.1: Feasibility Evaluator

**Create `backend/src/evaluation/feasibility_eval.py`:**

**Checks:**
1. **Daily Duration**: Total activities + travel ≤ available time
2. **Travel Times**: Between stops < 30 min (walk) or < 1 hour (transport)
3. **Pace Consistency**: Activities per day match pace

**Pace Rules:**
- Relaxed: 2-3 activities/day
- Moderate: 3-4 activities/day
- Fast: 4-5 activities/day

**Key Functions:**
- `evaluate_feasibility(itinerary: Dict, constraints: Dict) -> Dict`
- `check_daily_duration(day_itinerary: Dict, time_window: Dict) -> bool`
- `check_travel_times(itinerary: Dict) -> List[Dict]`
- `check_pace_consistency(itinerary: Dict, pace: str) -> bool`

**Return Format:**
```json
{
  "is_feasible": true,
  "score": 0.95,
  "violations": [],
  "warnings": ["Day 2 has tight schedule"]
}
```

**Test:** Test with various itineraries and verify checks.

### Step 6.2: Edit Correctness Evaluator

**Create `backend/src/evaluation/edit_correctness_eval.py`:**

**Checks:**
1. Only intended day/section modified
2. Other days unchanged
3. Edit intent correctly interpreted

**Key Functions:**
- `evaluate_edit_correctness(old_itinerary: Dict, new_itinerary: Dict, edit_intent: Dict) -> Dict`
- `compare_itineraries(old: Dict, new: Dict) -> Dict`
- `verify_edit_scope(changes: Dict, edit_intent: Dict) -> bool`

**Return Format:**
```json
{
  "is_correct": true,
  "modified_sections": ["day_2"],
  "unchanged_sections": ["day_1", "day_3"],
  "violations": []
}
```

**Test:** Edit itinerary and verify only intended sections change.

### Step 6.3: Grounding Evaluator

**Create `backend/src/evaluation/grounding_eval.py`:**

**Checks:**
1. All POIs have valid OpenStreetMap source_id
2. All tips have Wikivoyage citations
3. Missing data explicitly stated

**Key Functions:**
- `evaluate_grounding(itinerary: Dict, explanations: List[Dict]) -> Dict`
- `check_poi_sources(itinerary: Dict) -> List[Dict]`
- `check_citations(explanations: List[Dict]) -> List[Dict]`
- `identify_missing_data(itinerary: Dict) -> List[str]`

**Return Format:**
```json
{
  "is_grounded": true,
  "score": 0.98,
  "missing_citations": [],
  "uncertain_data": ["Opening hours for X not available"],
  "all_pois_have_sources": true
}
```

**Test:** Verify grounding checks work correctly.

---

## Phase 7: Frontend Components

### Step 7.1: Voice Input Component

**Create `frontend/src/components/VoiceInput.tsx`:**

**Functionality:**
1. Web Speech API integration
2. Microphone button with states
3. Real-time transcript
4. Error handling (browser compatibility)

**Key Features:**
- Start/stop recording
- Visual feedback (recording indicator)
- Handle browser permissions
- Error messages for unsupported browsers

**Test:** Record voice input and verify transcript.

### Step 7.2: Itinerary View Component

**Create `frontend/src/components/ItineraryView.tsx`:**

**Display:**
- Day tabs (Day 1 / Day 2 / Day 3)
- Time blocks (Morning / Afternoon / Evening)
- Activity details: name, duration, location
- Travel time between stops
- Visual pace indicators

**Key Features:**
- Responsive design
- Expand/collapse for details
- Clean, modern UI (TailwindCSS)

**Test:** Display sample itinerary and verify formatting.

### Step 7.3: Sources View Component

**Create `frontend/src/components/SourcesView.tsx`:**

**Display:**
- Citations grouped by day/activity
- Clickable links to sources
- OpenStreetMap source IDs
- Wikivoyage URLs

**Test:** Display citations and verify links work.

### Step 7.4: Transcript Display Component

**Create `frontend/src/components/TranscriptDisplay.tsx`:**

**Display:**
- Conversation history
- User messages and assistant responses
- Auto-scroll to latest
- Clean typography

**Test:** Display conversation and verify scrolling.

### Step 7.5: Explanation Panel Component

**Create `frontend/src/components/ExplanationPanel.tsx`:**

**Display:**
- Explanation text
- Citations
- Expandable format

**Test:** Display explanations and verify citations.

### Step 7.6: API Integration

**Create `frontend/src/services/api.ts`:**

**Functions:**
- `sendMessage(text: string) -> Promise<Response>`
- `planTrip(input: string) -> Promise<Itinerary>`
- `editItinerary(input: string) -> Promise<Itinerary>`
- `explainDecision(input: string) -> Promise<Explanation>`

**Test:** Connect frontend to backend API.

---

## Phase 8: n8n Integration

### Step 8.1: n8n Workflow Setup

**Create `n8n-workflows/pdf-email-workflow.json`:**

**Workflow Steps:**
1. **Webhook Trigger**: Receive itinerary data
2. **Generate PDF**: Use Puppeteer or pdfkit
   - Include: itinerary, activities, travel times, sources
   - Professional layout
3. **Send Email**: SMTP or SendGrid
   - Attach PDF
   - Include summary in body
4. **Return Response**: Success/failure status

**PDF Template:**
- Header: Trip to [City]
- Day-wise itinerary
- Activity details
- Travel times
- Sources/citations

**Test:** Trigger workflow and verify PDF generation and email.

### Step 8.2: Backend Webhook Integration

**Add to `backend/src/main.py`:**

**Endpoint:**
```python
@app.post("/api/generate-pdf")
async def generate_pdf(itinerary_data: dict):
    # Call n8n webhook
    # Return download URL or confirmation
```

**Test:** Call endpoint and verify n8n workflow triggers.

---

## Phase 9: Testing & Deployment

### Step 9.1: Unit Tests

**Create test files:**
- `tests/test_feasibility.py`: Test feasibility evaluator
- `tests/test_grounding.py`: Test grounding evaluator
- `tests/test_edits.py`: Test edit correctness

**Run tests:**
```bash
pytest tests/
```

### Step 9.2: Integration Tests

**Test end-to-end flows:**
1. Trip planning flow
2. Edit flow
3. Explanation flow
4. Evaluation checks

### Step 9.3: Frontend Deployment

**Deploy to Vercel:**
```bash
cd frontend
vercel deploy
```

**Configure:**
- Environment variables
- API URL
- Domain

### Step 9.4: Backend Deployment

**Deploy to Railway/Render:**
1. Connect GitHub repository
2. Set environment variables
3. Configure build command
4. Set health check endpoint

**Verify:**
- API endpoints accessible
- ChromaDB persistence works
- MCP connections work

### Step 9.5: Final Testing

**Test complete system:**
1. Voice input → Trip planning
2. Voice edit → Itinerary update
3. Explanation questions
4. PDF generation
5. Evaluation checks

---

## 🎯 Implementation Checklist

### Phase 1: Infrastructure
- [ ] Project structure created
- [ ] Backend skeleton (FastAPI)
- [ ] Frontend skeleton (Next.js)
- [ ] Git initialized

### Phase 2: Data Integration
- [ ] OpenStreetMap integration
- [ ] Wikivoyage scraper
- [ ] RAG vector store
- [ ] Retriever implementation

### Phase 3: MCP Tools
- [ ] POI Search MCP
- [ ] Itinerary Builder MCP
- [ ] MCP client wrapper

### Phase 4: Orchestration
- [ ] Conversation manager
- [ ] Intent classifier
- [ ] Main orchestrator

### Phase 5: Editing & Explanation
- [ ] Voice edit handler
- [ ] Explanation generator

### Phase 6: Evaluation
- [ ] Feasibility evaluator
- [ ] Edit correctness evaluator
- [ ] Grounding evaluator

### Phase 7: Frontend
- [ ] Voice input component
- [ ] Itinerary view
- [ ] Sources view
- [ ] Transcript display
- [ ] Explanation panel

### Phase 8: n8n
- [ ] PDF generation workflow
- [ ] Email integration
- [ ] Backend webhook

### Phase 9: Deployment
- [ ] Unit tests
- [ ] Integration tests
- [ ] Frontend deployed
- [ ] Backend deployed
- [ ] Final testing

---

## 📝 Notes

- Test after each phase
- Commit code frequently
- Document API endpoints
- Handle errors gracefully
- Focus on grounding and evaluation
- Keep UI simple but functional

---

**Good luck with your implementation!** 🚀
