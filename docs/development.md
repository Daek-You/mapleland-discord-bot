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

### Pull Request Guide

Write Pull Request titles and descriptions in Korean.

Include these items in the Pull Request description:

* Summary of changes
* Verification commands and results
* Manual verification results, if the feature needs real service integration
* Notes about secrets or environment variables, without exposing real values

---

## 4. Commit Convention

Use the existing commit type prefixes, but write the commit summary in Korean.

* feat: new feature
* fix: bug fix
* refactor: code improvement
* test: test code
* docs: documentation
* chore: build, tooling, or maintenance work

Example:

```text
feat: 공지 크롤러 추가
fix: 중복 알림 방지
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
* Save all text files as UTF-8
* Use UTF-8 explicitly when reading or writing files in scripts or terminal commands

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

---

## 9. Configuration Rules

* Do NOT hardcode Discord slash command names or descriptions inside command handlers
* Define slash command metadata in a dedicated bot configuration module
* Do NOT hardcode magic numbers or runtime configuration values in feature code
* Define configurable defaults and environment variable names in a dedicated config module
* Command handlers should read metadata from configuration and keep only Discord input/output logic
* Use service-layer formatter functions for Discord message templates
* Prefer simple Discord Markdown templates for text responses
* Use `[title](url)` links instead of exposing long raw URLs when listing resources
* Consider Discord embeds only when a message needs richer structure than Markdown can provide

---

## 10. Error Handling Rules

External services can fail even after the command response has already been sent. Handle those failures close to the code that calls the external API.

Rules:

* Catch specific exceptions instead of broad `Exception` when the expected failure mode is known
* Convert crawler/network failures into project-level crawler errors before returning to services
* Log unexpected service failures with context, but do not log secrets or raw tokens
* For Discord UI callbacks and timeout callbacks, guard delayed message edits with `discord.NotFound` and `discord.HTTPException`
* Background tasks, scheduled jobs, and UI timeout callbacks must not leave unhandled task exceptions in logs
* Clear in-memory session data in `finally` when cleanup must happen even if Discord API calls fail
* Add tests for failure paths whenever adding new external calls, delayed callbacks, or cleanup logic

### Discord UI Timeout Note

`discord.ui.View.on_timeout()` can run minutes after the original command response. By then, the message may have been deleted or Discord may return `404 Unknown Message`.

When editing an expired UI message:

* Disable interactive controls first so local view state is consistent
* Catch `discord.NotFound` and treat it as an already-gone message
* Catch `discord.HTTPException` and log a warning instead of letting the timeout task crash
* Always clear per-session memory state in `finally`
* Prefer a visible disabled component for expired-state messaging when the notice should appear near the controls
