from typing import Optional, Any, Dict
from openenv.core.env_server import Environment
from pii_redactor.models import PiiRedactorAction, PiiRedactorObservation, PiiRedactorState

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
    },
    {
        "difficulty": "Easy",
        "text": "HR Update: Please welcome Sarah Jenkins to the engineering team. Her desk is in building 4.",
        "pii_to_hide": ["Sarah Jenkins"],
        "context_to_keep": ["HR Update: Please welcome", "to the engineering team. Her desk is in building 4."]
    },
    {
        "difficulty": "Medium",
        "text": "DevOps Alert: The deployment failed because the AWS_SECRET_ACCESS_KEY was set to AKIAIOSFODNN7EXAMPLE in the production manifest.",
        "pii_to_hide": ["AKIAIOSFODNN7EXAMPLE"],
        "context_to_keep": ["DevOps Alert: The deployment failed because the AWS_SECRET_ACCESS_KEY was set to", "in the production manifest."]
    },
    {
        "difficulty": "Medium",
        "text": "SysAdmin: I temporarily whitelisted your requested IP 10.244.15.93 so you can access the internal reporting dashboard.",
        "pii_to_hide": ["10.244.15.93"],
        "context_to_keep": ["SysAdmin: I temporarily whitelisted your requested IP", "so you can access the internal reporting dashboard."]
    },
    {
        "difficulty": "Hard",
        "text": "Support Ticket: Customer called our public line 1-800-555-0199 and accidentally pasted their session token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9. Please revoke it.",
        "pii_to_hide": ["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"],
        "context_to_keep": ["Support Ticket: Customer called our public line 1-800-555-0199 and accidentally pasted their session token:", ". Please revoke it."]
    },
    {
        "difficulty": "Hard",
        "text": "DBA Request: Can you rotate the database password? Right now it is P@ssw0rd!SuperSecret99, which is way too weak for our 5 instances.",
        "pii_to_hide": ["P@ssw0rd!SuperSecret99"],
        "context_to_keep": ["DBA Request: Can you rotate the database password? Right now it is", ", which is way too weak for our 5 instances."]
    },
    {
        "difficulty": "Hard",
        "text": "Legal: We are preparing to settle the lawsuit with Oceanic Corp for $5.5M. Keep this strictly confidential until the 12th.",
        "pii_to_hide": ["Oceanic Corp", "$5.5M", "the 12th"],
        "context_to_keep": ["Legal: We are preparing to settle the lawsuit with", "for", ". Keep this strictly confidential until"]
    },
    {
        "difficulty": "Hard",
        "text": "Infrastructure: We are migrating from server beta-node-01. Please make sure the Stripe API key sk_live_51MabcxyZ123 isn't committed in the open source repo.",
        "pii_to_hide": ["beta-node-01", "sk_live_51MabcxyZ123"],
        "context_to_keep": ["Infrastructure: We are migrating from server", ". Please make sure the Stripe API key", "isn't committed in the open source repo."]
    }
]

class PiiRedactorEnvironment(Environment): 
    def __init__(self):
        super().__init__() 
        self._env_state: PiiRedactorState = PiiRedactorState()

    @property
    def state(self):
        return self._env_state

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None, **kwargs: Any) -> PiiRedactorObservation:
        self._env_state = PiiRedactorState()

        episode_id: Optional[str] = kwargs.get("episode_id", options.get("episode_id") if options else None)
        if episode_id is not None:
            self._env_state.episode_id = str(episode_id)

        first_task: Dict[str, Any] = TASKS[self._env_state.current_task_index]
        difficulty: str = first_task["difficulty"]
        text: str = first_task["text"]
        
        obs = PiiRedactorObservation(
            task_difficulty=difficulty,
            original_text=text,
            feedback="Initial task loaded. Redact the unreleased corporate data.",
        )
        return obs

    def step(self, action: PiiRedactorAction, **kwargs: Any) -> PiiRedactorObservation:
        """
        Evaluate the exact text replacement payload logic.

        Args:
            action (PiiRedactorAction): The parsed Action class containing the LLM redaction target text.
            kwargs (Any): Overflow framework arguments.

        Raises:
            ValueError: If the step is executed when the sequential matrix limit is already breached.

        Returns:
            PiiRedactorObservation: The consequent observation containing the sequential step reward.
        """
        if self._env_state.is_done:
            raise ValueError("Environment is already done. Please reset().")

        current_task: Dict[str, Any] = TASKS[self._env_state.current_task_index]
        agent_text: str = action.redacted_text
        
        reward: float = 0.0
        feedback_msg: str = ""
        
        pii_hidden: bool = True
        for secret in current_task["pii_to_hide"]:
            if secret in agent_text:
                pii_hidden = False
                break
                
        context_kept: bool = True
        for context in current_task["context_to_keep"]:
            if context not in agent_text:
                context_kept = False
                break
                
        if pii_hidden and context_kept:
            if "[REDACTED]" in agent_text:
                reward = 1.0
                feedback_msg = "Perfect redaction. Leak prevented."
            else:
                reward = 0.5
                feedback_msg = "Data hidden and context kept, but failed to use [REDACTED] tag."
        elif pii_hidden and not context_kept:
            reward = 0.2 
            feedback_msg = "Data hidden, but surrounding PR context was destroyed."
        elif not pii_hidden and context_kept:
            reward = 0.0
            feedback_msg = "CRITICAL FAILURE: Confidential data leaked."
        else:
            reward = 0.0
            feedback_msg = "Complete failure."

        self._env_state.total_score += reward
        self._env_state.current_task_index += 1
        self._env_state.step_count += 1
        
        done: bool = False
        next_obs: Optional[PiiRedactorObservation] = None
        
        if self._env_state.current_task_index >= len(TASKS):
            done = True
            self._env_state.is_done = True
            next_obs = PiiRedactorObservation(
                task_difficulty="Finished",
                original_text="",
                feedback="All compliance checks complete.",
                reward=reward,
                done=done
            )
        else:
            next_task = TASKS[self._env_state.current_task_index]
            difficulty = next_task["difficulty"]
            text = next_task["text"]
            next_obs = PiiRedactorObservation(
                task_difficulty=difficulty,
                original_text=text,
                feedback=feedback_msg,
                reward=reward,
                done=done
            )

        return next_obs

    def close(self) -> None:
        """Safely destroy or detach the environment processing instance."""
        pass