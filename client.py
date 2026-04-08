from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from .models import PiiRedactorAction, PiiRedactorObservation, PiiRedactorState

class PiiRedactorEnvClient(EnvClient[PiiRedactorAction, PiiRedactorObservation, PiiRedactorState]):
    
    def _step_payload(self, action: PiiRedactorAction) -> Dict:
        return {
            "redacted_text": action.redacted_text,
        }

    def _parse_result(self, payload: Dict) -> StepResult[PiiRedactorObservation]:
        obs_data = payload.get("observation", {})
        observation = PiiRedactorObservation(
            task_difficulty=obs_data.get("task_difficulty", ""),
            original_text=obs_data.get("original_text", ""),
            feedback=obs_data.get("feedback", "")
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> PiiRedactorState:
        return PiiRedactorState(
            current_task_index=payload.get("current_task_index", 0),
            total_score=payload.get("total_score", 0.0),
            is_done=payload.get("is_done", False)
        )