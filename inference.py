import asyncio
import os
import textwrap
from typing import List, Optional
from openai import OpenAI
from pii_redactor.models import PiiRedactorAction
from pii_redactor.server.pii_redactor_environment import PiiRedactorEnvironment

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "meta-llama/Meta-Llama-3-70B-Instruct"
TASK_NAME = "corporate_leak_eval"
BENCHMARK = "corporate_leak_preventer"
MAX_STEPS = 10 
TEMPERATURE = 0.1 
MAX_TOKENS = 150

SYSTEM_PROMPT: str = textwrap.dedent(
    """
    You are a strict Corporate Compliance & Security AI.
    Your ONLY job is to return the EXACT SAME TEXT provided, but replace highly confidential or leaked information with the exact string: [REDACTED].
    
    Confidential information includes:
    - Company Names being acquired or sued
    - Financial Amounts strictly related to unpublished metrics (e.g., $45.2M)
    - Secret Project Names and Internal Server Names (e.g., Project Titan, beta-node-01)
    - Specific Dates linked to unpublished releases (e.g., Nov 15th, the 12th)
    - Employee Names in confidential updates (e.g., Sarah Jenkins)
    - Technical Secrets (AWS Access Keys, API Keys, Session Tokens, Database Passwords, Internal IPs like 10.x.x.x)
    
    CRITICAL INSTRUCTIONS:
    1. Do NOT redact normal numbers like tester counts, public support phone numbers (e.g., 1-800-...), or general configuration counts.
    2. Context preservation is paramount. Do NOT alter, summarize, or destroy the surrounding text, punctuation, or spaces.
    3. Do NOT output any conversational filler, chain of thought, or greeting. Return ONLY the final redacted text.
    
    EXAMPLES:
    Input: "Internal Memo: CEO approved the acquisition of TechFlow Inc. for $1.2B. Please prepare the documents."
    Output: "Internal Memo: CEO approved the acquisition of [REDACTED] for [REDACTED]. Please prepare the documents."
    
    Input: "Support Ticket: Customer called our public line 1-800-555-0199 and accidentally pasted their session token: eyJhbGciOi. Please revoke it."
    Output: "Support Ticket: Customer called our public line 1-800-555-0199 and accidentally pasted their session token: [REDACTED]. Please revoke it."
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    """Log the initialization format for the benchmarking environment."""
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log standard tracking metric output for each discrete environment step."""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Log termination metadata denoting script success, overall score, and final metrics."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def build_user_prompt(difficulty: str, original_text: str, feedback: str) -> str:
    return textwrap.dedent(
        f"""
        Task Difficulty: {difficulty}
        Feedback from last step: {feedback}
        
        Draft to redact: 
        {original_text}
        """
    ).strip()

def get_model_message(client: OpenAI, difficulty: str, original_text: str, feedback: str) -> str:
    user_prompt = build_user_prompt(difficulty, original_text, feedback)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception:
        # Fails silently under framework production rules
        return ""

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = PiiRedactorEnvironment()
    
    rewards: List[float] = []
    steps_taken: int = 0
    score: float = 0.0
    success: bool = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs = env.reset()

        for step in range(1, MAX_STEPS + 1):
            if getattr(env, '_env_state', getattr(env, 'state', None)).is_done:
                break

            message = get_model_message(client, obs.task_difficulty, obs.original_text, obs.feedback)
            action = PiiRedactorAction(redacted_text=message)
            obs = env.step(action)
            
            reward: float = obs.reward
            done: bool = obs.done
            
            rewards.append(reward)
            steps_taken = step
            
            clean_action: str = message.replace('\n', ' ')
            log_step(step=step, action=clean_action, reward=reward, done=done, error=None)

            if done:
                break

        score = sum(rewards) / 10.0 
        score = min(max(score, 0.0), 1.0)
        success = score >= 0.7

    finally:
        env.close()
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())