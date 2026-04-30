# AGENTS.md

## 1. Project Overview

This project is a Discord bot for MapleLand.

Core features:

* Fetch notices
* Send notifications
* Summarize updates
* Answer user questions

---

## 2. Tech Stack

* Python 3.11+
* discord.py
* PostgreSQL + SQLAlchemy
* httpx / BeautifulSoup
* OpenAI API
* Docker

---

## 3. Architecture Rules

* bot/: Discord interface only
* services/: business logic
* crawler/: data fetching
* db/: persistence

Rules:

* Do NOT mix responsibilities
* Always use service layer
* Do NOT access DB directly from bot

---

## 4. Code Principles

* Use meaningful names
* Prefer readability over cleverness
* Follow SOLID principles
* Keep functions small and focused

---

## 5. Development Rules ⚠️

* Prefer minimal diffs
* Do NOT rewrite entire files unless asked
* Reuse existing code
* Do NOT duplicate logic
* Avoid hardcoded magic numbers and configuration values
* Store configurable values in a dedicated config module and read runtime values from environment variables

---

## 6. Testing Rule (MANDATORY)

* ALWAYS write tests for new features
* A feature is NOT complete unless tests pass

---

## 7. Git Rules

* Use feature branches
* Use Pull Requests
* Keep history clean (rebase preferred)

---

## 8. Safety Rules

* Do NOT implement game automation (botting, macro)
* Only informational features allowed

---

## 9. Goal

Build a clean, maintainable, and scalable system.

## 10. Security Rules

- Do NOT hardcode secrets (tokens, API keys)
- Always use environment variables
- Do NOT print or log sensitive values
- Assume secrets are stored in .env
