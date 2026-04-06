# CommuteGenie Singapore

CommuteGenie Singapore is a multi-agent AI system for intelligent public transportation assistance in Singapore.

It uses real-time transportation signals from **LTA DataMall**, contextual signals such as **Singapore time, rush hour, and public holidays**, and **Gemini** for reasoning and response generation.

The system follows a **manager-worker-reflection architecture** implemented using **LangGraph**, with a **FastAPI backend** and a **Streamlit frontend**.

---

## 👥 Team Members

- **Sujith Thota** – System architecture, Manager Agent, Context Agent, backend orchestration  
- **Lakshmi Naga Hrishitaa Dharmavarapu** – Bus Agent, Train Agent, frontend, documentation  
- **Shared Work** – Critic Agent, testing, prompt refinement, integration  

---

## 📌 Project Overview

Commuters often need to check multiple sources before making a transportation decision, such as:
- bus arrival timings
- MRT / train disruptions
- traffic incidents
- taxi availability
- commute context such as rush hour or public holidays

Instead of switching between different apps, CommuteGenie provides a single conversational interface where the user can ask transportation-related questions in natural language.

---

## 🧠 Architecture

### Agents:
- Manager / Orchestrator Agent  
- Transport Agent  
- Context Agent  
- Critic / Reflection Agent  

### Flow:
User → Streamlit → FastAPI → LangGraph → Manager → Transport + Context → Manager → Critic → Final Answer

---

## ⚙️ Technology Stack

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

## 📂 Project Structure

commutegenie_sg/
├── app/
├── frontend/
├── requirements.txt
├── .env
└── README.md

---

## 🚀 How to Run

### 1. Clone the repository
git clone <your-classroom-repo-link>
cd <repo-name>

### 2. Install dependencies
pip install -r requirements.txt

### 3. Setup environment variables
Create a `.env` file:
GOOGLE_API_KEY=your_gemini_api_key
MODEL_NAME=gemini-1.5-flash
LTA_ACCOUNT_KEY=your_lta_key
DEFAULT_COUNTRY=Singapore

### 4. Run backend
uvicorn app.main:app --reload

### 5. Run frontend
streamlit run frontend/streamlit_app.py

---

## 💡 Example Queries

- When is the next bus arriving at stop 83139?
- Any MRT disruption right now?
- Are taxis available right now?
- Will rush hour affect my commute?

---

## ✅ Features Implemented

- Multi-agent coordination using LangGraph  
- Real-time transport data integration  
- Context-aware reasoning  
- Reflection-based answer validation  
- Streamlit conversational UI  

---

## ⚠️ Current Limitations

- Weather is placeholder  
- No route planning yet  
- No long-term memory  
- In-memory caching only  

---

## 🔮 Future Improvements

- Real weather API integration  
- Route planning  
- RAG-based knowledge retrieval  
- Redis caching  
- User personalization  

---

## 📊 Summary

CommuteGenie demonstrates a multi-agent AI system combining:
- real-time APIs  
- contextual reasoning  
- LLM-based generation  
- reflection validation  

This makes the system modular, explainable, and scalable for real-world transport use.
