from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.graph import commutegenie_graph
from app.schemas import AskRequest, AskResponse

app = FastAPI(title="CommuteGenie Singapore Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "CommuteGenie Singapore API is running."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest):
    initial_state = {
        "user_id": payload.user_id,
        "question": payload.question,
        "used_agents": [],
        "trace": {},
        "revision_count": 0,
    }

    result = commutegenie_graph.invoke(initial_state)

    return AskResponse(
        answer=result.get("final_answer", "No answer generated."),
        approved=result.get("critic_result", {}).get("approved", False),
        used_agents=result.get("used_agents", []),
        trace=result.get("trace", {}),
    )