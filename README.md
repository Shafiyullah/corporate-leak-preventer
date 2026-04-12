---
title: PII Redactor
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Corporate Leak Preventer (OpenEnv)

## 🎯 Description and Motivation
In the high-stakes world of corporate finance and tech, a single accidental leak can cost a company billions in market cap or ruin a secret acquisition. 

The **Corporate Leak Preventer** is a specialized Reinforcement Learning (RL) environment designed to train and evaluate AI agents on their ability to act as strict compliance filters. The agent's goal is to scan internal memos and draft press releases to identify and redact unreleased quarterly earnings, acquisition targets, and secret project codenames using `[REDACTED]`, while ensuring that the surrounding professional context remains untouched.

## 🛠️ Action and Observation Space
* **Observation Space:** The agent receives a `PiiRedactorObservation` containing:
    * `task_difficulty`: (Easy, Medium, or Hard)
    * `original_text`: The raw draft containing sensitive data.
    * `feedback`: Guidance from the compliance engine based on previous performance.
* **Action Space:** The agent submits a `PiiRedactorAction` containing:
    * `redacted_text`: The sanitized version of the draft.

## 📈 Tasks & Difficulty Levels
The environment features **10 distinct scenarios** mapped across three difficulty levels to robustly stress-test the compliance and precision of frontier models:
1. **Easy:** Redacting a single financial revenue figure or employee name from a draft PR.
2. **Medium:** Identifying and redacting acquisition targets, dollar amounts, internal IPs, and leaked secret keys (e.g., AWS Secrets).
3. **Hard:** Handling highly-complex "trap" scenarios where the agent must redact a session token or database password while explicitly **ignoring** public support phone numbers and standard volume counts. The model must thread the needle to maintain syntax while omitting the specific secret.

## 🏆 Benchmark & Evaluation
The automated benchmark runner (`inference.py`) tests agents against the 10-task suite sequentially. 

**Prompt Engineering Breakthrough:** By using a structured few-shot prompt with explicit negative constraint bounding ("Do not redact normal numbers like public support phone numbers"), our baseline agent **(Meta-Llama-3-70B-Instruct)** achieved a flawless **10/10 Score (1.000 Reward)**. It successfully prevented all PII leakage without destroying context.

## 🚀 Setup and Usage Instructions

### 1. Installation
This project uses `uv` for lightning-fast dependency management.
```bash
# Install dependencies
uv sync