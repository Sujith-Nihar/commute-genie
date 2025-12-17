# Singapore Transport Query Agent  
**LangGraph + OpenAI + LTA DataMall**

## Overview
This project implements an **agentic AI system** that answers natural-language questions about **Singapore public transport**.  
It uses **LangGraph** to orchestrate a structured workflow, **LTA DataMall** as the authoritative real-time data source, and **OpenAI** for intent routing and response generation.

The focus of this submission is **agent design quality, clarity, and deployability**, not perfect accuracy.

---

## What this repository contains
- A **Jupyter Notebook** with:
  - Complete source code for the agentic workflow
  - Execution output for **10 simulated user queries**
  - Detailed inline documentation explaining every design decision
- A **production deployment plan** (FastAPI + Azure)
- Clear mapping to the **evaluation criteria**

---

## Problem statement
Users ask questions such as:
- “When is the next bus arriving at stop 83139?”
- “Are there any traffic incidents right now?”
- “Is there an MRT disruption on the East West Line?”
- “Will buses be crowded due to weather or public holidays?”

The system must:
- interpret intent correctly
- fetch **real-time transport data**
- incorporate **constraints** (time, weather, traffic, holidays)
- return a **grounded, customer-facing answer**

---

## High-level architecture
User Query  
→ Intent Classification  
→ Context Enrichment (time, weather, holidays)  
→ Conditional Tool Execution (LTA APIs)  
→ Grounded Response Generation  

This is implemented explicitly as a **LangGraph state machine**, not a single opaque LLM chain.

---

## Agentic workflow design
The workflow is divided into clear, single-responsibility nodes:

1. **Classify Node**
   - Determines user intent and extracts minimal entities
   - Uses Pydantic validation to ensure structured, safe outputs

2. **Context Node**
   - Attaches constraint signals:
     - Singapore local time + rush hour heuristic
     - Public holidays
     - Current weather

3. **Tool Nodes**
   - Call LTA DataMall endpoints:
     - Bus arrival (v3/BusArrival)
     - Bus stop lookup
     - Traffic incidents
     - Train service alerts
     - Taxi availability

4. **Respond Node**
   - Generates a final answer using **only** tool outputs and context
   - Asks a targeted follow-up if data is missing

This design makes decision-making **explicit, auditable, and testable**.

---

## Constraints handled
The agent systematically reasons over:
- **Time of day & rush hour**
- **Public holidays**
- **Weather conditions**
- **Traffic incidents**
- **Train service disruptions**

Constraints are attached even when the user does not explicitly mention them.

---

## Reliability & scalability considerations
- HTTP retries and timeouts for external APIs
- TTL caching:
  - Reference data (BusStops): hours
  - Real-time data (traffic/train/taxi): seconds
- Stateless per-request design → horizontal scalability

---

## Deployment plan (FastAPI + Azure)

### API layer
The agent is wrapped in a **FastAPI** service:
- `POST /query`
- `GET /health`

### Containerization
- Dockerized FastAPI app
- Environment-variable-based configuration

### Azure deployment
- **Azure Container Apps** (recommended for simplicity)
- **AKS** for enterprise-scale control

### Secrets management
- Secrets stored in **Azure Key Vault**
- Injected at runtime as environment variables

### Observability
- Logs: intent, tool usage, latencies, errors
- Azure Application Insights + Azure Monitor

### CI/CD
- GitHub Actions:
  - run tests
  - build Docker image
  - deploy to Azure

---

## Evaluation criteria mapping
- **Agentic workflow design:** explicit LangGraph routing
- **Variety of constraints:** time, weather, holidays, traffic
- **Solution structure:** typed state, isolated tools, caching
- **Clarity & documentation:** inline notebook + this README
- **Deployment understanding:** FastAPI, Azure, scaling strategy

---

## How to run locally
1. Open the notebook
2. Install dependencies
3. Set environment variables:
   - `OPENAI_API_KEY`
   - `LTA_ACCOUNT_KEY`
4. Run all cells

---

## Final note
This project prioritizes **clarity, robustness, and real-world deployability**, aligning closely with the take-home assessment goals.
