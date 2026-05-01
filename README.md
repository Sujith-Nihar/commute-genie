# CommuteGenie Singapore

CommuteGenie Singapore is a multi-agent AI system for intelligent public transportation assistance in Singapore.

It combines real-time signals from **LTA DataMall**, geocoding and routing from **Google Maps (Places + Directions APIs)**, contextual data (Singapore time, rush hour, public holidays, weather), and **Gemini** for LLM reasoning and response generation.

The system follows a **manager–worker–critic architecture** implemented using **LangGraph**, exposed through a **FastAPI backend**, and accessible via a **React/Vite frontend** or a **Streamlit demo UI**.

---

## 👥 Team Members

- **Sujith Thota (sthot10)** – System architecture, Manager Agent, Context Agent, backend orchestration, Google Directions API integration
- **Lakshmi Naga Hrishitaa Dharmavarapu (ldhar)** – Transport Agent, Google Maps API integration, frontend, documentation
- **Shared Work** – Critic Agent, Trip Planner Agent, testing, prompt refinement, integration

---

## Project Overview

Commuters often need to check multiple sources before making a transportation decision:

- Bus arrival timings
- MRT / train disruptions
- Traffic incidents
- Taxi availability
- Rush hour or public holiday context
- End-to-end route recommendations

Instead of switching between apps, CommuteGenie provides a single conversational interface where the user asks transportation-related questions in natural language and receives a concise, grounded answer.

**Example queries:**

- `I want to go from Orchard Road to Marina Bay Sands. What's the best way?`
- `When is the next bus at stop 83139?`
- `Are there any MRT disruptions right now?`
- `Is traffic bad right now?`
- `Are taxis available near me?`
- `Will rush hour affect my commute today?`

---

## Architecture

### Pattern

**Manager–Worker–Critic** on a **LangGraph StateGraph**, with selective real-time data fetching and LLM-based synthesis and reflection.

### Agents

| Agent | Role |
|---|---|
| **Manager Router** | Classifies the query using an LLM and produces a JSON routing plan (which workers to invoke) |
| **Trip Planner** | End-to-end pipeline: geocode → directions → real-time signals → score → draft answer |
| **Transport Agent** | Keyword-based selection of LTA tools (bus, MRT, taxi, traffic) |
| **Context Agent** | Fetches time, public holiday, and weather context |
| **Manager Writer** | Synthesizes worker outputs into a structured draft answer using an LLM |
| **Critic Agent** | Reviews the draft for grounding and format compliance; approves or flags issues |

### LangGraph Workflow

```
[POST /ask]
     │
     ▼
manager_router  ──(LLM routing decision)──────────────────────────────────┐
     │                                                                     │
     ├──[use_trip_planner]────► trip_planner ──────────────────────────► manager_writer
     │                                                                     │
     ├──[transport + context]──► transport_agent ──► context_agent ──► manager_writer
     │                                                                     │
     ├──[transport only]───────► transport_agent ──────────────────────► manager_writer
     │                                                                     │
     ├──[context only]─────────► context_agent ───────────────────────► manager_writer
     │                                                                     │
     └──[none]────────────────────────────────────────────────────────► manager_writer
                                                                           │
                                                                      critic_agent
                                                                           │
                                                                        [END]
```

### Shared State

All nodes share a single `AgentState` TypedDict threaded through the graph:

| Field | Set by |
|---|---|
| `question`, `user_id` | API entry point |
| `manager_plan` | Manager Router |
| `transport_result` | Transport Agent |
| `context_result` | Context Agent |
| `trip_result` | Trip Planner |
| `draft_answer` | Trip Planner or Manager Writer |
| `critic_result`, `final_answer` | Critic Agent |
| `used_agents`, `trace` | All nodes (accumulated) |

---

## Routing Logic

The **Manager Router** sends the user question to Gemini with a structured prompt. The LLM returns a JSON routing plan:

```json
{
  "use_trip_planner": true,
  "use_transport": false,
  "use_context": false,
  "context_needs": [],
  "intent_summary": "User wants a route from Orchard Road to Marina Bay Sands."
}
```

**Routing rules:**
- `use_trip_planner = true` — query involves travelling from A to B (takes priority over all other flags)
- `use_transport = true` — query involves specific LTA lookups (bus arrivals, MRT alerts, taxi, traffic)
- `use_context = true` — query involves time-sensitive factors (rush hour, weather, holidays)
- Both `use_transport` and `use_context` can be true for multi-intent queries
- If none apply, the Manager Writer answers directly from LLM knowledge

---

## Trip Planner Flow

The Trip Planner is a self-contained pipeline that runs entirely within a single LangGraph node:

```
1. Parse origin + destination  →  LLM extracts locations from the question
2. Geocode both endpoints      →  Google Places API (text search, Singapore-biased)
3. Fetch route options         →  Google Directions API (driving + transit modes)
4. Classify errors             →  Distinguish API denial from no-route vs. OK
5. Decide real-time needs      →  Inspect route steps: driving → traffic,
                                  transit → train alerts + bus stops,
                                  long walk → weather
6. Fetch real-time signals     →  Call only the needed LTA / WeatherAPI tools
7. Score and rank routes       →  Apply additive penalty minutes per mode
8. Draft structured answer     →  LLM writes a concise bullet-point response
```

**Scoring penalties (additive minutes):**

| Condition | Penalty |
|---|---|
| Heavy traffic (≥5 incidents) | +15 min to driving/taxi |
| Moderate traffic (2–4 incidents) | +7.5 min to driving/taxi |
| Train disruption | +20 min to transit |
| Bus wait > 15 min | +5 min to transit |
| High weather impact | +10 min (driving/taxi), +20 min (walking) |
| Moderate weather impact | +5 min |
| Each extra transfer | +8 min to transit |

**Fallback behavior:**
If the Google Directions API is unavailable (key missing, billing inactive, or REQUEST_DENIED), the Trip Planner:
1. Still geocodes both locations via Google Places
2. Fetches available LTA real-time signals (train alerts, taxi, time)
3. Produces a general guidance response covering MRT, Taxi/Grab, and Bus options
4. The response clearly notes that precise route data is temporarily unavailable — it never blames the user's locations

---

## Tool / API Layer

### LTA DataMall (`app/tools/lta_client.py`, `app/tools/transit_tools.py`)

| Tool | LTA Endpoint | Data |
|---|---|---|
| `tool_bus_arrival` | `v3/BusArrival` | Next 3 estimated arrivals per service |
| `tool_bus_stops_search` | `BusStops` (paged) | Search bus stop by name/road |
| `tool_nearest_bus_stops` | `BusStops` + Haversine | Closest stops to a coordinate |
| `tool_traffic_incidents` | `TrafficIncidents` | Current road incidents |
| `tool_train_alerts` | `TrainServiceAlerts` | MRT disruption status |
| `tool_taxi_availability` | `Taxi-Availability` | Available taxi positions |
| `tool_nearest_ev_charging_points` | `EVCBatch` | EV charging stations near a location |

LTA tools use a short-lived **TTL cache** (30 seconds for real-time data, 6 hours for static bus stop list) to avoid hammering the API on repeated queries.

### Google Maps (`app/tools/google_maps_client.py`)

| Function | API | Purpose |
|---|---|---|
| `search_place(query)` | Places API v1 (`places:searchText`) | Geocode free-text location to lat/lon |
| `get_directions(origin, destination, modes)` | Directions API (REST) | Fetch route options for driving and transit modes |

Both calls are Singapore-biased (bounding box `1.13°N–1.47°N, 103.60°E–104.10°E`).

### WeatherAPI (`app/tools/context_tools.py`)

Fetches current Singapore weather via `api.weatherapi.com`. Impact is classified as `minimal / low / moderate / high` based on condition keywords (thunderstorm → high, rain → moderate, cloudy → low, clear → minimal). Configured via `OPENWEATHER_API_KEY`.

### Context Tools (`app/tools/context_tools.py`)

| Function | Data |
|---|---|
| `get_sg_time_context()` | Current SG time, hour, weekday, is_rush_hour, is_weekend |
| `get_sg_holiday_context()` | Whether today is a Singapore public holiday |
| `get_weather_context()` | Current weather condition and impact level |

---

## Technology Stack

### Backend
- **FastAPI** — REST API (`POST /ask`, `GET /health`)
- **LangGraph** — StateGraph-based multi-agent orchestration
- **LangChain** — LLM message wrappers
- **Gemini** (`gemini-2.5-flash`) — LLM for routing, writing, and critique
- **LTA DataMall** — Real-time Singapore transit data
- **Google Maps Platform** — Geocoding (Places API) and routing (Directions API)
- **WeatherAPI** — Current Singapore weather

### Frontend
- **React 18 + TypeScript + Vite** — Primary web UI (`frontend/src/`)
- **Streamlit** — Lightweight demo UI (`frontend/streamlit_app.py`)

Both frontends communicate with the FastAPI backend at `POST /ask`.

---

## Project Structure

```text
/
├── app/
│   ├── main.py              # FastAPI app — POST /ask entry point
│   ├── graph.py             # LangGraph StateGraph definition
│   ├── state.py             # AgentState TypedDict
│   ├── config.py            # Settings loaded from .env
│   ├── schemas.py           # AskRequest / AskResponse Pydantic models
│   ├── prompts.py           # All LLM system prompts
│   │
│   ├── agents/
│   │   ├── manager_agent.py       # manager_router_node, manager_writer_node
│   │   ├── transport_agent.py     # transport_agent_node (LTA tools)
│   │   ├── context_agent.py       # context_agent_node (time / holiday / weather)
│   │   ├── critic_agent.py        # critic_agent_node (format + grounding check)
│   │   └── trip_planner_agent.py  # trip_planner_node (geocode → route → score → draft)
│   │
│   ├── services/
│   │   └── llm_service.py         # ChatGoogleGenerativeAI factory
│   │
│   └── tools/
│       ├── lta_client.py          # LTA DataMall HTTP client (retry + pagination)
│       ├── transit_tools.py       # LTA tool functions + TTL cache
│       ├── context_tools.py       # Time, holiday, weather tools
│       ├── google_maps_client.py  # Google Places + Directions API client
│       └── route_tools.py         # Geocoding, scoring, trip result assembly
│
├── frontend/
│   ├── streamlit_app.py     # Streamlit demo (calls POST /ask)
│   ├── src/                 # React/Vite app
│   │   ├── App.tsx
│   │   ├── pages/           # Landing, Chat, About, NotFound
│   │   ├── components/      # Chat UI, layout, shadcn-style components
│   │   └── lib/
│   │       └── api.ts       # Calls POST /ask and GET /health
│   └── package.json
│
├── tests/
│   └── test_trip_planner.py # Integration-style script (runs graph.invoke)
│
├── .env                     # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/cs494-agentic-ai-spring-2026/group-project-code-submission-team6_commutegenie-2.git
cd group-project-code-submission-team6_commutegenie-2
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# Gemini LLM (required)
GOOGLE_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-2.5-flash

# LTA DataMall (required for bus / MRT / taxi / traffic tools)
LTA_ACCOUNT_KEY=your_lta_datamall_account_key_here
DEFAULT_COUNTRY=Singapore

# Google Maps Platform (required for trip planning)
# Enable: Places API (New) and Directions API on the same key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# WeatherAPI (optional — weather context)
# Sign up at https://www.weatherapi.com/
OPENWEATHER_API_KEY=your_weatherapi_key_here
```

| Variable | Required | Used for |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini LLM (routing, writing, critique) |
| `MODEL_NAME` | No (default: `gemini-2.5-flash`) | LLM model selection |
| `LTA_ACCOUNT_KEY` | Yes | All LTA DataMall endpoints |
| `DEFAULT_COUNTRY` | No (default: `Singapore`) | LTA client region |
| `GOOGLE_MAPS_API_KEY` | Yes (for trip planning) | Google Places geocoding + Directions routing |
| `OPENWEATHER_API_KEY` | No | WeatherAPI current conditions |

> **Note:** `GOOGLE_MAPS_API_KEY` must have both the **Places API (New)** and the **Directions API** enabled in Google Cloud Console, with billing active.

---

## How to Run

### Backend (FastAPI)

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check message |
| `GET` | `/health` | Returns `{"status": "ok"}` |
| `POST` | `/ask` | Main endpoint — accepts `{user_id, question}`, returns `{answer, approved, used_agents, trace}` |

**Example request:**

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "question": "I want to go from Orchard Road to Marina Bay Sands. What is the best way?"}'
```

**Example response:**

```json
{
  "answer": "• Best Option:\n  - Transit (~22 min)\n\n• Why:\n  - Fastest with no current train disruptions\n  - Avoids peak-hour road congestion\n\n• Route:\n  - EWL from Somerset → Bayfront, walk to Marina Bay Sands\n\n• Conditions:\n  - Traffic: heavy\n  - Train: normal\n\n• Backup:\n  - Driving (~38 min)",
  "approved": true,
  "used_agents": ["manager_router", "trip_planner", "manager_writer", "critic_agent"],
  "trace": { ... }
}
```

### React / Vite Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`. It connects to the FastAPI backend at `http://127.0.0.1:8000` by default. Override with:

```bash
VITE_API_BASE_URL=http://your-backend-url npm run dev
```

### Streamlit Demo UI

```bash
streamlit run frontend/streamlit_app.py
```

Opens at `http://localhost:8501`. The Streamlit app calls the same `POST /ask` endpoint.

---

## Example User Queries

### Trip Planning

| Query | Agents Invoked |
|---|---|
| `I want to go from Orchard Road to Marina Bay Sands. What's the best way?` | manager_router → trip_planner → manager_writer → critic_agent |
| `How do I get to Changi Airport from Jurong East?` | manager_router → trip_planner → manager_writer → critic_agent |
| `Best route from Tampines MRT to NUS?` | manager_router → trip_planner → manager_writer → critic_agent |

### Transport Lookups

| Query | Agents Invoked |
|---|---|
| `When is the next bus at stop 83139?` | manager_router → transport_agent → manager_writer → critic_agent |
| `Any MRT disruptions right now?` | manager_router → transport_agent → manager_writer → critic_agent |
| `Find bus stop code for Lucky Plaza` | manager_router → transport_agent → manager_writer → critic_agent |
| `Any traffic incidents now?` | manager_router → transport_agent → manager_writer → critic_agent |
| `Are taxis available right now?` | manager_router → transport_agent → manager_writer → critic_agent |

### Context Queries

| Query | Agents Invoked |
|---|---|
| `Will rush hour affect my commute today?` | manager_router → context_agent → manager_writer → critic_agent |
| `Is it raining and are there MRT disruptions?` | manager_router → transport_agent → context_agent → manager_writer → critic_agent |

---

## Testing

`tests/test_trip_planner.py` is an integration-style script that invokes the full LangGraph pipeline directly (no HTTP layer):

```bash
python tests/test_trip_planner.py
```

It runs several trip planning scenarios and prints the router decision, agents used, trip trace, critic result, and final answer for each. Requires a valid `.env` with all API keys configured.

---

## Known Limitations

- **No iteration on critic rejection** — The Critic Agent flags format or grounding issues but the pipeline does not loop back to rewrite. If the critic rejects, its feedback is appended as a note to the final answer. A true revision loop requires adding a back-edge in the LangGraph graph.

- **Hardcoded current location** — "Nearest bus stop" queries that do not include an explicit location fall back to a hardcoded Queensway Shopping Centre coordinate. Real device GPS integration is not implemented.

- **Transport agent is keyword-based** — Tool selection in the Transport Agent uses regex/keyword matching, not LLM tool-calling. Ambiguous or unusually phrased queries may miss relevant tools.

- **Synchronous pipeline** — All LTA and Google API calls within a single request run sequentially. Parallelizing independent calls (e.g., traffic + train alerts + weather) would reduce latency.

- **Single process, in-memory cache** — The TTL cache is per-process. Multi-worker deployments (e.g., `uvicorn --workers 4`) will not share cache state and may issue redundant API calls.

- **Google Directions API billing** — Route planning requires an active Google Cloud billing account with the Directions API enabled. Without it, the system falls back to general guidance mode automatically.

- **WeatherAPI key label** — The environment variable is named `OPENWEATHER_API_KEY` for historical reasons, but the actual provider is [WeatherAPI](https://www.weatherapi.com/), not OpenWeatherMap.

---

## Future Improvements

- Implement the critic revision loop (back-edge in LangGraph from critic to manager_writer)
- Replace keyword-based transport routing with LLM function-calling / tool-use
- Add real user location input (GPS coordinates from the React frontend)
- Parallelize independent real-time API calls with `asyncio.gather`
- Add persistent caching (Redis) for multi-worker and cross-restart cache sharing
- Integrate LangSmith or OpenTelemetry for structured tracing and observability
- Add input validation and rate limiting to the `/ask` endpoint
- Expand route modes (walking, bicycling) and support multi-leg trip planning

---

## Summary

CommuteGenie Singapore is a modular multi-agent transportation assistant built with:

- **FastAPI** — REST backend
- **LangGraph** — stateful multi-agent workflow
- **Gemini** — LLM for routing, writing, and critique
- **LTA DataMall** — real-time Singapore transit data
- **Google Maps Platform** — geocoding and route directions
- **WeatherAPI** — real-time weather context
- **React/Vite** — primary web frontend
- **Streamlit** — lightweight demo frontend

It uses a manager–worker–critic architecture to combine real-time transport data, contextual signals, and LLM reasoning into concise, grounded commuter answers.
# informs-uic-hackathon
