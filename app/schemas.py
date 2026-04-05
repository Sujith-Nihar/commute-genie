from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., description="User transportation question")
    user_id: Optional[str] = "default_user"


class AskResponse(BaseModel):
    answer: str
    approved: bool
    used_agents: List[str]
    trace: Dict[str, Any]