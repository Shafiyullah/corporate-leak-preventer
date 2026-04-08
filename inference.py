import asyncio
import os
import textwrap
from typing import List, Optional
from openai import OpenAI

from models import PiiRedactorAction
from server.pii_redactor_environment import PiiRedactorEnvironment

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "meta-llama/Meta-Llama-3-70B-Instruct"
TASK_NAME = "corporate_leak_eval"
BENCHMARK = "corporate_leak_preventer"
MAX_STEPS = 5 
TEMPERATURE = 0.1 
MAX_TOKENS = 150

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a strict Corporate Compliance AI. 
    You will be given draft emails and memos. 
    Your ONLY job is to return the exact same text, but replace highly confidential information (Company Names being acquired, Money Amounts, Secret Project Names, and Dates) with the exact string: [REDACTED].
    Do NOT redact normal numbers like tester counts. 
    Do not add conversational filler, just return the redacted text.
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
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
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return ""

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = PiiRedactorEnvironment()
    
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset()
        obs = result.observation

        for step in range(1, MAX_STEPS + 1):
            if env.state.is_done:
                break

            message = get_model_message(client, obs.task_difficulty, obs.original_text, obs.feedback)
            action = PiiRedactorAction(redacted_text=message)
            step_result = await env.step(action)
            
            obs = step_result.observation
            reward = step_result.reward or 0.0
            done = step_result.done
            
            rewards.append(reward)
            steps_taken = step
            
            clean_action = message.replace('\n', ' ')
            log_step(step=step, action=clean_action, reward=reward, done=done, error=None)

            if done:
                break

        score = sum(rewards) / 3.0 
        score = min(max(score, 0.0), 1.0)
        success = score >= 0.3

    finally:
        await env.close()
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())