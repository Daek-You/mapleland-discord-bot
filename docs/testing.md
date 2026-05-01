# Testing Guide

## 1. Core Principle

* Tests are mandatory
* No feature is complete without passing tests

---

## 2. Testing Tool

* pytest
* Run pytest inside Docker with `docker compose run --rm app`

---

## 3. Test Scope

* Unit tests for services
* Mock external dependencies

  * API
  * crawler
  * database

---

## 4. Development Cycle

```text
Design → Test → Implement → Verify → Refactor → Test Again
```

---

## 5. Rules

* Write tests before or alongside code
* Do NOT skip tests
* Do NOT delete failing tests
* Fix code, not tests
* After feature development or bug fixes, run the full Docker test command

### Required Verification Command

```powershell
docker compose run --rm app
```

This command runs `uv run pytest -p no:cacheprovider` in the container, using the same Python and dependencies as the Docker development environment.

This verifies automated tests only. For Discord commands such as `/ping`, also run the bot with a real local `.env` token and confirm the command in a Discord test server.

```powershell
docker compose run --rm app uv run python -m app.main
```

### Reporting Test Results

When reporting test results, include enough detail for reviewers to see which tests passed.

Use verbose pytest output when a change adds or modifies tests:

```powershell
docker compose run --rm app uv run pytest -v
```

The report should include:

* The command that was run
* The total pass/fail result
* The relevant test file or test names that passed
* Any warnings that remain

---

## 6. Example Test Structure

```python
def test_fetch_notices():
    notices = fetch_notices()
    assert len(notices) > 0
```

---

## 7. Refactoring Rule

* Always run all tests after refactoring
* If any test fails → rollback and fix

---

## Commit After Verification

* Commit only after the required Docker test command passes
* Keep each commit focused on a small feature or fix

---

## 8. Goal

Ensure reliability and prevent regressions.
