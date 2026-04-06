# CommuteGenie Singapore

CommuteGenie Singapore is a multi-agent AI system for intelligent public transportation assistance in Singapore.

It uses real-time transportation signals from **LTA DataMall**, contextual signals such as **Singapore time, rush hour, and public holidays**, and **Gemini** for reasoning and response generation.

The system follows a **manager-worker-reflection architecture** implemented using **LangGraph**, with a **FastAPI backend** and a **Streamlit frontend**.

---

## 👥 Team Members

- **Sujith Thota (sthot10)** – System architecture, Manager Agent, Context Agent, backend orchestration  
- **Lakshmi Naga Hrishitaa Dharmavarapu (ldhar)** – Transport Agent, frontend, documentation  
- **Shared Work** – Critic Agent, testing, prompt refinement, integration  

---

## Project Overview

Commuters often need to check multiple sources before making a transportation decision, such as:
- bus arrival timings
- MRT / train disruptions
- traffic incidents
- taxi availability
- commute context such as rush hour or public holidays

Instead of switching between different apps, CommuteGenie provides a single conversational interface where the user can ask transportation-related questions in natural language.

Example questions:
- When is the next bus arriving at stop 83139?
- Are there any MRT disruptions right now?
- Is traffic bad at the moment?
- Are taxis available right now?
- Will rush hour affect my commute today?

The system retrieves relevant transportation and contextual data, coordinates multiple agents, and generates a grounded natural-language answer.

---

## Architecture

### Architecture Style

This project uses a **multi-agent architecture** with the following agents:
- **Manager / Orchestrator Agent**
- **Transport Agent**
- **Context Agent**
- **Critic / Reflection Agent**

The workflow is implemented using **LangGraph**.

### High-Level Flow

```
User
  ↓
Streamlit Frontend
  ↓
FastAPI Backend
  ↓
LangGraph Workflow
  ↓
Manager Agent
  ↓
Transport Agent + Context Agent
  ↓
Manager Agent (response drafting)
  ↓
Critic Agent
  ↓
Final Answer
```

---

## Technology Stack

### Backend
- FastAPI
- LangGraph
- LangChain
- Gemini (Google Generative AI)

### Frontend
- Streamlit

### Data Sources
- LTA DataMall
- Singapore time and holiday context

---

## Project Structure

```text
commutegenie_sg/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── prompts.py
│   ├── state.py
│   ├── graph.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── llm_service.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── manager_agent.py
│   │   ├── transport_agent.py
│   │   ├── context_agent.py
│   │   └── critic_agent.py
│   │
│   └── tools/
│       ├── __init__.py
│       ├── lta_client.py
│       ├── transit_tools.py
│       └── context_tools.py
│
├── frontend/
│   └── streamlit_app.py
│
├── .env
├── requirements.txt
└── README.md
```

---

# 🚀 How to Run (IMPORTANT)

### 1. Clone the repository

```
git clone https://github.com/cs494-agentic-ai-spring-2026/group-project-code-submission-team6_commutegenie-2.git
cd group-project-code-submission-team6_commutegenie-2
```

---

### 2. Install dependencies

```
pip install -r requirements.txt
```

---

### 3. Configure environment variables

Create a `.env` file:

```
GOOGLE_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-1.5-flash
LTA_ACCOUNT_KEY=your_lta_datamall_account_key_here
DEFAULT_COUNTRY=Singapore
```

---

### 4. Run backend

```
uvicorn app.main:app --reload
```

---

### 5. Run frontend

```
streamlit run frontend/streamlit_app.py
```

---

## Example Queries

- When is the next bus arriving at stop 83139?  
- Find bus stop code for Lucky Plaza  
- Any MRT disruption right now?  
- Any traffic incidents now?  
- Are taxis available right now?  
- Will rush hour affect travel now?  

---

## Summary

CommuteGenie Singapore is a modular multi-agent transportation assistant built with:
- FastAPI  
- Streamlit  
- LangGraph  
- Gemini  
- LTA DataMall  

It uses a manager-worker-critic architecture to combine:
- real-time transport data  
- contextual signals  
- LLM-based reasoning  
- reflection-based answer validation  

This makes the system:
- modular  
- explainable  
- extensible  
- suitable for coursework and future enhancement  
