# Development Guide

## 1. Git Branch Strategy

### Branch Types

* main: production-ready
* develop: integration branch
* feature/*: new features
* fix/*: bug fixes
* refactor/*: refactoring
* test/*: testing work

---

## 2. Workflow

1. Create branch from develop
2. Implement feature
3. Write tests
4. Build the Docker image
5. Run tests in Docker
6. Open Pull Request
7. Merge after review

### Docker Development Workflow

Use Docker for local development so the project works even when Python is not installed on the host machine.

Build the development image:

```powershell
docker compose build app
```

Run the default test command:

```powershell
docker compose run --rm app
```

Run a specific command inside the container:

```powershell
docker compose run --rm app uv run pytest
```

Run the Discord bot after setting `.env`:

```powershell
docker compose run --rm app uv run python -m app.main
```

For local slash command testing, set `DISCORD_GUILD_ID` in `.env` so commands sync to one test server immediately.

After changing dependencies in `pyproject.toml`, rebuild the image:

```powershell
docker compose build --no-cache app
```

---

## 3. Merge Strategy

* feature → develop: Rebase and merge
* develop → main: Merge commit

Alternative (simple mode):

* feature → main: Squash merge

---

## 4. Commit Convention

* feat: new feature
* fix: bug fix
* refactor: code improvement
* test: test code
* docs: documentation
* chore: build, tooling, or maintenance work

Example:

```text
feat: add notice crawler
fix: prevent duplicate notifications
```

## 4.1 Commit Workflow

After developing or modifying a feature, run the required Docker test command before committing:

```powershell
docker compose run --rm app
```

If the tests pass, create a commit for that small feature or fix.

Rules:

* Keep commits scoped to one small feature, bug fix, or maintenance change
* Do NOT mix unrelated changes in the same commit
* Do NOT commit changes before the required tests pass
* Use the commit convention above for every commit
* Leave unrelated working tree changes unstaged
* Mention important verification results when summarizing the commit

---

## 5. Code Style

* Follow PEP8
* Use type hints
* Avoid abbreviations
* Write self-explanatory code

---

## 6. Naming Convention

Good examples:

```python
get_latest_notices()
save_notice_to_db()
send_discord_notification()
```

Bad examples:

```python
fn1()
dataProc()
tmp()
```

---

## 7. SOLID Principles

* Single Responsibility
* Open/Closed
* Liskov Substitution
* Interface Segregation
* Dependency Inversion

---

## 8. Development Philosophy

* Small changes over big rewrites
* Stability over speed
* Code is maintained longer than written
