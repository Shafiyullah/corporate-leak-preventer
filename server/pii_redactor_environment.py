from models import PiiRedactorAction, PiiRedactorObservation, PiiRedactorState

TASKS = [
    {
        "difficulty": "Easy",
        "text": "Draft PR: We are thrilled to announce our Q3 revenue hit a record $45.2M, beating expectations.",
        "pii_to_hide": ["$45.2M"],
        "context_to_keep": ["Draft PR: We are thrilled to announce our Q3 revenue hit a record", ", beating expectations."]
    },
    {
        "difficulty": "Medium",
        "text": "Internal Memo: CEO approved the acquisition of TechFlow Inc. for $1.2B. Please prepare the documents.",
        "pii_to_hide": ["TechFlow Inc.", "$1.2B"],
        "context_to_keep": ["Internal Memo: CEO approved the acquisition of", "for", ". Please prepare the documents."]
    },
    {
        "difficulty": "Hard",
        "text": "CONFIDENTIAL: Project Titan is scheduled for beta release on Nov 15th to a closed group of 500 testers.",
        "pii_to_hide": ["Project Titan", "Nov 15th"],
        "context_to_keep": ["CONFIDENTIAL:", "is scheduled for beta release on", "to a closed group of 500 testers."]
    }
]

class PiiRedactorEnvironment:
    def __init__(self):
        self.state = PiiRedactorState()

    async def reset(self):
        self.state = PiiRedactorState()
        first_task = TASKS[self.state.current_task_index]
        
        class ResetResult:
            def __init__(self, obs):
                self.observation = obs
                
        obs = PiiRedactorObservation(
            task_difficulty=first_task["difficulty"],
            original_text=first_task["text"],
            feedback="Initial task loaded. Redact the unreleased corporate data."
        )
        return ResetResult(obs)

    async def step(self, action: PiiRedactorAction):
        if self.state.is_done:
            raise ValueError("Environment is already done. Please reset().")

        current_task = TASKS[self.state.current_task_index]
        agent_text = action.redacted_text
        
        reward = 0.0
        feedback_msg = ""
        
        pii_hidden = True
        for secret in current_task["pii_to_hide"]:
            if secret in agent_text:
                pii_hidden = False
                break
                
        context_kept = True
        for context in current_task["context_to_keep"]:
            if context not in agent_text:
                context_kept = False
                break
                
        if pii_hidden and context_kept:
            reward = 1.0
            feedback_msg = "Perfect redaction. Leak prevented."
        elif pii_hidden and not context_kept:
            reward = 0.2 
            feedback_msg = "Data hidden, but surrounding PR context was destroyed."
        elif not pii_hidden and context_kept:
            reward = 0.0
            feedback_msg = "CRITICAL FAILURE: Confidential data leaked."
        else:
            reward = 0.0
            feedback_msg = "Complete failure."

        self.state.total_score += reward
        self.state.current_task_index += 1
        
        done = False
        next_obs = None
        
        if self.state.current_task_index >= len(TASKS):
            done = True
            self.state.is_done = True
            next_obs = PiiRedactorObservation(
                task_difficulty="Finished",
                original_text="",
                feedback="All compliance checks complete."
            )
        else:
            next_task = TASKS[self.state.current_task_index]
            next_obs = PiiRedactorObservation(
                task_difficulty=next_task["difficulty"],
                original_text=next_task["text"],
                feedback=feedback_msg
            )

        class StepResult:
            def __init__(self, obs, rew, is_done):
                self.observation = obs
                self.reward = rew
                self.done = is_done
                
        return StepResult(next_obs, reward, done)

    async def get_state(self):
        return self.state

    async def close(self):
        pass