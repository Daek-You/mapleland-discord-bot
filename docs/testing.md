# Testing Guide

## 1. Core Principle

* Tests are mandatory
* No feature is complete without passing tests

---

## 2. Testing Tool

* pytest
* Run pytest locally with uv for the normal development loop
* Use Docker separately when deployment compatibility must be verified

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
* After feature development or bug fixes, run the full local test command

### Required Verification Command

```powershell
uv run --locked pytest -p no:cacheprovider -v
```

The project `.python-version` selects Python 3.11, and `uv.lock` provides the same
resolved dependency versions on local machines and in Docker. The `--locked` option
fails instead of silently changing the lockfile.

This verifies automated tests only. For Discord commands such as `/ping`, also run the bot with a real local `.env` token and confirm the command in a Discord test server.

```powershell
uv run --locked python -m app.main
```

When deployment files or dependencies change, also verify the Docker image:

```powershell
docker compose build app
docker compose run --rm app uv run pytest -p no:cacheprovider -v
```

### Reporting Test Results

When reporting test results, include enough detail for reviewers to see which tests passed.

Use verbose pytest output when a change adds or modifies tests:

```powershell
uv run --locked pytest -p no:cacheprovider -v
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

* Commit only after the required local test command passes
* Keep each commit focused on a small feature or fix

---

## 8. Goal

Ensure reliability and prevent regressions.
