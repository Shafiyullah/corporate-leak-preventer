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
The environment features three distinct levels of difficulty to test the precision of frontier models:
1. **Easy:** Redacting a single financial revenue figure from a draft PR.
2. **Medium:** Identifying and redacting both an acquisition target (company name) and a specific dollar amount within an internal memo.
3. **Hard:** Handling complex scenarios where the agent must redact a secret project name and a launch date, but **must not** redact non-sensitive numbers like tester counts or public order numbers.

## 🚀 Setup and Usage Instructions

### 1. Installation
This project uses `uv` for lightning-fast dependency management.
```bash
# Install dependencies
uv sync