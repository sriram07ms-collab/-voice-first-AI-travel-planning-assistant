# Voice-First AI Travel Planning Assistant

A capstone project building a voice-first AI travel planning assistant that understands spoken trip requests, generates realistic itineraries, allows voice-based edits, and explains decisions with grounded data sources.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Core Capabilities](#core-capabilities)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Implementation Guide](#implementation-guide)
- [Evaluation Criteria](#evaluation-criteria)
- [Deployment](#deployment)

## 🎯 Project Overview

Build a deployed voice-mode travel planner that:
- Collects trip preferences conversationally (max 6 clarifying questions)
- Creates feasible day-wise itineraries grounded in real data
- Allows voice-based itinerary modifications
- Explains decisions with citations
- Generates PDF itineraries via n8n workflow

## 📝 Problem Statement

People don't struggle to find places to visit. They struggle to turn preferences, time constraints, travel effort, weather, and personal pace into a **doable plan**.

This system bridges that gap by providing an AI assistant that creates realistic, grounded, and editable travel plans through natural voice interaction.

## ✨ Core Capabilities

### 1. Voice-Based Trip Planning
- Accepts spoken inputs: *"Plan a 3-day trip to Jaipur next weekend. I like food and culture, relaxed pace."*
- Asks clarifying questions only when required (maximum 6)
- Confirms constraints before generating plan

### 2. Voice-Based Editing
- Supports comprehensive edit operations:
  - **Change Pace**: *"Make Day 2 more relaxed"* or *"Make Day 1 faster"*
  - **Swap Entire Days**: *"Swap Day 1 with Day 2"* or *"Swap day 1 itinerary with day 2"*
  - **Move Time Blocks**: *"Swap Day 1 evening with Day 2 evening"* or *"Move Day 1 morning to Day 2 afternoon"*
  - **Add Activities**: *"Add one famous local food place"* or *"Add a museum to Day 2"*
  - **Add Days**: *"Add one more day"* or *"Extend the itinerary"*
  - **Remove Activities**: *"Remove the shopping stop from Day 2"*
  - **Reduce Travel Time**: *"Reduce travel time between activities"*
  - **Regenerate Time Blocks**: *"Plan something new for Day 1 evening"*
- Handles voice transcription variations (e.g., "play one" = "swap day 1")
- Only modifies affected itinerary sections, preserving unchanged days and activities

### 3. Explanation & Reasoning
- Answers various question types with grounded explanations:
  - **POI Selection**: *"Why did you pick Hawa Mahal?"* or *"Why did you pick this place?"*
  - **Timing Questions**: *"Why is this activity scheduled at this time?"*
  - **Feasibility**: *"Is this plan doable?"* or *"Is this itinerary feasible?"*
  - **Weather Scenarios**: *"What if it rains?"* or *"What's the weather forecast?"*
  - **General Questions**: Any other questions about the itinerary
- Provides explanations with citations from Wikivoyage, OpenStreetMap, and weather APIs
- Uses RAG (Retrieval-Augmented Generation) to ground responses in real travel data

### 4. Companion UI
- Day-wise itinerary display (Day 1 / Day 2 / Day 3)
- Morning / Afternoon / Evening blocks
- Duration and travel time between stops
- Live transcript display
- Sources/References section

### 5. PDF Generation & Email (n8n)
- Generates PDF itinerary
- Emails to user automatically

## 🏗️ System Architecture

The system is organized into four main layers:

- **User Interface Layer**: Next.js frontend with voice input, itinerary display, live transcript, and sources.
- **Orchestration Layer (LLM + MCP)**: Python backend that manages conversation state, intent recognition, and calls MCP tools.
- **Data & Knowledge Layer**: RAG over travel content plus live APIs (OpenStreetMap, Wikivoyage, weather).
- **Evaluation Layer**: Feasibility, edit-correctness, and grounding evaluators used in tests and runtime.

High‑level architecture diagram:

```
┌─────────────────────────────────────────────────────────────────┐
│                       User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Voice Input  │  │ Companion UI │  │ Live Transcript     │   │
│  │ (STT)        │  │ (Itinerary)  │  │ & Sources Display   │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────────────────┘   │
└─────────┼──────────────────┼────────────────────────────────────┘
          │                  │
┌─────────┼──────────────────┼────────────────────────────────────┐
│         │        Orchestration Layer (LLM + MCP)               │
│  ┌──────▼──────────────────▼─────────────────────┐             │
│  │  Main Orchestrator (LLM)                      │             │
│  │  - Intent Recognition                         │             │
│  │  - Conversation Management                    │             │
│  │  - Decision Explanation                       │             │
│  └──────┬──────────────────┬─────────────────────┘             │
│         │                  │                                   │
│  ┌──────▼──────┐  ┌────────▼─────────┐  ┌──────────────┐      │
│  │ POI Search  │  │ Itinerary Builder│  │ Travel/Weather│      │
│  │ MCP Tool    │  │ MCP Tool         │  │ MCP Tools     │      │
│  └─────────────┘  └──────────────────┘  └──────────────┘      │
└─────────┼──────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                    Data & Knowledge Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ RAG System   │  │ OpenStreetMap│  │ Weather API         │   │
│  │ (Wikivoyage) │  │ (Overpass)   │  │ (Open-Meteo)        │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                        Evaluation Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Feasibility  │  │ Edit         │  │ Grounding &         │   │
│  │ Evaluator    │  │ Correctness  │  │ Hallucination Check │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                      External Services                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ n8n Workflow: PDF Generation + Email                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

## 🔧 Technology Stack

### Frontend
- **Framework**: Next.js 14 (React) SPA
- **Styling**: TailwindCSS
- **Voice**: Web Speech API (browser speech‑to‑text) + text input
- **Maps & Travel Time**: Google Maps JavaScript / embed + backend travel time API (Google Maps Directions)
- **Deployment**: GitHub Pages via GitHub Actions (`deploy-frontend-pages.yml`)

### Backend
- **Framework**: Python FastAPI
- **LLM Provider**: Groq API (xAI)
- **LLM Model**: `llama3-70b-8192` (configured via `GROQ_MODEL`)
- **Conversation Orchestration**: Custom `TravelOrchestrator` (intent classification, session management, MCP calls)
- **MCP**: Model Context Protocol servers for POI search, itinerary building, and weather
- **Deployment**: Render (containerized backend with persistent ChromaDB volume)

### Data & RAG
- **Vector DB**: ChromaDB (local persistent store, see `backend/src/rag/vector_store.py`)
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Primary Data Sources**:
  - Google Places API (POIs and rich place metadata)
  - Google Maps Directions API (real‑time travel time and distance)
  - OpenStreetMap (Overpass API) as POI fallback and for `source_id` grounding
  - Wikivoyage / Wikipedia (city guides, tips, safety, cultural context)
  - Open‑Meteo API (weather forecasts used in planning and explanations)

### External Services
- **n8n**: Self‑hosted or n8n.cloud for PDF + email workflow
- **PDF**: External HTML→PDF service (e.g. htmlpdfapi.com or Gotenberg) called from n8n
- **Email**: SMTP (typically Gmail App Password) configured in n8n

## 🧩 MCP Tools Used

The backend exposes three core MCP tools (see `mcp-tools/`):

- **POI Search MCP** (`mcp-tools/poi-search/server.py`): Uses Google Places API first (with OpenStreetMap/Overpass fallback) to find POIs for a given city, interests, and constraints, returning ranked POIs with metadata and `source_id`s.
- **Itinerary Builder MCP** (`mcp-tools/itinerary-builder/server.py`): Takes candidate POIs and user constraints and returns a structured, day‑wise itinerary that respects pace and feasibility rules.
- **Weather MCP** (`mcp-tools/weather/server.py`): Calls Open‑Meteo and related weather data sources so the orchestrator can answer *“What if it rains?”* and adjust itineraries for weather.

These MCP tools are called from the backend orchestrator layer (see `backend/src/orchestrator/`), and can also be run independently as MCP servers.

## 📁 Project Structure

```
voice-first-travel-assistant/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceInput.tsx          # Microphone button & STT
│   │   │   ├── TranscriptDisplay.tsx   # Live transcript
│   │   │   ├── ItineraryView.tsx       # Day-wise itinerary display
│   │   │   ├── SourcesView.tsx         # Citations display
│   │   │   └── ExplanationPanel.tsx    # Why questions
│   │   ├── hooks/
│   │   │   └── useSpeechRecognition.ts
│   │   ├── services/
│   │   │   └── api.ts                  # Backend API client
│   │   └── App.tsx
│   ├── package.json
│   └── README.md
│
├── backend/
│   ├── src/
│   │   ├── main.py                     # FastAPI app
│   │   ├── orchestrator/
│   │   │   ├── conversation_manager.py # Conversation state
│   │   │   ├── intent_classifier.py    # Intent recognition
│   │   │   └── orchestrator.py         # Main LLM coordinator
│   │   ├── mcp/
│   │   │   ├── poi_search_mcp.py       # POI Search MCP
│   │   │   ├── itinerary_builder_mcp.py # Itinerary Builder MCP
│   │   │   ├── travel_time_mcp.py      # Travel Time MCP (optional)
│   │   │   └── mcp_client.py           # MCP client wrapper
│   │   ├── rag/
│   │   │   ├── vector_store.py         # ChromaDB setup
│   │   │   ├── retriever.py            # Semantic search
│   │   │   └── data_loader.py          # Wikivoyage scraper
│   │   ├── evaluation/
│   │   │   ├── feasibility_eval.py     # Feasibility checks
│   │   │   ├── edit_correctness_eval.py # Edit validation
│   │   │   └── grounding_eval.py       # Grounding checks
│   │   ├── data_sources/
│   │   │   ├── openstreetmap.py        # Overpass API client
│   │   │   ├── wikivoyage.py           # Wikivoyage scraper
│   │   │   └── weather.py              # Weather API (optional)
│   │   └── utils/
│   │       └── config.py               # Configuration
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── mcp-tools/
│   ├── poi-search/
│   │   ├── server.py                   # POI Search MCP server
│   │   └── requirements.txt
│   ├── itinerary-builder/
│   │   ├── server.py                   # Itinerary Builder MCP server
│   │   └── requirements.txt
│   └── README.md
│
├── n8n-workflows/
│   ├── pdf-email-workflow.json         # n8n workflow export
│   └── README.md
│
├── tests/
│   ├── test_feasibility.py
│   ├── test_grounding.py
│   └── test_edits.py
│
├── docs/
│   ├── API.md
│   └── DEPLOYMENT.md
│
├── .gitignore
├── README.md
└── IMPLEMENTATION_GUIDE.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (get from https://console.groq.com/keys)
- (Optional) n8n instance

### Environment Variables

Create `.env` files in both `frontend/` and `backend/`:

**backend/.env**:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama3-70b-8192  # Best model for quality
DATABASE_URL=postgresql://...  # Optional for conversation state
CHROMA_PERSIST_DIR=./chroma_db
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
OPEN_METEO_API_URL=https://api.open-meteo.com/v1
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/...
```

**frontend/.env.local**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📖 Implementation Guide

See [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for detailed step-by-step implementation instructions.

### Quick Overview

1. **Phase 1**: Project setup and skeleton
2. **Phase 2**: Data integration (OpenStreetMap, Wikivoyage, RAG)
3. **Phase 3**: MCP tools implementation
4. **Phase 4**: Orchestration layer
5. **Phase 5**: Editing and explanation features
6. **Phase 6**: Evaluation system
7. **Phase 7**: Frontend components
8. **Phase 8**: n8n integration
9. **Phase 9**: Testing and deployment

## ✅ Evaluation Criteria

### Feasibility Evaluation
- ✅ Daily duration ≤ available time (9 AM - 10 PM = 13 hours max)
- ✅ Travel time between stops < 30 min (walking) or < 1 hour (transport)
- ✅ Pace consistency (relaxed = 2-3 activities/day, moderate = 3-4, fast = 4-5)

### Edit Correctness Evaluation
- ✅ Only intended day/section modified
- ✅ Other days unchanged
- ✅ Edit intent correctly interpreted

### Grounding & Hallucination Evaluation
- ✅ All POIs have valid OpenStreetMap `source_id`
- ✅ All tips cite Wikivoyage URLs
- ✅ Missing data explicitly stated ("I couldn't find opening hours for X")

## 📊 Datasets & External APIs

### Required Data Sources
1. **Google Places + Maps APIs**
   - Primary POI search (places, ratings, types, coordinates)
   - Real‑time travel time and distance between stops
   - Used by POI Search MCP and travel time estimator

2. **OpenStreetMap (Overpass API)**
   - Fallback POI search when Google APIs are unavailable
   - Location data (lat/lon), categories, metadata
   - Stable `source_id`s for grounding and evaluation

3. **Wikivoyage / Wikipedia**
   - City guides and travel tips
   - Safety information
   - Cultural context
   - Indoor alternatives

4. **Open‑Meteo**
   - Daily/hourly weather forecast for trip dates
   - Used by the Weather MCP and explanation generator

## 🔍 How to Run Evals

All tests use `pytest` from the repo root (ensure `backend` dependencies are installed first).

- **Feasibility evaluator**: `pytest tests/test_feasibility.py -v`
- **Edit correctness evaluator**: `pytest tests/test_edits.py -v`
- **Grounding & hallucination evaluator**: `pytest tests/test_grounding.py -v`
- **End‑to‑end integration flows**: `pytest tests/test_integration.py -v`
- **Additional phase tests**: `pytest tests/test_phase*.py -v`

Each evaluator can also be imported directly from `backend/src/evaluation/` for programmatic evaluation.

## 🗣️ Sample Test Conversation Transcript

This is an example of an end‑to‑end interaction the system is designed to handle:

1. **User**: "Plan a 3‑day trip to Jaipur next weekend. I like food and culture, relaxed pace."
2. **Assistant**: Asks up to a few clarifying questions (dates, party size, budget).
3. **Assistant**: Returns a 3‑day itinerary with morning/afternoon/evening blocks, travel times, and cited sources.
4. **User**: "Make Day 2 more relaxed and add one famous local food place."
5. **Assistant**: Applies a focused edit to Day 2 only, re‑runs feasibility/grounding checks, and explains what changed and why.

## 🚢 Deployment

### Frontend
- Deploy to Githubpages
- Connect to backend API URL
- Ensure environment variables are set

### Backend
- Deploy to Render
- Set environment variables
- Ensure ChromaDB persistence works
- Health check endpoint: `/health`

### n8n
- Set up n8n instance (self-hosted or cloud)
- Import workflow from `n8n-workflows/pdf-email-workflow.json`
- Configure webhook URL in backend

## 📚 Key Design Decisions

1. **Voice-First**: Primary input is voice (STT), with text fallback
2. **Grounded Data**: Every recommendation must cite sources
3. **Edit Scope**: Only modify affected sections, preserve rest
4. **Conversation Limits**: Max 6 clarifying questions before planning
5. **Error Handling**: Graceful degradation when data unavailable

## 🎯 Success Metrics

- ✅ System generates feasible itineraries
- ✅ All POIs grounded in real data
- ✅ Edits modify only intended sections
- ✅ Natural voice conversation flow
- ✅ Accessible via public URL
- ✅ PDF generation and email working

## 📝 License

This is a capstone project for educational purposes.

## 🤝 Contributing

This is a capstone project. Implementation should follow the step-by-step guide in `IMPLEMENTATION_GUIDE.md`.

---

**Note**: This project must demonstrate real GenAI system capabilities, not just a prompt-based demo. Focus on grounding, evaluation, and user experience.
