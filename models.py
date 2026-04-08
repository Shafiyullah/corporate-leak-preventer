from pydantic import BaseModel, Field

class PiiRedactorAction(BaseModel):
    redacted_text: str = Field(..., description="The text with PII replaced by [REDACTED]")

class PiiRedactorObservation(BaseModel):
    task_difficulty: str
    original_text: str
    feedback: str = "Redact the sensitive information using [REDACTED]."

class PiiRedactorState(BaseModel):
    current_task_index: int = 0
    total_score: float = 0.0
    is_done: bool = False